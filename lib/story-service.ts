import { env } from 'cloudflare:workers';
import { getChatGPTUser, type ChatGPTUser } from '../app/chatgpt-auth';
import { StorySchema, type Story, type StoryRecord } from './story-model';
import { SCENES } from './scene-catalog';
import { z } from 'zod';

type StoryRow = { id: string; owner_id: string; data: string; revision: number; created_at: number; updated_at: number; token?: string | null; published_at?: number | null };
type PublicationRow = { token: string; story_id: string; data: string; source_revision: number; published_at: number; active: number };
type AssetRow = { id: string; story_id: string; object_key: string; name: string; type: string; size: number; ready: number; created_at: number };
export type StoryAsset = { id: string; name: string; type: string; size: number; url: string };

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const TOKEN = /^[a-f0-9]{32}$/;
const JSON_LIMIT = 160 * 1024;
const MAX_UPLOAD = 12 * 1024 * 1024;
const STORY_SELECT = `SELECT s.*, p.token, p.published_at FROM stories s LEFT JOIN publications p ON p.story_id=s.id AND p.active=1`;
const revisionSchema = z.number().int().min(1).max(2147483647);
const eventSchema = z.object({ event: z.enum(['start', 'chapter', 'complete']), sessionId: z.string().regex(UUID), chapterId: z.string().min(1).max(80).optional(), publishedAt: z.number().int().positive().optional() }).strict();
const feedbackSchema = z.object({ sessionId: z.string().regex(UUID), choice: z.enum(['moved', 'clear', 'confused']), note: z.string().max(500).default(''), publishedAt: z.number().int().positive().optional() }).strict();

