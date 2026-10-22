const REQUEST_MS=20000;
const base=new URL('.',import.meta.url);
let manifestPromise;

function deadline(job,controller,milliseconds){
  let timer;
  const expiry=new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(new Error('资源下载超时'));},milliseconds);});
  return Promise.race([job,expiry]).finally(()=>clearTimeout(timer));
}
export async function fetchBytes(url,{onProgress=()=>{},timeout=REQUEST_MS,attempts=3}={}){
  let failure;
  for(let attempt=0;attempt<attempts;attempt++){
    const controller=new AbortController(),target=new URL(url,base);
    if(attempt)target.searchParams.set('retry',`${attempt}-${Date.now()}`);
    try{
      return await deadline((async()=>{
        const response=await fetch(target,{signal:controller.signal,credentials:'same-origin',cache:attempt?'reload':'default'});
        if(!response.ok)throw new Error(`资源响应 ${response.status}`);
        if(/text\/html/.test(response.headers.get('content-type')||''))throw new Error('资源返回了访问页面');
        if(!response.body?.getReader){const bytes=new Uint8Array(await response.arrayBuffer());onProgress(bytes.length);return bytes;}
        const reader=response.body.getReader(),parts=[];let count=0;
        while(true){const {done,value}=await reader.read();if(done)break;parts.push(value);count+=value.length;if(!controller.signal.aborted)onProgress(count);}
        const bytes=new Uint8Array(count);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}return bytes;
      })(),controller,timeout);
    }catch(error){failure=error;controller.abort();onProgress(0);}
  }
  throw failure;
}
export async function loadJSON(url){return JSON.parse(new TextDecoder().decode(await fetchBytes(url)));}
async function verify(bytes,digest){
  if(!globalThis.crypto?.subtle)return;
  const hash=await crypto.subtle.digest('SHA-256',bytes),actual=[...new Uint8Array(hash)].map(n=>n.toString(16).padStart(2,'0')).join('');
  if(actual!==digest)throw new Error('资源下载不完整');
}
export async function readPack(pack,{onProgress=()=>{},timeout=REQUEST_MS,attempts=3}={}){
  const counts=new Array(pack.chunks.length).fill(0),parts=new Array(pack.chunks.length);let cursor=0;
  const report=()=>onProgress(Math.min(1,counts.reduce((sum,n)=>sum+n,0)/pack.packedBytes));
  async function worker(){
    while(cursor<pack.chunks.length){const index=cursor++,chunk=pack.chunks[index];
      const bytes=await fetchBytes(chunk.url,{timeout,attempts,onProgress:count=>{counts[index]=Math.min(count,chunk.bytes);report();}});
      if(bytes.length!==chunk.bytes)throw new Error('资源长度不完整');await verify(bytes,chunk.sha256);parts[index]=bytes;counts[index]=bytes.length;report();
    }
  }
  await Promise.all([worker(),worker()]);
  const compressed=new Uint8Array(pack.packedBytes);let offset=0;for(const part of parts){compressed.set(part,offset);offset+=part.length;}
  const controller=new AbortController();
  const bytes=new Uint8Array(await deadline(new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer(),controller,15000));
  if(bytes.length!==pack.bytes||new TextDecoder().decode(bytes.subarray(0,4))!=='glTF'||new DataView(bytes.buffer).getUint32(8,true)!==bytes.length)throw new Error('模型文件不完整');
  await verify(bytes,pack.sha256);onProgress(1);return bytes.buffer;
}
export async function loadModelBytes(url,options={}){
  if(typeof DecompressionStream==='undefined')return (await fetchBytes(url,{onProgress:count=>options.onProgress?.(Math.min(.95,count/10000000))})).buffer;
  manifestPromise??=loadJSON('assets/model-packs.json?v=20261013-monologue').catch(error=>{manifestPromise=null;throw error;});
  const manifest=await manifestPromise,path=url.split('?')[0],pack=manifest[path];
  if(!pack)throw new Error('模型资源未就位');return readPack(pack,options);
}
