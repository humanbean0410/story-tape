import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import * as THREE from '../dist/vendor/three.module.js';
const read=f=>readFileSync(new URL('../dist/'+f,import.meta.url),'utf8'),clean=s=>s.replace(/^import .*;\n/gm,'').replace(/export /g,'');
const config=new Function('THREE',clean(read('production-config.js'))+';return {SETS,SET_ORDER,getShot};')(THREE),{SCRIPT}=new Function(clean(read('script-book.js'))+';return {SCRIPT};')();
const elements=new Map(),element=id=>{if(!elements.has(id))elements.set(id,{hidden:false,textContent:'',dataset:{},classList:{add(){},remove(){}},addEventListener(type,fn){this[type]=fn;},setAttribute(){}});return elements.get(id);};
const document={getElementById:element,body:{dataset:{},classList:{add(){},remove(){}}},documentElement:{style:{setProperty(){}}}};
class TapeDeck{constructor(){this.visible=false;}setTrack(){}update(){}open(){this.visible=true;}}
class SceneControls{attach(){}clear(){}}
class SoundStage{unlock(){return Promise.resolve();}setScene(){}stopTrain(){}foley(){}}
class StoryPlayback{constructor(){this.manual=false;}start(){}stop(){}}
const fakeEngine=kind=>({kind,ready:true,enabled:true,stageReveal:{value:0},gearReveal:{value:0},focalLength:35,camera:{fov:35,aspect:1280/720},rect:[0,0,1280,535],position:new THREE.Vector3(20,20,20),target:new THREE.Vector3(),setBackstage(value){this.backstage=value;},resize(){},frame(){return {pos:new THREE.Vector3(2,3,4),target:new THREE.Vector3(0,1,0)};},stopPerformance(){},flyFrame(){throw new Error('scene entry must not run a dolly');}});
let source=clean(read('film-motion.js'))+clean(read('scene-only.js')).split('syncUI();requestAnimationFrame(animate);function startScene')[0];
const run=new Function('THREE','SETS','SET_ORDER','getShot','SCRIPT','LENSES','TapeDeck','SceneControls','SoundStage','StoryPlayback','document','matchMedia','location','history','addEventListener','requestAnimationFrame','setTimeout','clearTimeout','innerWidth','innerHeight','fakeEngine',source+`;engine=fakeEngine('casa');ensureSet=async id=>fakeEngine(id);let cuts=0;cut=()=>{cuts++;return Promise.resolve();};return {state,switchSet,openFilm,startFilmTake,returnToTape,get engine(){return engine;},get cuts(){return cuts;},takeNumbers};`);
const app=run(THREE,config.SETS,config.SET_ORDER,config.getShot,SCRIPT,[28,35,50,85],TapeDeck,SceneControls,SoundStage,StoryPlayback,document,()=>({matches:false}),{hash:'#casa',pathname:'/',search:''},{replaceState(){}},()=>{},fn=>fn(),fn=>{fn();return 0;},()=>{},1280,720,fakeEngine);
app.state.phase='recording';await app.switchSet('station');assert.equal(app.cuts,0);assert.equal(app.state.phase,'recording');assert.equal(app.state.backstage,false);assert.equal(app.engine.backstage,false);assert.equal(app.engine.cinemaAmount,1);assert.equal(app.engine.gearReveal.value,1);assert.deepEqual(app.engine.position.toArray(),[2,3,4]);assert.equal(app.takeNumbers.station,1);
await app.openFilm('station');assert.equal(app.state.phase,'prologue');assert.equal(app.engine.cinemaAmount,1);app.startFilmTake();assert.equal(app.state.phase,'recording');
app.returnToTape();assert.equal(app.cuts,0,'returning to tape does not expose a studio retreat');
console.log('Scene switches and cassette opening enter the fixed cinema frame directly; no dolly or studio retreat, and an explicit cut remains separate.');