export function json(data: unknown, status = 200): Response {
  return Response.json(data, { status, headers: { 'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff' } });
}
export async function api(action: () => Promise<Response>): Promise<Response> {
  try { return await action(); }
  catch (error) {
    if (error instanceof ApiError) return json({ error: error.code, message: error.message }, error.status);
    if (error instanceof z.ZodError) return json({ error: 'invalid_input', message: '内容格式不正确，请检查章节、镜头、文字和时长。' }, 400);
    console.error('Story API request failed', error instanceof Error ? error.message : 'unknown error');
    return json({ error: 'server_error', message: '暂时无法完成操作，请稍后重试。' }, 500);
  }
}
export function sameOrigin(request: Request): void {
  const origin = request.headers.get('origin');
  if (!origin || origin !== new URL(request.url).origin || request.headers.get('sec-fetch-site') === 'cross-site') {
    throw new ApiError(403, 'origin_rejected', '请在本站页面完成此操作。');
  }
}
export async function user(): Promise<ChatGPTUser> {
  const value = await getChatGPTUser();
  if (!value) throw new ApiError(401, 'sign_in_required', '请先使用 ChatGPT 登录，再保存自己的作品。');
  return value;
}
function database(): D1Database {
  if (!env.DB) throw new ApiError(503, 'storage_unavailable', '作品存储暂时不可用，请稍后重试。');
  return env.DB;
}
function bucket(): R2Bucket {
  if (!env.BUCKET) throw new ApiError(503, 'storage_unavailable', '文件存储暂时不可用，请稍后重试。');
  return env.BUCKET;
}
function validId(id: string): void { if (!UUID.test(id)) throw new ApiError(404, 'not_found', '找不到这篇作品或文件。'); }
function validToken(token: string): void { if (!TOKEN.test(token)) throw new ApiError(404, 'not_found', '这个观看链接不存在，或作者已经撤销。'); }
export async function limitedBody(request: Request, limit: number): Promise<Uint8Array> {
  const declared = Number(request.headers.get('content-length'));
  if (Number.isFinite(declared) && declared > limit) throw new ApiError(413, 'too_large', '上传内容超出大小限制。');
  if (!request.body) throw new ApiError(400, 'empty_body', '请提供要保存的内容。');
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let length = 0;
  for (;;) {
    const result = await reader.read();
    if (result.done) break;
    length += result.value.byteLength;
    if (length > limit) { await reader.cancel(); throw new ApiError(413, 'too_large', '上传内容超出大小限制。'); }
    chunks.push(result.value);
  }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return bytes;
}
export async function readJson(request: Request): Promise<unknown> {
  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) throw new ApiError(415, 'invalid_type', '请发送 JSON 内容。');
  try { return JSON.parse(new TextDecoder().decode(await limitedBody(request, JSON_LIMIT))); }
  catch (error) { if (error instanceof ApiError) throw error; throw new ApiError(400, 'invalid_json', '提交内容无法读取，请重试。'); }
}
export function validateStory(input: unknown): Story {
  const data = StorySchema.parse(input);
  const ids = new Set<string>();
  for (const chapter of data.chapters) {
    if (ids.has(chapter.id)) throw new ApiError(400, 'duplicate_chapter', '章节编号不能重复。');
    ids.add(chapter.id);
    const allowed = SCENES.find(scene => scene.id === chapter.scene)!.shots.map(shot => shot.id as string);
    const beats = new Set<string>();
    for (const beat of chapter.beats) {
      if (beats.has(beat.id)) throw new ApiError(400, 'duplicate_beat', '同一章节的台词编号不能重复。');
      beats.add(beat.id);
      if (!allowed.includes(beat.shot)) throw new ApiError(400, 'invalid_shot', '所选机位不属于这个场景。');
    }
    if (chapter.sound === 'upload' && !chapter.audioAssetId) throw new ApiError(400, 'audio_required', '请先上传配乐，或选择场景环境声。');
  }
  return data;
}
export function referencedAssetIds(data: Story): Set<string> {
  return new Set(data.chapters.flatMap(chapter => [chapter.photoAssetId, chapter.audioAssetId]).filter((id): id is string => !!id));
}
function record(row: StoryRow): StoryRecord {
  return { id: row.id, data: JSON.parse(row.data), revision: row.revision, createdAt: row.created_at, updatedAt: row.updated_at,
    publication: row.token && row.published_at ? { token: row.token, publishedAt: row.published_at } : null };
}
async function owned(id: string, ownerId: string): Promise<StoryRow> {
  validId(id);
  const row = await database().prepare(`${STORY_SELECT} WHERE s.id=? AND s.owner_id=?`).bind(id, ownerId).first<StoryRow>();
  if (!row) throw new ApiError(404, 'not_found', '找不到这篇作品。');
  return row;
}
async function activePublication(token: string): Promise<PublicationRow> {
  validToken(token);
  const row = await database().prepare('SELECT * FROM publications WHERE token=? AND active=1').bind(token).first<PublicationRow>();
  if (!row) throw new ApiError(404, 'not_found', '这个观看链接不存在，或作者已经撤销。');
  return row;
}
async function verifyAssets(id: string, data: Story): Promise<void> {
  const references = referencedAssetIds(data);
  if (!references.size) return;
  const rows = (await database().prepare('SELECT * FROM story_assets WHERE story_id=? AND ready=1').bind(id).all<AssetRow>()).results;
  for (const chapter of data.chapters) {
    for (const [assetId, kind] of [[chapter.photoAssetId, 'image/'], [chapter.audioAssetId, 'audio/']] as const) {
      if (assetId && !rows.some(asset => asset.id === assetId && asset.type.startsWith(kind))) {
        throw new ApiError(400, 'invalid_asset', '素材不存在、未上传完成，或不属于这篇作品。');
      }
    }
  }
}
function conflict(): never { throw new ApiError(409, 'revision_conflict', '另一处已经更新这篇作品。请重新载入后再修改；你当前的内容仍保留在编辑器中。'); }
function assetRecord(row: AssetRow): StoryAsset { return { id: row.id, name: row.name, type: row.type, size: row.size, url: `/api/assets/${row.id}` }; }

