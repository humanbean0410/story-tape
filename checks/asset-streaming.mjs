import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash,webcrypto} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {fetchBytes,readPack} from '../dist/asset-transport.js';
globalThis.crypto??=webcrypto;
const root=new URL('../dist/',import.meta.url),manifest=JSON.parse(await readFile(new URL('assets/model-packs.json',root),'utf8'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
for(const [path,pack] of Object.entries(manifest)){
  const parts=await Promise.all(pack.chunks.map(async chunk=>{const bytes=await readFile(new URL(chunk.url,root));assert.ok(bytes.length<=1024*1024);assert.equal(bytes.length,chunk.bytes);assert.equal(hash(bytes),chunk.sha256);return bytes;}));
  const unpacked=gunzipSync(Buffer.concat(parts)),original=await readFile(new URL(path,root));assert.equal(unpacked.length,pack.bytes);assert.equal(hash(unpacked),pack.sha256);assert.deepEqual(unpacked,original);
}
// Reproduce the deployed cassette's stalled body; the deadline must settle
// even when an underlying stream never rejects on abort.
let calls=0;
globalThis.fetch=async()=>{calls++;return calls===1?{ok:true,headers:new Headers(),arrayBuffer:()=>new Promise(()=>{})}:new Response(new Uint8Array([1,2,3]));};
assert.deepEqual([...await fetchBytes('assets/stalled.bin',{timeout:25,attempts:2})],[1,2,3]);assert.equal(calls,2);
globalThis.fetch=async()=>({ok:true,headers:new Headers(),arrayBuffer:()=>new Promise(()=>{})});
await assert.rejects(fetchBytes('assets/stalled.bin',{timeout:25,attempts:2}),/超时/);
globalThis.fetch=async()=>new Response('<html>access page</html>',{headers:{'content-type':'text/html'}});
await assert.rejects(fetchBytes('assets/private.bin',{timeout:25,attempts:1}),/访问页面/);
globalThis.fetch=async url=>new Response(await readFile(new URL(new URL(url).pathname.split('/dist/')[1],root)));
const decoded=await readPack(manifest['assets/cassette-deck.glb']);assert.equal(hash(new Uint8Array(decoded)),manifest['assets/cassette-deck.glb'].sha256);
console.log(`All ${Object.keys(manifest).length} models restore byte-for-byte; 1 MiB request limit, stuck-body retry/deadline, access-page rejection, and cassette reassembly passed.`);
