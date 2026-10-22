import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {earbudRoute,earbudCablePoints,cableGeometry} from '../dist/tape-motion.js';
import * as THREE from '../dist/vendor/three.module.js';
const source=readFileSync(new URL('../dist/tape-deck.js',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replace('export class TapeDeck','class TapeDeck');
const meta=JSON.parse(readFileSync(new URL('../dist/assets/cassette-deck-info.json',import.meta.url),'utf8'));
for(const [width,height,rect] of [[1280,720,{left:0,top:0,width:1280,height:720}],[390,844,{left:0,top:0,width:390,height:844}],[1280,720,{left:90,top:45,width:920,height:590}]]){
  const elements=new Map(),element=id=>{if(!elements.has(id))elements.set(id,{hidden:true,style:{},addEventListener(){},getBoundingClientRect:()=>rect,setPointerCapture(){},hasPointerCapture:()=>false});return elements.get(id);};
  const document={getElementById:element};
  const TapeDeck=new Function('THREE','SETS','SET_ORDER','ease','document','addEventListener','innerWidth','innerHeight','earbudRoute','cableGeometry',source+';return TapeDeck;')(THREE,{casa:{number:'01',name:'街角店铺'}},['casa'],n=>Math.max(0,Math.min(1,n)),document,()=>{},width,height,earbudRoute,cableGeometry);
  const deck=new TapeDeck({reducedMotion:{matches:false},audio:{unlock:()=>Promise.resolve(),mechanism(){}}});deck.meta=meta;
  deck.model=new THREE.Group();deck.cassette=new THREE.Mesh(new THREE.BoxGeometry(...meta.cassette.local_size),new THREE.MeshBasicMaterial());deck.cassette.name='Cassette';deck.cassette.position.set(...meta.cassette.start.position);deck.model.add(deck.cassette);
  deck.bay=new THREE.Mesh(new THREE.BoxGeometry(3.2,.25,1.85),new THREE.MeshBasicMaterial());deck.bay.position.set(...meta.cassette.insertPosition);deck.model.add(deck.bay);
  deck.camera=new THREE.PerspectiveCamera(width<=600?50:33,rect.width/rect.height,.04,70);deck.camera.position.set(...(width<=600?[10,10,7]:meta.camera.pos));deck.camera.lookAt(new THREE.Vector3(...meta.camera.target));deck.camera.updateMatrixWorld(true);deck.ready=true;deck.stageReady=true;deck.dropOutline={visible:false,material:{}};
  deck.rest={pos:deck.cassette.position.clone(),rotation:deck.cassette.rotation.clone()};
  const project=p=>{p=p.clone().project(deck.camera);return{clientX:rect.left+(.5+p.x*.5)*rect.width,clientY:rect.top+(.5-p.y*.5)*rect.height,pointerId:1,preventDefault(){}};};
  const bounds=deck.screenBounds(deck.cassette),pickup={clientX:bounds.left+12,clientY:(bounds.top+bounds.bottom)/2,pointerId:1,preventDefault(){}};
  assert.ok(deck.isCassetteHit(pickup,'Earphones'),'cassette edge remains grabbable under a cable');
  deck.down(pickup);assert.ok(deck.drag);
  const targetPoint=deck.drag.point.clone();targetPoint.x+=meta.cassette.insertPosition[0]-deck.drag.from.x;targetPoint.z+=meta.cassette.insertPosition[2]-deck.drag.from.z;
  // Pointerup can contain the final position without an intervening move.
  await deck.up(project(targetPoint));assert.equal(deck.animation.type,'insert','final release position accepts edge pickup');assert.match(element('entry-status').textContent,/已放入/);
  deck.animation=null;deck.inserted=true;deck.stageReady=false;deck.play();assert.ok(deck.waitingToPlay);await deck.setReady(true);assert.equal(deck.animation.type,'play','waiting for the scene resumes automatically');
  deck.animation=null;deck.inserted=false;deck.cassette.position.copy(deck.rest.pos);deck.down(pickup);deck.up({...pickup,clientX:rect.left+5,clientY:rect.top+5});assert.equal(deck.animation.type,'return','drop away from the player returns the cassette');
}
console.log('Edge pickup, cable overlap, final pointerup without pointermove, embedded canvas offsets, mobile projection and automatic playback after loading passed.');

// The listener sees both physical earbuds leave the table before the scene fades.
{
  const elements=new Map(),element=id=>{if(!elements.has(id))elements.set(id,{hidden:true,style:{},addEventListener(){}});return elements.get(id);};
  const TapeDeck=new Function('THREE','SETS','SET_ORDER','ease','document','addEventListener','innerWidth','innerHeight','earbudRoute','earbudCablePoints','cableGeometry',source+';return TapeDeck;')(THREE,{casa:{number:'01',name:'街角店铺'}},['casa'],n=>{n=Math.max(0,Math.min(1,n));return n*n*(3-2*n);},{getElementById:element},()=>{},1280,720,earbudRoute,earbudCablePoints,cableGeometry);
  const deck=new TapeDeck({reducedMotion:{matches:false},audio:{}});deck.scene=new THREE.Scene();deck.playerBox=new THREE.Box3(new THREE.Vector3(-.7,.1,-1.9),new THREE.Vector3(3,1.45,1.4));deck.camera=new THREE.PerspectiveCamera(33,1280/720,.04,70);deck.camera.position.set(...meta.camera.pos);deck.camera.lookAt(new THREE.Vector3(...meta.camera.target));
  const parent=new THREE.Group();deck.scene.add(parent);deck.earbuds=[new THREE.Group(),new THREE.Group()];deck.earbuds.forEach((o,i)=>{parent.add(o);o.position.set(i?-1.05:-2.7,.17,i?1.76:1.59);});parent.updateMatrixWorld(true);deck.earbudRest=deck.earbuds.map(o=>({position:o.position.clone(),quaternion:o.quaternion.clone()}));deck.tableCord={visible:true};deck.jack=new THREE.Group();deck.jack.position.set(...meta.jack.insertPosition);deck.scene.add(deck.jack);deck.earbudCables=deck.earbuds.map(()=>{const m=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshStandardMaterial());deck.scene.add(m);return m;});
  deck.wearEarbuds(.5);assert.ok(deck.earbuds.every(o=>o.visible&&o.position.y>2),'both buds are visibly lifted towards the listener');assert.equal(deck.tableCord.visible,false);assert.ok(deck.earbudCables.every(m=>m.visible&&Array.from(m.geometry.attributes.position.array).every(Number.isFinite)),'modeled cables follow the lifted buds');
  deck.wearEarbuds(1);assert.ok(deck.earbuds.every(o=>!o.visible),'buds pass beyond the viewing edge when worn');assert.ok(deck.earbudCables.every(m=>!m.visible));
}
console.log('Physical earbud pickup, listener approach and cable continuity passed.');