export async function session(): Promise<Response> {
  const value = await getChatGPTUser();
  return json({ user: value ? { id: value.userId, name: value.displayName, email: value.email } : null });
}
export async function listStories(): Promise<Response> {
  const owner = await user();
  const result = await database().prepare(`${STORY_SELECT} WHERE s.owner_id=? ORDER BY s.updated_at DESC LIMIT 100`).bind(owner.userId).all<StoryRow>();
  return json({ stories: result.results.map(record) });
}
export async function createStory(request: Request): Promise<Response> {
  sameOrigin(request);
  const owner = await user();
  const body = z.object({ data: z.unknown() }).strict().parse(await readJson(request));
  const data = validateStory(body.data);
  if (referencedAssetIds(data).size) throw new ApiError(400, 'invalid_asset', '先建立作品，再上传这篇作品的素材。');
  const id = crypto.randomUUID();
  const now = Date.now();
  const result = await database().prepare('INSERT INTO stories(id,owner_id,data,revision,created_at,updated_at) SELECT ?,?,?,1,?,? WHERE (SELECT COUNT(*) FROM stories WHERE owner_id=?) < 100')
    .bind(id, owner.userId, JSON.stringify(data), now, now, owner.userId).run();
  if (!result.meta.changes) throw new ApiError(429, 'story_limit', '每个账户最多保存 100 篇作品，请整理旧作品后再创建。');
  return json({ story: record({ id, owner_id: owner.userId, data: JSON.stringify(data), revision: 1, created_at: now, updated_at: now }) }, 201);
}
export async function getStory(id: string): Promise<Response> {
  const owner = await user();
  return json({ story: record(await owned(id, owner.userId)) });
}
export async function updateStory(request: Request, id: string): Promise<Response> {
  sameOrigin(request);
  const owner = await user();
  const existing = await owned(id, owner.userId);
  const body = z.object({ data: z.unknown(), revision: revisionSchema }).strict().parse(await readJson(request));
  if (existing.revision !== body.revision) conflict();
  const data = validateStory(body.data);
  await verifyAssets(id, data);
  const result = await database().prepare('UPDATE stories SET data=?,revision=revision+1,updated_at=? WHERE id=? AND owner_id=? AND revision=?')
    .bind(JSON.stringify(data), Date.now(), id, owner.userId, body.revision).run();
  if (!result.meta.changes) conflict();
  return json({ story: record(await owned(id, owner.userId)) });
}
export async function deleteStory(request: Request, id: string): Promise<Response> {
  sameOrigin(request);
  const owner = await user();
  await owned(id, owner.userId);
  const keys = (await database().prepare('SELECT object_key FROM story_assets WHERE story_id=?').bind(id).all<{object_key: string}>()).results.map(value => value.object_key);
  await database().batch([
    database().prepare('DELETE FROM story_events WHERE story_id=?').bind(id),
    database().prepare('DELETE FROM story_feedback WHERE story_id=?').bind(id),
    database().prepare('DELETE FROM publications WHERE story_id=?').bind(id),
    database().prepare('DELETE FROM story_assets WHERE story_id=?').bind(id),
    database().prepare('DELETE FROM stories WHERE id=? AND owner_id=?').bind(id, owner.userId),
  ]);
  if (keys.length) await bucket().delete(keys);
  return json({ ok: true });
}
export async function publishStory(request: Request, id: string): Promise<Response> {
  sameOrigin(request);
  const owner = await user();
  const existing = await owned(id, owner.userId);
  const body = z.object({ revision: revisionSchema }).strict().parse(await readJson(request));
  if (existing.revision !== body.revision) conflict();
  const data: Story = JSON.parse(existing.data);
  await verifyAssets(id, data);
  const snapshot = JSON.stringify({...data, chapters:data.chapters.map(chapter=>({...chapter,note:''}))});
  // A revoked link is never reactivated. Active links keep their URL on an explicit republish.
  const token = existing.token ?? Array.from(crypto.getRandomValues(new Uint8Array(16)), value => value.toString(16).padStart(2, '0')).join('');
  const publishedAt = Math.max(Date.now(), (existing.published_at ?? 0) + 1);
  const result = await database().prepare(`INSERT INTO publications(token,story_id,data,source_revision,published_at,active)
    SELECT ?,id,?,revision,?,1 FROM stories WHERE id=? AND owner_id=? AND revision=?
    ON CONFLICT(story_id) DO UPDATE SET token=CASE WHEN publications.active=1 THEN publications.token ELSE excluded.token END,data=excluded.data,source_revision=excluded.source_revision,published_at=MAX(publications.published_at+1,excluded.published_at),active=1`)
    .bind(token, snapshot, publishedAt, id, owner.userId, body.revision).run();
  if (!result.meta.changes) conflict();
  const published = await database().prepare('SELECT token,published_at FROM publications WHERE story_id=? AND active=1').bind(id).first<{token:string;published_at:number}>();
  if (!published) throw new ApiError(409, 'publication_changed', '发布状态已经改变，请重新载入后确认。');
  return json({ token: published.token, url: `${new URL(request.url).origin}/watch/${published.token}`, publishedAt: published.published_at });
}
export async function revokePublication(request: Request, id: string): Promise<Response> {
  sameOrigin(request);
  const owner = await user();
  await owned(id, owner.userId);
  await database().prepare('UPDATE publications SET active=0 WHERE story_id=?').bind(id).run();
  return json({ ok: true });
}
export async function getPublicStory(token: string): Promise<Response> {
  const value = await activePublication(token);
  return json({ id: value.story_id, token: value.token, data: JSON.parse(value.data), publishedAt: value.published_at });
}
async function viewerIsAuthor(storyId: string): Promise<boolean> {
  const viewer = await getChatGPTUser();
  if (!viewer) return false;
  return !!(await database().prepare('SELECT 1 AS found FROM stories WHERE id=? AND owner_id=?').bind(storyId, viewer.userId).first());
}
export async function sessionHash(token: string, time: number, sessionId: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${token}:${time}:${sessionId}`));
  return Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, '0')).join('');
}
export async function addEvent(request: Request, token: string): Promise<Response> {
  sameOrigin(request);
  const publication = await activePublication(token);
  const body = eventSchema.parse(await readJson(request));
  if (body.publishedAt && body.publishedAt !== publication.published_at) throw new ApiError(409, 'snapshot_changed', '作者更新了这篇作品，请刷新后继续观看。');
  const data: Story = JSON.parse(publication.data);
  if (body.event === 'chapter' && (!body.chapterId || !data.chapters.some(chapter => chapter.id === body.chapterId))) throw new ApiError(400, 'invalid_chapter', '这个章节不在已发布作品中。');
  if (body.event !== 'chapter' && body.chapterId) throw new ApiError(400, 'invalid_event', '该事件不需要章节编号。');
  if (await viewerIsAuthor(publication.story_id)) return json({ ok: true, excluded: true });
  const hash = await sessionHash(token, publication.published_at, body.sessionId);
  const now = Date.now();
  // A complete event also records start; completion rate therefore never exceeds 100%.
  const rows = body.event === 'start' ? ['start'] : ['start', body.event];
  const result = await database().batch(rows.map(event => database().prepare(`INSERT OR IGNORE INTO story_events(id,story_id,publication_time,session_hash,event,chapter_id,created_at)
    SELECT ?,?,?,?,?,?,? WHERE EXISTS (SELECT 1 FROM publications WHERE token=? AND active=1 AND published_at=?) AND (SELECT COUNT(*) FROM story_events WHERE story_id=? AND publication_time=?) < 50000`)
    .bind(crypto.randomUUID(), publication.story_id, publication.published_at, hash, event, event === 'chapter' ? body.chapterId : '', now, token, publication.published_at, publication.story_id, publication.published_at)));
  if (!result[result.length - 1].meta.changes) {
    const recorded = await database().prepare('SELECT 1 AS found FROM story_events WHERE story_id=? AND publication_time=? AND session_hash=? AND event=? AND chapter_id=?').bind(publication.story_id, publication.published_at, hash, body.event, body.event === 'chapter' ? body.chapterId : '').first();
    if (!recorded) {
      const current = await activePublication(token);
      if (current.published_at !== publication.published_at) throw new ApiError(409, 'snapshot_changed', '作者更新了这篇作品，请刷新后继续观看。');
      throw new ApiError(429, 'analytics_limit', '这个发布版本的播放记录已达上限，观看不受影响。');
    }
  }
  return json({ ok: true });
}
export async function addFeedback(request: Request, token: string): Promise<Response> {
  sameOrigin(request);
  const publication = await activePublication(token);
  if (!(JSON.parse(publication.data) as Story).feedback) throw new ApiError(403, 'feedback_disabled', '作者未开启观众反馈。');
  const body = feedbackSchema.parse(await readJson(request));
  if (body.publishedAt && body.publishedAt !== publication.published_at) throw new ApiError(409, 'snapshot_changed', '作者更新了这篇作品，请刷新后再发送反馈。');
  if (await viewerIsAuthor(publication.story_id)) throw new ApiError(403, 'author_feedback_excluded', '作者自己的观看与反馈不计入观众数据，请将链接分享给观众后收集回应。');
  const hash = await sessionHash(token, publication.published_at, body.sessionId);
  const result = await database().prepare(`INSERT OR IGNORE INTO story_feedback(id,story_id,publication_time,session_hash,choice,note,created_at)
    SELECT ?,?,?,?,?,?,? WHERE EXISTS (SELECT 1 FROM publications WHERE token=? AND active=1 AND published_at=?) AND (SELECT COUNT(*) FROM story_feedback WHERE story_id=? AND publication_time=?) < 5000`)
    .bind(crypto.randomUUID(), publication.story_id, publication.published_at, hash, body.choice, body.note.trim(), Date.now(), token, publication.published_at, publication.story_id, publication.published_at).run();
  if (!result.meta.changes) {
    const recorded = await database().prepare('SELECT 1 AS found FROM story_feedback WHERE story_id=? AND publication_time=? AND session_hash=?').bind(publication.story_id, publication.published_at, hash).first();
    if (!recorded) {
      const current = await activePublication(token);
      if (current.published_at !== publication.published_at) throw new ApiError(409, 'snapshot_changed', '作者更新了这篇作品，请刷新后再发送反馈。');
      throw new ApiError(429, 'feedback_limit', '这个发布版本的反馈已达上限，暂时不能接收更多留言。');
    }
  }
  return json({ ok: true });
}
export async function insights(id: string): Promise<Response> {
  const owner = await user();
  const story = await owned(id, owner.userId);
  const publication = await database().prepare('SELECT * FROM publications WHERE story_id=? ORDER BY published_at DESC LIMIT 1').bind(id).first<PublicationRow>();
  const data: Story = publication ? JSON.parse(publication.data) : JSON.parse(story.data);
  if (!publication) return json({ starts: 0, completions: 0, completionRate: null, chapters: data.chapters.map(chapter => ({ id: chapter.id, title: chapter.title, views: 0 })), feedback: [], feedbackCount: 0 });
  const db = database();
  const [eventRows, feedbackRows, totalRows] = await db.batch([
    db.prepare('SELECT event,chapter_id,COUNT(*) AS count FROM story_events WHERE story_id=? AND publication_time=? GROUP BY event,chapter_id').bind(id, publication.published_at),
    db.prepare('SELECT choice,note,created_at FROM story_feedback WHERE story_id=? AND publication_time=? ORDER BY created_at DESC LIMIT 100').bind(id, publication.published_at),
    db.prepare('SELECT COUNT(*) AS count FROM story_feedback WHERE story_id=? AND publication_time=?').bind(id, publication.published_at),
  ]);
  const counts = eventRows.results as {event:string; chapter_id:string; count:number}[];
  const starts = counts.find(value => value.event === 'start')?.count ?? 0;
  const completions = counts.find(value => value.event === 'complete')?.count ?? 0;
  return json({ starts, completions, completionRate: starts ? completions / starts : null,
    chapters: data.chapters.map(chapter => ({ id: chapter.id, title: chapter.title, views: counts.find(value => value.event === 'chapter' && value.chapter_id === chapter.id)?.count ?? 0 })),
    feedback: (feedbackRows.results as {choice:string;note:string;created_at:number}[]).map(value => ({choice:value.choice,note:value.note,createdAt:value.created_at})),
    feedbackCount: (totalRows.results[0] as {count:number}).count });
}
export async function listAssets(id: string): Promise<Response> {
  const owner = await user();
  await owned(id, owner.userId);
  const result = await database().prepare('SELECT * FROM story_assets WHERE story_id=? AND ready=1 ORDER BY created_at DESC').bind(id).all<AssetRow>();
  return json({ assets: result.results.map(assetRecord) });
}
export function sniffAsset(bytes: Uint8Array): {type: string; maxSize: number} | null {
  const ascii = (start: number, end: number) => String.fromCharCode(...bytes.slice(start,end));
  if (bytes.length >= 8 && bytes[0] === 137 && ascii(1,4) === 'PNG' && bytes[4] === 13 && bytes[5] === 10 && bytes[6] === 26 && bytes[7] === 10) return {type:'image/png', maxSize:5*1024*1024};
  if (bytes.length >= 4 && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return {type:'image/jpeg', maxSize:5*1024*1024};
  if (bytes.length >= 12 && ascii(0,4) === 'RIFF' && ascii(8,12) === 'WEBP') return {type:'image/webp', maxSize:5*1024*1024};
  if (bytes.length >= 12 && ascii(0,4) === 'RIFF' && ascii(8,12) === 'WAVE') return {type:'audio/wav', maxSize:MAX_UPLOAD};
  if (bytes.length >= 27 && ascii(0,4) === 'OggS') return {type:'audio/ogg', maxSize:MAX_UPLOAD};
  if (bytes.length >= 12 && ascii(4,8) === 'ftyp' && ['M4A ', 'M4B ', 'isom', 'mp42'].includes(ascii(8,12))) return {type:'audio/mp4', maxSize:MAX_UPLOAD};
  if (bytes.length >= 4 && (ascii(0,3) === 'ID3' || (bytes[0] === 255 && (bytes[1] & 0xe0) === 0xe0 && (bytes[1] & 6) !== 0 && (bytes[2] & 0xf0) !== 0xf0))) return {type:'audio/mpeg', maxSize:MAX_UPLOAD};
  return null;
}
export async function uploadAsset(request: Request, id: string): Promise<Response> {
  sameOrigin(request);
  const owner = await user();
  await owned(id, owner.userId);
  const contentType = request.headers.get('content-type');
  if (!contentType?.startsWith('multipart/form-data;')) throw new ApiError(415, 'invalid_type', '请上传 JPG、PNG、WebP 或 MP3、M4A、OGG、WAV 文件。');
  const bytes = await limitedBody(request, MAX_UPLOAD + 16384);
  let form: FormData;
  try { form = await new Response(bytes.buffer as ArrayBuffer, {headers:{'content-type':contentType}}).formData(); }
  catch { throw new ApiError(400, 'invalid_upload', '文件提交不完整，请重新上传。'); }
  const file = form.get('file');
  if (!(file instanceof File) || form.getAll('file').length !== 1) throw new ApiError(400, 'invalid_upload', '每次请选择一个文件。');
  if (!file.size) throw new ApiError(400, 'empty_file', '不能上传空文件。');
  const fileBytes = new Uint8Array(await file.arrayBuffer());
  const detected = sniffAsset(fileBytes);
  if (!detected) throw new ApiError(415, 'unsupported_file', '文件内容不是支持的图片或音频格式。');
  if (file.size > detected.maxSize) throw new ApiError(413, 'too_large', detected.type.startsWith('image/') ? '图片最多 5 MiB。' : '音频最多 12 MiB。');
  const assetId = crypto.randomUUID();
  const key = `stories/${id}/${assetId}`;
  const name = file.name.replace(/[\x00-\x1f\x7f/\\]/g, '_').slice(0,160) || '素材';
  const now = Date.now();
  const db = database();
  const reserved = await db.prepare(`INSERT INTO story_assets(id,story_id,object_key,name,type,size,ready,created_at)
    SELECT ?,?,?,?,?,?,0,? WHERE EXISTS(SELECT 1 FROM stories WHERE id=? AND owner_id=?) AND (SELECT COUNT(*) FROM story_assets WHERE story_id=?) < 20`)
    .bind(assetId, id, key, name, detected.type, file.size, now, id, owner.userId, id).run();
  if (!reserved.meta.changes) throw new ApiError(409, 'asset_limit', '每篇作品最多上传 20 个文件。请重新载入确认作品仍然存在。');
  try {
    await bucket().put(key, fileBytes, { httpMetadata: { contentType: detected.type }, customMetadata: {storyId: id} });
    const ready = await db.prepare('UPDATE story_assets SET ready=1 WHERE id=? AND EXISTS(SELECT 1 FROM stories WHERE id=? AND owner_id=?)').bind(assetId,id,owner.userId).run();
    if (!ready.meta.changes) { await bucket().delete(key); throw new ApiError(404,'not_found','作品已经删除，文件未保存。'); }
  } catch (error) { await db.prepare('DELETE FROM story_assets WHERE id=?').bind(assetId).run(); throw error; }
  return json({ asset: assetRecord({id:assetId,story_id:id,object_key:key,name,type:detected.type,size:file.size,ready:1,created_at:now}) }, 201);
}
export async function getAsset(request: Request, assetId: string): Promise<Response> {
  validId(assetId);
  const db = database();
  const value = await db.prepare('SELECT a.*, s.owner_id FROM story_assets a JOIN stories s ON s.id=a.story_id WHERE a.id=? AND a.ready=1').bind(assetId).first<AssetRow & {owner_id:string}>();
  if (!value) throw new ApiError(404,'not_found','素材不存在或已删除。');
  const viewer = await getChatGPTUser();
  if (viewer?.userId !== value.owner_id) {
    const token = new URL(request.url).searchParams.get('publication');
    if (!token || !TOKEN.test(token)) throw new ApiError(404,'not_found','素材不存在或尚未公开。');
    const publication = await activePublication(token);
    if (publication.story_id !== value.story_id || !referencedAssetIds(JSON.parse(publication.data)).has(assetId)) throw new ApiError(404,'not_found','素材不存在或尚未公开。');
  }
  let range: {offset:number;length:number} | undefined;
  const requested = request.headers.get('range');
  if (requested) {
    const match = /^bytes=(\d*)-(\d*)$/.exec(requested);
    if (!match || (!match[1] && !match[2])) return new Response(null,{status:416,headers:{'Content-Range':`bytes */${value.size}`}});
    const start = match[1] ? Number(match[1]) : Math.max(0, value.size-Number(match[2]));
    const end = match[1] ? (match[2] ? Math.min(Number(match[2]),value.size-1) : value.size-1) : value.size-1;
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start > end || start >= value.size || start < 0) return new Response(null,{status:416,headers:{'Content-Range':`bytes */${value.size}`}});
    range = {offset:start,length:end-start+1};
  }
  const object = await bucket().get(value.object_key, range ? {range} : undefined);
  if (!object) throw new ApiError(404,'not_found','素材文件暂时无法读取。');
  const headers = new Headers({ 'Content-Type':value.type, 'Content-Length':String(range?.length ?? value.size), 'Cache-Control':'private, no-store', 'Accept-Ranges':'bytes', 'X-Content-Type-Options':'nosniff', 'Content-Disposition':`inline; filename*=UTF-8''${encodeURIComponent(value.name)}` });
  if (range) headers.set('Content-Range',`bytes ${range.offset}-${range.offset+range.length-1}/${value.size}`);
  return new Response(object.body,{status:range?206:200,headers});
}
