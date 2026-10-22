import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from '../dist/vendor/three.module.js';
const read=f=>readFileSync(new URL('../dist/'+f,import.meta.url),'utf8');
const clean=s=>s.replace(/^import .*;\n/gm,'').replace(/export /g,'');
const config=new Function('THREE',clean(read('production-config.js'))+';return {SETS,SET_ORDER,getShot};')(THREE);
const {SCRIPT}=new Function(clean(read('script-book.js'))+';return {SCRIPT};')();
assert.deepEqual(SCRIPT.scenes.map(s=>s.id),config.SET_ORDER);assert.equal(config.SET_ORDER.length,6);assert.ok(SCRIPT.scenes.every(s=>s.lines.length>=12&&s.camera&&s.sound));
const elements=new Map(),element=id=>{if(!elements.has(id))elements.set(id,{hidden:false,textContent:'',classList:{add(){},remove(){}},addEventListener(type,fn){this[type]=fn;},setAttribute(){}});return elements.get(id);};
const document={getElementById:element,body:{dataset:{},classList:{add(){},remove(){}}},documentElement:{style:{setProperty(){}}}};
class TapeDeck{setTrack(){}update(){}constructor(){this.visible=false;}}
class SceneControls{clear(){}update(){}}
class StoryPlayback{constructor(){this.manual=false;}update(){}stop(){}follow(){this.manual=false;}}
class SoundStage{setTapeMotor(){}unlock(){return Promise.resolve();}setScene(){}tick(){}mechanism(){}}
let source=clean(read('scene-only.js'));source=clean(read('film-motion.js'))+source.slice(0,source.indexOf('syncUI();requestAnimationFrame(animate);function startScene'));
const run=new Function('THREE','SETS','SET_ORDER','getShot','SCRIPT','LENSES','TapeDeck','SceneControls','SoundStage','StoryPlayback','document','matchMedia','location','addEventListener','requestAnimationFrame','innerWidth','innerHeight',source+`;let changed=0,started=0;switchSet=async id=>{changed++;activeId=id;state.phase='recording';started++;};return {state,selection,takeNumbers,animate,selectShot,bind(e){engine=e;},get changes(){return changed;},get starts(){return started;},get active(){return activeId;}};`);
const app=run(THREE,config.SETS,config.SET_ORDER,config.getShot,SCRIPT,[28,35,50,85],TapeDeck,SceneControls,SoundStage,StoryPlayback,document,()=>({matches:false}),{hash:'#casa'},()=>{},()=>{},1280,720);
let fly;
app.bind({ready:true,rect:[0,0,1280,535],focalLength:35,update(){},flyTo(id){fly=id;}});app.state.phase='recording';app.state.recordStart=0;app.state.playlist=true;app.takeNumbers.casa=3;
app.animate(120000);assert.equal(app.changes,0,'a two-minute take remains in its act, regardless of playback flag');
app.selectShot('window');assert.equal(app.state.phase,'recording');assert.equal(app.takeNumbers.casa,3);
element('master-shot').click();assert.equal(fly,'shot:master');assert.equal(app.state.phase,'recording');assert.equal(app.takeNumbers.casa,3,'master return keeps the same take');
await element('next-act').click();assert.equal(app.active,'station');assert.equal(app.changes,1);assert.equal(app.starts,1,'one explicit click advances exactly one act');
console.log('Six matching screenplay acts, indefinite scene hold, explicit next act, and master return within the current take passed.');
