import { GLTFLoader } from './vendor/GLTFLoader.js';
import { loadModelBytes } from './asset-transport.js?v=20261013-monologue';
export { loadJSON } from './asset-transport.js?v=20261013-monologue';
export async function loadGLTF(url,options={}){
  const data=await loadModelBytes(url,{...options,onProgress:progress=>{options.onProgress?.(progress);dispatchEvent(new CustomEvent('model-progress',{detail:{url,progress}}));}});
  let timer;
  try{return await Promise.race([new GLTFLoader().parseAsync(data,new URL('.',new URL(url,location.href)).href),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('模型解码超时')),30000);})]);}
  finally{clearTimeout(timer);}
}
