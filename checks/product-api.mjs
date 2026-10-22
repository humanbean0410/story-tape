// SQLite-backed integration checks. Cloudflare bindings and platform identity are replaced
// with deterministic in-memory adapters; application service code and generated SQL are real.
// Run: node --experimental-vm-modules checks/product-api.mjs
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { webcrypto } from 'node:crypto';
import vm from 'node:vm';
import ts from 'typescript';
import * as zod from 'zod';

const root = resolve(import.meta.dirname, '..');
const sqlite = new DatabaseSync(':memory:');
sqlite.exec('PRAGMA foreign_keys = ON');
for (const migration of readdirSync(resolve(root, 'drizzle')).filter(path => path.endsWith('.sql')).sort()) sqlite.exec(readFileSync(resolve(root,'drizzle',migration),'utf8'));
class Statement {
  constructor(sql,values=[]) { this.sql=sql;this.values=values; }
  bind(...values) {return new Statement(this.sql,values);}
  async first() {return sqlite.prepare(this.sql).get(...this.values) ?? null;}
  async all() {return {results:sqlite.prepare(this.sql).all(...this.values),success:true,meta:{}};}
  async run() {const result=sqlite.prepare(this.sql).run(...this.values);return {results:[],success:true,meta:{changes:Number(result.changes),last_row_id:Number(result.lastInsertRowid)}};}
}
const objects=new Map();
const env={ DB:{prepare:sql=>new Statement(sql),batch:async statements=>{
  sqlite.exec('BEGIN');
  try {const result=[];for(const statement of statements)result.push(/^\s*SELECT/i.test(statement.sql)?await statement.all():await statement.run());sqlite.exec('COMMIT');return result;}
  catch(error){sqlite.exec('ROLLBACK');throw error;}
}}, BUCKET:{put:async(key,data)=>{objects.set(key,new Uint8Array(data));},delete:async keys=>{for(const key of Array.isArray(keys)?keys:[keys])objects.delete(key);},get:async(key,options)=>{
  const bytes=objects.get(key);if(!bytes)return null;
  const selected=options?.range?bytes.slice(options.range.offset,options.range.offset+options.range.length):bytes;
  return {body:new Response(selected).body};
}}};
let identity={userId:'owner-a',displayName:'Author A',email:'a@example.test',fullName:null};
const context=vm.createContext({console,TextEncoder,TextDecoder,Uint8Array,ArrayBuffer,Response,Request,Headers,File,FormData,crypto:webcrypto,Date,Set,Map,URL,Number,JSON});
const loaded=new Map();
const fake = (identifier,exports) => new vm.SyntheticModule(Object.keys(exports),function(){for(const [key,value] of Object.entries(exports))this.setExport(key,value);},{context,identifier});
const mocks=new Map([['cloudflare:workers',fake('cloudflare:workers',{env})],['zod',fake('zod',zod)],['auth',fake('auth',{getChatGPTUser:async()=>identity})]]);
async function moduleAt(path){
  if(loaded.has(path))return loaded.get(path);
  const source=ts.transpileModule(readFileSync(path,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  const module=new vm.SourceTextModule(source,{context,identifier:path});loaded.set(path,module);
  await module.link(async(specifier,parent)=>{
    if(mocks.has(specifier))return mocks.get(specifier);
    if(specifier.includes('chatgpt-auth'))return mocks.get('auth');
    let dependency=resolve(dirname(parent.identifier),specifier);if(!dependency.endsWith('.ts'))dependency+='.ts';return moduleAt(dependency);
  });return module;
}
const serviceModule=await moduleAt(resolve(root,'lib/story-service.ts'));await serviceModule.evaluate();const api=serviceModule.namespace;
const origin='https://test.chatgpt.site';
function request(path,body,method='POST',custom={}) {return new Request(origin+path,{method,headers:{origin,'content-type':'application/json',...custom},body:body===undefined?undefined:JSON.stringify(body)});}
async function invoke(fn,...args){const response=await api.api(()=>api[fn](...args));const body=response.headers.get('content-type')?.includes('json')?await response.json():null;return {response,body,status:response.status};}
const story={schemaVersion:1,title:'A little walk',subtitle:'',author:'A',dedication:'',template:'blank',opening:true,feedback:true,chapters:[{id:'one',scene:'casa',title:'An afternoon',note:'',sound:'ambience',audioAssetId:null,photoAssetId:null,beats:[{id:'first',speaker:'I',text:'We sat here.',shot:'master',seconds:7}]}]};

const modelModule=await moduleAt(resolve(root,'lib/story-model.ts'));await modelModule.evaluate();
const fingerprint=modelModule.namespace.storyFingerprint;
const canonical=modelModule.namespace.StorySchema.parse(story);
assert.equal(fingerprint(story),fingerprint(canonical),'saving schema-normalized field order must not schedule another save');
const changedFingerprint=structuredClone(story);changedFingerprint.chapters[0].beats[0].text='Actually edited.';
assert.notEqual(fingerprint(story),fingerprint(changedFingerprint),'real edits still trigger a save');
const invalidFingerprint=structuredClone(story);invalidFingerprint.title='';assert.doesNotThrow(()=>fingerprint(invalidFingerprint),'invalid in-progress drafts still recover locally');

identity=null;
assert.equal((await invoke('listStories')).status,401);
assert.deepEqual((await invoke('session')).body,{user:null});
identity={userId:'owner-a',displayName:'Author A',email:'a@example.test',fullName:null};
assert.equal((await invoke('createStory',request('/api/stories',{data:story},'POST',{origin:'https://evil.test'}))).status,403);
assert.equal((await invoke('createStory',request('/api/stories',{data:story},'POST',{'content-length':String(500000)}))).status,413);
const invalid=structuredClone(story);invalid.chapters[0].beats[0].shot='not-a-shot';
assert.equal((await invoke('createStory',request('/api/stories',{data:invalid}))).status,400);
const created=await invoke('createStory',request('/api/stories',{data:story}));assert.equal(created.status,201);
const id=created.body.story.id;assert.equal(created.body.story.revision,1);
assert.equal((await invoke('listStories')).body.stories.length,1);
identity={userId:'owner-b',displayName:'Author B',email:'b@example.test',fullName:null};
assert.equal((await invoke('getStory',id)).status,404);
assert.equal((await invoke('updateStory',request(`/api/stories/${id}`,{data:story,revision:1},'PUT'),id)).status,404);
assert.equal((await invoke('deleteStory',request(`/api/stories/${id}`,undefined,'DELETE'),id)).status,404);
assert.equal((await invoke('listStories')).body.stories.length,0);
identity={userId:'owner-a',displayName:'Author A',email:'a@example.test',fullName:null};

function multipart(filename,bytes,type){const form=new FormData();form.append('file',new File([bytes],filename,{type}));return new Request(origin+`/api/stories/${id}/assets`,{method:'POST',headers:{origin},body:form});}
assert.equal((await invoke('uploadAsset',multipart('bad.png',new TextEncoder().encode('<svg>bad</svg>'),'image/png'),id)).status,415);
const png=new Uint8Array(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jHo0AAAAASUVORK5CYII=','base64'));
const photo=await invoke('uploadAsset',multipart('photo.png',png,'image/png'),id);assert.equal(photo.status,201);
const photoId=photo.body.asset.id;
assert.equal((await invoke('listAssets',id)).body.assets.length,1);
assert.equal(objects.size,1);
const changed=structuredClone(story);changed.chapters[0].photoAssetId=photoId;
assert.equal((await invoke('updateStory',request(`/api/stories/${id}`,{data:changed,revision:1},'PUT'),id)).body.story.revision,2);
assert.equal((await invoke('updateStory',request(`/api/stories/${id}`,{data:story,revision:1},'PUT'),id)).status,409);
assert.equal((await invoke('publishStory',request(`/api/stories/${id}/publish`,{revision:1}),id)).status,409);
const publishPair=await Promise.all([invoke('publishStory',request(`/api/stories/${id}/publish`,{revision:2}),id),invoke('publishStory',request(`/api/stories/${id}/publish`,{revision:2}),id)]);
const published=publishPair[0];assert.equal(published.status,200);assert.equal(publishPair[0].body.token,publishPair[1].body.token);
const token=published.body.token;assert.match(token,/^[a-f0-9]{32}$/);assert.equal(published.body.url,origin+`/watch/${token}`);
const ownerSession=webcrypto.randomUUID();
const excluded=await invoke('addEvent',request(`/api/public/${token}/events`,{event:'start',sessionId:ownerSession}),token);assert.equal(excluded.body.excluded,true);
assert.equal((await invoke('addFeedback',request(`/api/public/${token}/feedback`,{sessionId:ownerSession,choice:'moved'}),token)).status,403);
assert.equal((await invoke('insights',id)).body.starts,0);
const draft=structuredClone(changed);draft.title='Draft-only title';
await invoke('updateStory',request(`/api/stories/${id}`,{data:draft,revision:2},'PUT'),id);
identity=null;
const snapshot=await invoke('getPublicStory',token);assert.equal(snapshot.body.data.title,story.title);assert.equal(snapshot.body.ownerId,undefined);assert.equal(snapshot.body.revision,undefined);
assert.equal((await invoke('getStory',id)).status,401);
assert.equal((await invoke('getAsset',new Request(origin+`/api/assets/${photoId}`),photoId)).status,404);
const asset=await api.getAsset(new Request(origin+`/api/assets/${photoId}?publication=${token}`),photoId);assert.equal(asset.status,200);assert.equal((await asset.arrayBuffer()).byteLength,png.length);
const range=await api.getAsset(new Request(origin+`/api/assets/${photoId}?publication=${token}`,{headers:{range:'bytes=2-5'}}),photoId);assert.equal(range.status,206);assert.equal((await range.arrayBuffer()).byteLength,4);
const sessionId=webcrypto.randomUUID();
assert.equal((await invoke('addEvent',request(`/api/public/${token}/events`,{event:'start',sessionId,publishedAt:1}),token)).status,409);
await invoke('addEvent',request(`/api/public/${token}/events`,{event:'start',sessionId}),token);
await invoke('addEvent',request(`/api/public/${token}/events`,{event:'start',sessionId}),token);
assert.equal((await invoke('addEvent',request(`/api/public/${token}/events`,{event:'chapter',sessionId,chapterId:'missing'}),token)).status,400);
await invoke('addEvent',request(`/api/public/${token}/events`,{event:'chapter',sessionId,chapterId:'one'}),token);
await invoke('addEvent',request(`/api/public/${token}/events`,{event:'complete',sessionId}),token);
await invoke('addEvent',request(`/api/public/${token}/events`,{event:'complete',sessionId}),token);
await invoke('addFeedback',request(`/api/public/${token}/feedback`,{sessionId,choice:'moved',note:'Stayed with me.'}),token);
await invoke('addFeedback',request(`/api/public/${token}/feedback`,{sessionId,choice:'confused',note:'Duplicate.'}),token);
assert.equal((await invoke('insights',id)).status,401);
identity={userId:'owner-a',displayName:'Author A',email:'a@example.test',fullName:null};
const insights=(await invoke('insights',id)).body;assert.equal(insights.starts,1);assert.equal(insights.completions,1);assert.equal(insights.completionRate,1);assert.equal(insights.chapters[0].views,1);assert.equal(insights.feedbackCount,1);assert.equal(insights.feedback[0].choice,'moved');
assert.notEqual(sqlite.prepare('SELECT session_hash FROM story_events LIMIT 1').get().session_hash,sessionId);
const republished=await invoke('publishStory',request(`/api/stories/${id}/publish`,{revision:3}),id);assert.equal(republished.body.token,token);
assert.equal((await invoke('getPublicStory',token)).body.data.title,'Draft-only title');assert.equal((await invoke('insights',id)).body.starts,0);
await invoke('revokePublication',request(`/api/stories/${id}/publish`,undefined,'DELETE'),id);
assert.equal((await invoke('getPublicStory',token)).status,404);
identity=null;assert.equal((await invoke('getAsset',new Request(origin+`/api/assets/${photoId}?publication=${token}`),photoId)).status,404);
identity={userId:'owner-a',displayName:'Author A',email:'a@example.test',fullName:null};
const renewed=await invoke('publishStory',request(`/api/stories/${id}/publish`,{revision:3}),id);assert.notEqual(renewed.body.token,token);assert.equal((await invoke('getPublicStory',token)).status,404);
for(let count=1;count<20;count++)assert.equal((await invoke('uploadAsset',multipart(`photo-${count}.png`,png,'image/png'),id)).status,201);
assert.equal((await invoke('uploadAsset',multipart('too-many.png',png,'image/png'),id)).status,409);
assert.equal(objects.size,20);
const concurrent=await Promise.all([invoke('updateStory',request(`/api/stories/${id}`,{data:draft,revision:3},'PUT'),id),invoke('updateStory',request(`/api/stories/${id}`,{data:draft,revision:3},'PUT'),id)]);
assert.deepEqual(concurrent.map(result=>result.status).sort(),[200,409]);
await invoke('deleteStory',request(`/api/stories/${id}`,undefined,'DELETE'),id);
assert.equal((await invoke('getStory',id)).status,404);assert.equal((await invoke('getPublicStory',renewed.body.token)).status,404);assert.equal(objects.size,0);
assert.equal(sqlite.prepare('SELECT COUNT(*) AS count FROM story_events').get().count,0);
assert.equal(sqlite.prepare('SELECT COUNT(*) AS count FROM story_feedback').get().count,0);
assert.equal(sqlite.prepare('SELECT COUNT(*) AS count FROM story_assets').get().count,0);
assert.equal(api.sniffAsset(new Uint8Array([0,1,2,3])),null);
const disabledStory=structuredClone(story);disabledStory.feedback=false;
const disabled=await invoke('createStory',request('/api/stories',{data:disabledStory}));
const disabledId=disabled.body.story.id;
assert.equal((await invoke('insights',disabledId)).body.completionRate,null);
const disabledPublication=await invoke('publishStory',request(`/api/stories/${disabledId}/publish`,{revision:1}),disabledId);
identity=null;
assert.equal((await invoke('addFeedback',request(`/api/public/${disabledPublication.body.token}/feedback`,{sessionId,choice:'moved'}),disabledPublication.body.token)).status,403);
assert.notEqual(await api.sessionHash(token,1,sessionId),await api.sessionHash(token,2,sessionId));
// New rows must fail explicitly at a bounded publication budget, rather than claim success.
const capEvent=sqlite.prepare('INSERT INTO story_events(id,story_id,publication_time,session_hash,event,chapter_id,created_at) VALUES(?,?,?,?,?,?,?)');
sqlite.exec('BEGIN');for(let i=0;i<50000;i++)capEvent.run('event-cap-'+i,disabledId,disabledPublication.body.publishedAt,'session-'+i,'start','',Date.now());sqlite.exec('COMMIT');
assert.equal((await invoke('addEvent',request(`/api/public/${disabledPublication.body.token}/events`,{sessionId:webcrypto.randomUUID(),event:'start'}),disabledPublication.body.token)).status,429);
const enabledSnapshot=structuredClone(disabledStory);enabledSnapshot.feedback=true;sqlite.prepare('UPDATE publications SET data=? WHERE token=?').run(JSON.stringify(enabledSnapshot),disabledPublication.body.token);
const capFeedback=sqlite.prepare('INSERT INTO story_feedback(id,story_id,publication_time,session_hash,choice,note,created_at) VALUES(?,?,?,?,?,?,?)');
sqlite.exec('BEGIN');for(let i=0;i<5000;i++)capFeedback.run('feedback-cap-'+i,disabledId,disabledPublication.body.publishedAt,'session-'+i,'clear','',Date.now());sqlite.exec('COMMIT');
assert.equal((await invoke('addFeedback',request(`/api/public/${disabledPublication.body.token}/feedback`,{sessionId:webcrypto.randomUUID(),choice:'moved'}),disabledPublication.body.token)).status,429);
console.log('PASS: API identity, CSRF/limits, owner isolation, revision conflicts, uploads, snapshot publication, public asset access/ranges, analytics/feedback deduplication, revoke/republish, file cap, cascade deletion.');
sqlite.close();
