import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { EnvHttpProxyAgent, fetch } from 'undici';

const root = path.dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(await fsp.readFile(path.join(root, 'files.json'), 'utf8'));
const expectedOrigin = 'https://casa-bellas-action.tb8zssvcd2.chatgpt.site';
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const matches = (bytes, item) => bytes.length === item.bytes && digest(bytes) === item.sha256;

function destination(relative) {
  if (typeof relative !== 'string' || relative.includes('\\') || path.isAbsolute(relative)
      || relative.split('/').some(part => part === '..' || part === '' || part === '.')) {
    throw new Error('Invalid project path');
  }
  const result = path.resolve(root, relative);
  if (!result.startsWith(root + path.sep)) throw new Error('Path outside project');
  return result;
}

function sourceFile(name) {
  if (typeof name !== 'string' || path.basename(name) !== name) throw new Error('Invalid source filename');
  return path.join(root, name);
}

function proxyOptions() {
  if (process.platform !== 'darwin'
      || ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY'].some(key => process.env[key])) return {};
  // Honor the user's existing system proxy, without storing any machine-specific settings.
  try {
    const settings = execFileSync('/usr/sbin/scutil', ['--proxy'], { encoding: 'utf8', timeout: 3000 });
    const value = key => settings.match(new RegExp('^\\s*' + key + '\\s*:\\s*(.+)$', 'm'))?.[1]?.trim();
    const result = {};
    for (const [scheme, key] of [['HTTP', 'httpProxy'], ['HTTPS', 'httpsProxy']]) {
      const host = value(scheme + 'Proxy');
      const port = value(scheme + 'Port');
      if (value(scheme + 'Enable') === '1' && host && /^\d+$/.test(port || '')) {
        const address = new URL('http://localhost');
        address.hostname = host;
        address.port = port;
        result[key] = address.href;
      }
    }
    return result;
  } catch { return {}; }
}

async function restoreCode() {
  const buffers = new Map();
  let restored = 0;
  for (const item of manifest.code) {
    const target = destination(item.path);
    // Preserve edits made in the destination platform after the initial import.
    if (fs.existsSync(target)) continue;
    if (!Number.isSafeInteger(item.offset) || !Number.isSafeInteger(item.bytes)
        || item.offset < 0 || item.bytes < 0) throw new Error('Invalid source byte range');
    if (!buffers.has(item.source)) buffers.set(item.source, await fsp.readFile(sourceFile(item.source)));
    const bytes = buffers.get(item.source).subarray(item.offset, item.offset + item.bytes);
    if (!matches(bytes, item)) throw new Error('Source incomplete or altered: ' + item.path);
    await fsp.mkdir(path.dirname(target), { recursive: true });
    await fsp.writeFile(target, bytes, { mode: item.path.endsWith('.sh') ? 0o755 : 0o644 });
    restored++;
  }
  return restored;
}

async function requestAsset(url, dispatcher) {
  const signal = AbortSignal.timeout(90000);
  let current = url;
  for (let redirects = 0; redirects <= 5; redirects++) {
    const response = await fetch(current, {
      dispatcher,
      redirect: 'manual',
      signal,
      headers: { Accept: '*/*', 'User-Agent': 'StoryTape-AssetRestore/1.0' },
    });
    if (![301, 302, 303, 307, 308].includes(response.status)) return response;
    const location = response.headers.get('location');
    await response.body?.cancel();
    if (!location) throw new Error('Asset redirect has no destination');
    const next = new URL(location, current);
    if (next.origin !== expectedOrigin || next.username || next.password) {
      throw new Error('Unexpected asset redirect origin');
    }
    current = next;
  }
  throw new Error('Too many asset redirects');
}

async function downloadAsset(item, dispatcher) {
  if (!item.path.startsWith('public/')) throw new Error('Invalid asset path');
  const target = destination(item.path);
  if (fs.existsSync(target) && matches(await fsp.readFile(target), item)) return false;
  const url = new URL(item.url);
  if (url.origin !== expectedOrigin || url.username || url.password) throw new Error('Unexpected asset origin');
  let lastError;
  for (let attempt = 1; attempt <= 3; attempt++) {
    const temporary = target + '.' + process.pid + '.part';
    try {
      const response = await requestAsset(url, dispatcher);
      if (!response.ok) {
        await response.body?.cancel();
        const error = new Error('HTTP ' + response.status + ' for ' + item.path);
        error.permanent = response.status >= 400 && response.status < 500 && response.status !== 429;
        throw error;
      }
      const declaredLength = response.headers.get('content-length');
      if (declaredLength && Number(declaredLength) > item.bytes) throw new Error('Unexpected asset size: ' + item.path);
      const parts = [];
      let size = 0;
      for await (const part of response.body) {
        size += part.length;
        if (size > item.bytes) throw new Error('Asset exceeded expected size: ' + item.path);
        parts.push(part);
      }
      const bytes = Buffer.concat(parts, size);
      if (!matches(bytes, item)) {
        const error = new Error('Asset version or checksum mismatch: ' + item.path);
        error.permanent = true;
        throw error;
      }
      await fsp.mkdir(path.dirname(target), { recursive: true });
      await fsp.writeFile(temporary, bytes);
      await fsp.rename(temporary, target);
      return true;
    } catch (error) {
      await fsp.rm(temporary, { force: true });
      lastError = error;
      if (error.permanent || attempt === 3) break;
      await new Promise(resolve => setTimeout(resolve, attempt * 1000));
    }
  }
  throw new Error('Could not restore ' + item.path + ': ' + lastError.message
    + '. Check access to the original public site and the platform HTTP(S)_PROXY settings; then rerun npm run restore.');
}

const dispatcher = new EnvHttpProxyAgent(proxyOptions());
let nextIndex = 0;
let checked = 0;
let downloaded = 0;
let sourceCount = 0;
let failed = false;
try {
  sourceCount = await restoreCode();
  const workers = Array.from({ length: 4 }, async () => {
    while (!failed) {
      const index = nextIndex++;
      if (index >= manifest.assets.length) break;
      try {
        if (await downloadAsset(manifest.assets[index], dispatcher)) downloaded++;
        checked++;
        if (checked % 20 === 0 || checked === manifest.assets.length) {
          console.log('Assets verified: ' + checked + '/' + manifest.assets.length);
        }
      } catch (error) { failed = true; throw error; }
    }
  });
  const results = await Promise.allSettled(workers);
  const failure = results.find(result => result.status === 'rejected');
  if (failure) throw failure.reason;
  console.log('Application ready: ' + sourceCount + ' source files restored, '
    + downloaded + ' assets downloaded, ' + checked + ' assets verified.');
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
} finally {
  await dispatcher.close();
}
