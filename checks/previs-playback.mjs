import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
import * as THREE from '../public/film/vendor/three.module.js';
let now=0,raf;const events=new Map(),messages=[],instances=[];
const parent={postMessage:m=>messages.push(m)};
class SetStub{
 constructor(canvas,options){Object.assign(this,{ready:true,position:new THREE.Vector3(),target:new THREE.Vector3(),stageReveal:{value:1},gearReveal:{value:1},rig:{visible:false},renderer:{},camera:{position:new THREE.Vector3()},trainStarts:0});instances.push(this);queueMicrotask(options.onReady);}
 setBackstage(){} stopPerformance(){} resize(){} frame(){return{pos:new THREE.Vector3(0,2,10),target:new THREE.Vector3(0,2,0)};}
 update(){this.camera.position.copy(this.position);} prepareTrain(){} startTrain(){this.trainStarts++;}
}
class AudioStub{constructor(){this.ctx={currentTime:0,suspend:async()=>{},resume:async()=>{}};this.cues=0;}stopTrain(){}setScene(){}async unlock(){}trainCue(){this.cues++;}}
const nodes=new Map();const context=vm.createContext({console,structuredClone,URLSearchParams,location:{origin:'http://local',search:''},innerWidth:1280,innerHeight:720,document:{getElementById:id=>{if(!nodes.has(id))nodes.set(id,{textContent:'',hidden:true});return nodes.get(id);}},matchMedia:()=>({matches:false}),performance:{now:()=>now},parent,addEventListener:(name,fn)=>events.set(name,fn),requestAnimationFrame:fn=>raf=fn,setTimeout,clearTimeout,MediaRecorder:undefined});
const synthetic=(exports)=>new vm.SyntheticModule(Object.keys(exports),function(){for(const[k,v]of Object.entries(exports))this.setExport(k,v);},{context});
const module=new vm.SourceTextModule(await fs.readFile('public/film/previs-engine.js','utf8'),{context});
await module.link(spec=>spec==='three'?synthetic(THREE):spec.includes('stage-reveal')?synthetic({configureStageReveal:()=>{}}):spec.includes('sound-stage')?synthetic({SoundStage:AudioStub}):synthetic({Scene3D:SetStub,Station3D:SetStub,Interior3D:SetStub,Courtyard3D:SetStub,Diner3D:SetStub,Alley3D:SetStub}));await module.evaluate();
const shot={id:'s1',name:'推进',preset:'master',seconds:6,focal:35,aperture:8,focus:null,aspect:'2.39',light:1,movement:'push',easing:'smooth',startOffset:[0,0,0],endOffset:[0,0,-1.2],targetOffset:[0,0,0],trainAt:null};
const item={scene:'interior',sceneId:'interior1',shot,sceneOffset:12};
async function send(data,origin='http://local'){await events.get('message')({origin,source:parent,data});}
function tick(t){now=t;raf(t);}
await send({type:'previs:play',items:[item]});const engine=instances[0];tick(0);const start=engine.position.z;tick(3000);assert.ok(engine.position.z<start-.5,'push moves the physical camera during playback');assert.equal(messages.at(-1).sceneElapsed,15,'single-shot playback retains scene audio offset');
await send({type:'previs:pause'});const pausedZ=engine.position.z;tick(9000);assert.equal(engine.position.z,pausedZ,'pause freezes camera');await send({type:'previs:resume'});tick(10000);assert.ok(engine.position.z<pausedZ,'resume continues from pause rather than restarting');tick(12000);assert.equal(messages.at(-1).status,'done');assert.ok(Math.abs(engine.position.z-8.8)<1e-6,'playback arrives at authored end frame');
await send({...item,type:'previs:seek',progress:.5});assert.ok(Math.abs(engine.position.z-9.4)<1e-6,'scrub previews the same interpolated camera path');await send({...item,type:'previs:seek',progress:1});assert.ok(Math.abs(engine.position.z-8.8)<1e-6,'end frame preview matches playback');
const hold={...item,shot:{...shot,movement:'hold',startOffset:[.4,0,.7]}};await send({type:'previs:play',items:[hold]});tick(13000);const fixed=engine.position.clone();tick(15000);assert.ok(engine.position.equals(fixed),'fixed shot stays fixed even with old nonzero end offset');await send({type:'previs:stop'});assert.equal(messages.at(-1).status,'ready');
const before=instances.length;await send({type:'previs:play',items:[{...item,scene:'station'}]},'http://untrusted');assert.equal(instances.length,before,'cross-origin messages ignored');
console.log('PASS: real camera motion, authored endpoints, pause/resume, scrub parity, fixed shots, single-shot audio offset, origin validation.');
