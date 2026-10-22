import * as THREE from 'three';
import { Scene3D } from './scene3d.js?v=20261014-previs-v2';
import { Station3D } from './station3d.js?v=20261014-previs-v2';
import { Interior3D } from './interior3d.js?v=20261014-previs-v2';
import { Courtyard3D } from './courtyard3d.js?v=20261014-previs-v2';
import { Diner3D, Alley3D } from './story-set3d.js?v=20261014-previs-v2';
import { configureStageReveal } from './stage-reveal.js?v=20261013-monologue';
import { SoundStage } from './sound-stage.js?v=20261015-pause';
const canvas=document.getElementById('scene'),status=document.getElementById('status');
const classes={casa:Scene3D,station:Station3D,interior:Interior3D,courtyard:Courtyard3D,diner:Diner3D,alley:Alley3D};
const send=data=>parent.postMessage(data,location.origin);
const sets=new Map(),pending=new Map(),reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
let paused=false,pausedElapsed=0,pausedAt=0;
let engine,renderer,current=null,playlist=null,playIndex=0,shotStart=0,sceneBase=0,totalBase=0,generation=0,loading=false,trainFired=false,trainDue=0,last=0,lastMessage=0,wide=false,recorder=null,recordRequest=null,recordChunks=[],outputCanvas=null,exportInput=null;
const audio=new SoundStage();audio.preloadMusic=()=>Promise.resolve(null);audio.playMusic=()=>Promise.resolve(false);
function state(kind,elapsed=0){send({type:'previs:state',status:kind,canResume:paused&&!!playlist,scene:current?.scene,sceneId:current?.sceneId,shotId:current?.shot.id,elapsed,sceneElapsed:sceneBase+elapsed,totalElapsed:totalBase+elapsed});}
function report(error,requestId){status.textContent=error.message||String(error);document.getElementById('retry').hidden=false;send({type:'previs:error',message:status.textContent,requestId});}
async function ensure(id){
 if(sets.has(id))return sets.get(id);if(pending.has(id))return pending.get(id);
 const job=new Promise((resolve,reject)=>{let next;const timer=setTimeout(()=>reject(Error('布景加载超时，可重新加载后重试。')),90000);
  next=new classes[id](canvas,{sceneOnly:true,renderer,reducedMotion,onVisit:()=>{},onHover:()=>{},onError:e=>{clearTimeout(timer);reject(e);},onReady:()=>{clearTimeout(timer);if(!renderer)renderer=next.renderer;next.enabled=false;next.interactive=false;configureStageReveal(next);sets.set(id,next);resolve(next);}});
 });pending.set(id,job);try{return await job;}finally{pending.delete(id);}
}
function localOffset(base,value){const back=base.pos.clone().sub(base.target).normalize(),right=new THREE.Vector3(0,1,0).cross(back).normalize();return right.multiplyScalar(value[0]).add(new THREE.Vector3(0,value[1],0)).addScaledVector(back,value[2]);}
function configure(item){
 if(engine)engine.enabled=false;engine=sets.get(item.scene);engine.enabled=true;engine.stopPerformance?.();engine.setBackstage(false);engine.flight=null;engine.orbit=null;engine.cinematic=true;engine.recording=true;engine.cinemaAmount=1;engine.stageReveal.value=1;engine.gearReveal.value=1;engine.rig.visible=false;
 current=item;wide=false;engine.frameAspect=Number(item.shot.aspect);engine.focalLength=item.shot.focal;engine.apertureOverride=item.shot.aperture;engine.focusOverride=item.shot.focus;engine.resize({preserveView:true});
 const base=engine.frame('shot:'+item.shot.preset);item.base=base;trainFired=false;trainDue=0;audio.stopTrain();audio.setScene(item.scene);at(0);status.textContent='';
 send({type:'previs:ready',scene:item.scene,sceneId:item.sceneId,canRecord:typeof MediaRecorder!=='undefined'&&typeof canvas.captureStream==='function'});
}
function at(progress){
 if(!engine||!current||wide)return;const s=current.shot,k=s.easing==='smooth'?progress*progress*(3-2*progress):progress;
 const start=localOffset(current.base,s.startOffset),end=localOffset(current.base,s.movement==='hold'?s.startOffset:s.endOffset);
 engine.position.copy(current.base.pos).add(start.lerp(end,k));engine.target.copy(current.base.target).add(localOffset(current.base,s.targetOffset));engine.flight=null;
}
function valid(item){const s=item?.shot;return !!classes[item?.scene]&&typeof item?.sceneId==='string'&&s&&Number.isFinite(s.seconds)&&s.seconds>=2&&s.seconds<=30&&Number.isFinite(s.focal)&&s.focal>=18&&s.focal<=135&&['2.39','1.85','1.7778','1','0.5625'].includes(s.aspect)&&[s.startOffset,s.endOffset,s.targetOffset].every(v=>Array.isArray(v)&&v.length===3&&v.every(n=>Number.isFinite(n)&&Math.abs(n)<=12))&&Number.isFinite(s.light)&&s.light>=0&&s.light<=1&&Number.isFinite(s.aperture)&&s.aperture>=1.4&&s.aperture<=16&&(s.focus==null||Number.isFinite(s.focus)&&s.focus>=.1&&s.focus<=80)&&(s.trainAt==null||Number.isFinite(s.trainAt)&&s.trainAt>=0&&s.trainAt<=30);}
async function show(item,token){loading=true;state('loading');status.textContent='布景正在加载…';await ensure(item.scene);if(token!==generation)return false;configure(structuredClone(item));loading=false;state('ready');return true;}
function reset(abortRecord=true){if(paused)audio.ctx?.resume().catch(()=>{});generation++;playlist=null;paused=false;pausedElapsed=0;loading=false;audio.stopTrain();audio.ambient?.gain.setTargetAtTime(0,audio.ctx.currentTime,.1);trainDue=0;engine?.stopPerformance?.();state('paused');if(abortRecord&&recorder){recordRequest=null;recorder.stop();recorder=null;}}
async function start(items,record=false,requestId){
 if(!Array.isArray(items)||!items.length||items.length>72||!items.every(valid))throw Error('镜头参数无效。');
 reset();const token=generation;playIndex=0;sceneBase=items[0].sceneOffset||0;totalBase=0;const accepted=items.map(x=>structuredClone(x));
 if(!await show(accepted[0],token))return;
 try{await audio.unlock();audio.setScene(current.scene,true);}catch{}
 if(record){await setupRecording(requestId);}
 if(token!==generation)return;playlist=accepted;shotStart=performance.now();state('playing');
}
async function next(){
 const sequence=playlist;if(!sequence)return;const token=generation;const previous=current,total=current.shot.seconds;
 if(playIndex+1>=sequence.length){at(1);playlist=null;audio.stopTrain();audio.ambient?.gain.setTargetAtTime(0,audio.ctx.currentTime,.1);state('done',total);if(recorder){recorder.stop();recorder=null;}return;}
 loading=true;if(recorder?.state==='recording')recorder.pause();state('loading',total);playIndex++;totalBase+=total;sceneBase=sequence[playIndex].sceneOffset??(sequence[playIndex].sceneId===previous.sceneId?sceneBase+total:0);
 if(await show(sequence[playIndex],token)){shotStart=performance.now();if(recorder?.state==='paused')recorder.resume();state('playing');}
}
function render(now,dt){
 if(!engine?.ready)return;engine.update(now,dt,{light:current?.shot.light??.8,mode:wide?'backstage':'filming',pointer:[0,0],depthView:0,depthAmount:0});
 if(outputCanvas&&recorder){drawOutput(outputCanvas,true);}
}
function crop(target){const r=engine.rect,scale=canvas.width/innerWidth;const context=target.getContext('2d'),fit=Math.min(target.width/r[2],target.height/r[3]),w=r[2]*fit,h=r[3]*fit;context.fillStyle='#08090a';context.fillRect(0,0,target.width,target.height);context.drawImage(canvas,Math.round(r[0]*scale),Math.round(r[1]*scale),Math.round(r[2]*scale),Math.round(r[3]*scale),(target.width-w)/2,(target.height-h)/2,w,h);}
function drawOutput(target,subtitle=false){crop(target);if(subtitle&&current?.shot.text){const c=target.getContext('2d'),font=Math.round(target.height*.044),max=target.width*.8,text=current.shot.text; c.font=font+'px system-ui';c.textAlign='center';const chars=[...text],lines=[];let line='';for(const ch of chars){if(ch==='\n'||c.measureText(line+ch).width>max){lines.push(line);line=ch==='\n'?'':ch;}else line+=ch;}if(line)lines.push(line);const visible=lines.slice(0,3),lineHeight=font*1.5,y=target.height-font*.9-visible.length*lineHeight;c.fillStyle='rgba(0,0,0,.48)';c.fillRect(0,y-font*.65,target.width,target.height-y+font*.65);c.fillStyle='#fff';visible.forEach((t,i)=>c.fillText(t,target.width/2,y+i*lineHeight));}}
function capture(requestId){if(loading||!engine?.ready||wide)throw Error('请在电影视角中等待布景就位。');render(performance.now(),0);const r=engine.rect,scale=canvas.width/innerWidth,out=document.createElement('canvas');out.width=Math.round(r[2]*scale);out.height=Math.round(r[3]*scale);crop(out);send({type:'previs:frame',dataUrl:out.toDataURL('image/png'),width:out.width,height:out.height,requestId});}
async function setupRecording(requestId){
 if(typeof MediaRecorder==='undefined'||typeof canvas.captureStream!=='function')throw Error('当前浏览器不支持动态分镜导出，请用支持 MediaRecorder 的浏览器。');
 const mime=['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm'].find(t=>MediaRecorder.isTypeSupported(t));if(!mime)throw Error('当前浏览器不支持 WebM 导出。');
 outputCanvas=document.createElement('canvas');const aspect=Number(current.shot.aspect);outputCanvas.width=1280;outputCanvas.height=Math.round(1280/aspect);if(outputCanvas.height>1280){outputCanvas.height=1280;outputCanvas.width=Math.round(1280*aspect);}
 render(performance.now(),0);drawOutput(outputCanvas,true);const stream=outputCanvas.captureStream(24);
 if(audio.ctx){const destination=audio.ctx.createMediaStreamDestination();audio.master.connect(destination);try{if(parent.__previsAudioStream){exportInput=audio.ctx.createMediaStreamSource(parent.__previsAudioStream);exportInput.connect(destination);}}catch{}for(const t of destination.stream.getAudioTracks())stream.addTrack(t);exportInput={node:exportInput,destination};}
 recordRequest=requestId;const chunks=[],recordCanvas=outputCanvas,mix=exportInput,r=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:4500000});recorder=r;
 r.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};r.onerror=e=>report(Error('动态分镜录制失败，请重试。'),requestId);
 r.onstop=()=>{if(recordRequest===requestId&&chunks.length){send({type:'previs:video',blob:new Blob(chunks,{type:mime}),mime,requestId});recordRequest=null;}stream.getTracks().forEach(t=>t.stop());if(mix){mix.node?.disconnect();try{audio.master.disconnect(mix.destination);}catch{}if(exportInput===mix)exportInput=null;}if(outputCanvas===recordCanvas)outputCanvas=null;};r.start(200);
}
addEventListener('message',async e=>{
 if(e.origin!==location.origin||e.source!==parent||!e.data?.type?.startsWith('previs:'))return;
 const m=e.data;try{if(m.type==='previs:shot'){if(!valid(m))throw Error('镜头参数无效。');reset();sceneBase=0;totalBase=0;await show(m,generation);}
 else if(m.type==='previs:play'||m.type==='previs:record'){await start(m.items,m.type==='previs:record',m.requestId);}
 else if(m.type==='previs:stop'){reset();at(0);render(performance.now(),0);state('ready');}
 else if(m.type==='previs:pause'&&playlist&&!loading&&!recorder){pausedElapsed=Math.max(0,Math.min(current.shot.seconds,(performance.now()-shotStart)/1000));paused=true;pausedAt=performance.now();audio.ctx?.suspend().catch(()=>{});if(trainDue)trainDue=Math.max(0,trainDue-performance.now())||1;audio.ambient?.gain.setTargetAtTime(0,audio.ctx.currentTime,.1);state('paused',pausedElapsed);}
 else if(m.type==='previs:resume'&&playlist&&paused){shotStart=performance.now()-pausedElapsed*1000;if(trainDue)trainDue=performance.now()+trainDue;if(engine.trainRun)engine.trainRun.start+=performance.now()-pausedAt;paused=false;audio.ctx?.resume().catch(()=>{});state('playing',pausedElapsed);}
 else if(m.type==='previs:seek'){if(!valid(m)||!Number.isFinite(m.progress))throw Error('预览参数无效。');const same=current?.sceneId===m.sceneId&&current?.shot.id===m.shot.id;reset();sceneBase=0;totalBase=0;const token=generation;if(same){configure(structuredClone(m));loading=false;}else if(!await show(m,token))return;const progress=Math.max(0,Math.min(1,m.progress));at(progress);render(performance.now(),0);state('ready',current.shot.seconds*progress);}

 else if(m.type==='previs:capture'){capture(m.requestId);}
 else if(m.type==='previs:wide'&&engine?.ready){reset();wide=true;engine.setBackstage(true);engine.cinemaAmount=0;engine.stageReveal.value=0;engine.gearReveal.value=0;engine.resize({preserveView:true});status.textContent='摄影棚全景 · 可拖动绕场观察';state('ready');}
 }catch(error){loading=false;reset();report(error,m.requestId);}
});
addEventListener('resize',()=>engine?.resize({preserveView:true}));
addEventListener('model-progress',e=>{if(loading)status.textContent='布景加载 '+Math.round(e.detail.progress*100)+'%';});
addEventListener('visibilitychange',()=>{if(document.hidden){reset();}});
function animate(now){const dt=Math.min((now-last)/1000||.016,.05);last=now;
 if(playlist&&!paused&&!loading&&engine?.ready){const elapsed=Math.max(0,Math.min(current.shot.seconds,(now-shotStart)/1000));at(elapsed/current.shot.seconds);
  if(current.scene==='station'&&!trainFired&&current.shot.trainAt!==null&&elapsed>=current.shot.trainAt){trainFired=true;engine.prepareTrain();engine.trainQueued=true;audio.trainCue(2.3);trainDue=now+2300;}
  if(trainDue&&now>=trainDue){trainDue=0;engine.trainQueued=false;engine.startTrain();}
  if(now-lastMessage>100){state('playing',elapsed);lastMessage=now;}render(now,dt);if(elapsed>=current.shot.seconds){next().catch(e=>{loading=false;reset();report(e);});}
 }else if(!paused)render(now,dt);requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
const id=new URLSearchParams(location.search).get('scene');send({type:'previs:ready',scene:classes[id]?id:'interior',handshake:true});
