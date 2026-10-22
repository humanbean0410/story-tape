import type { PrevisReference } from './previs-model';
const DB='story-tape:previs-media:v2';
const open=()=>new Promise<IDBDatabase>((resolve,reject)=>{const request=indexedDB.open(DB,1);request.onupgradeneeded=()=>request.result.createObjectStore('media');request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);});
export async function storeMedia(id:string,blob:Blob){const db=await open();try{await new Promise<void>((resolve,reject)=>{const tx=db.transaction('media','readwrite');tx.objectStore('media').put(blob,id);tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);});}finally{db.close();}}
export async function loadMedia(id:string):Promise<Blob|null>{const db=await open();try{return await new Promise((resolve,reject)=>{const req=db.transaction('media').objectStore('media').get(id);req.onsuccess=()=>resolve(req.result||null);req.onerror=()=>reject(req.error);});}finally{db.close();}}
export async function removeMedia(id:string){const db=await open();try{await new Promise<void>((resolve,reject)=>{const tx=db.transaction('media','readwrite');tx.objectStore('media').delete(id);tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);});}finally{db.close();}}
export async function importMedia(file:File):Promise<PrevisReference>{
 if(file.size>20*1024*1024)throw Error('本地素材每个不超过 20 MiB。');
 if(!/^(image\/(jpeg|png|webp)|audio\/(mpeg|mp3|mp4|wav|x-wav|ogg|aac|webm))$/.test(file.type))throw Error('请使用 JPG / PNG / WebP 或 MP3 / M4A / WAV / OGG 音频。');
 const reference:PrevisReference={id:crypto.randomUUID(),name:file.name.slice(0,200),type:file.type,role:file.type.startsWith('audio/')?'sound':'space',accepted:true,note:''};
 const url=URL.createObjectURL(file);
 try{if(file.type.startsWith('image/')){await new Promise<void>((resolve,reject)=>{const image=new Image();image.onload=()=>{reference.width=image.naturalWidth;reference.height=image.naturalHeight;resolve();};image.onerror=()=>reject(Error('图片无法读取'));image.src=url;});if(Math.min(reference.width!,reference.height!)<720)reference.note='较短边不足 720px：细节判断可能有限。';}
 else{await new Promise<void>((resolve,reject)=>{const a=new Audio();const timer=setTimeout(()=>reject(Error('音频元信息读取超时')),12000);a.onloadedmetadata=()=>{clearTimeout(timer);if(!Number.isFinite(a.duration)){reject(Error('无法确认音频长度'));return;}reference.seconds=a.duration;resolve();};a.onerror=()=>{clearTimeout(timer);reject(Error('音频无法读取'));};a.src=url;});}
 await storeMedia(reference.id,file);return reference;}finally{URL.revokeObjectURL(url);}
}
