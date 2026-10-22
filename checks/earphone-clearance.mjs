import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from '../dist/vendor/three.module.js';
import {loadGeometry} from './model-geometry.mjs';
import {routePoint,plugRoute,earbudRoute,jackCablePoints,earbudCablePoints,cableGeometry} from '../dist/tape-motion.js';
const meta=JSON.parse(readFileSync(new URL('../dist/assets/cassette-deck-info.json',import.meta.url)));
const scene=await loadGeometry(new URL('../dist/assets/cassette-deck.glb',import.meta.url)),get=name=>scene.getObjectByName(name);
const tapeBox=new THREE.Box3().setFromObject(get('Cassette'));
for(const name of ['EarbudLeft','EarbudRight','Earphones_static','EarphoneRemote','JackPlug'])assert.ok(!new THREE.Box3().setFromObject(get(name)).intersectsBox(tapeBox),`${name}: its complete exported mesh clears the initial cassette`);
get('DoorPivot').rotation[meta.door.axis]=meta.door.closed;get('Cassette').position.set(...meta.cassette.insertPosition);get('Cassette').rotation.set(...meta.cassette.insertRotation);scene.updateMatrixWorld(true);
const playerBox=new THREE.Box3().setFromObject(get('Player'));playerBox.max.y=Math.max(playerBox.max.y,1.45);
const surfaces=[new THREE.Box3().setFromObject(get('TrackReceipt'))],junction=new THREE.Vector3(...meta.earphones.junction),jack=get('JackPlug'),jackRest=jack.position.clone(),jackQ=jack.quaternion.clone(),path=plugRoute(jackRest,new THREE.Vector3(...meta.jack.insertPosition),playerBox);
const buds=['EarbudLeft','EarbudRight'].map(get),rests=buds.map(o=>({position:o.position.clone(),quaternion:o.quaternion.clone()}));
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
const solidRay=new THREE.Raycaster(),rayDirection=new THREE.Vector3(.17,.91,.34).normalize();
function insideSolid(object,point){let inside=false;object.traverse(mesh=>{if(inside||!mesh.isMesh||!new THREE.Box3().setFromObject(mesh).containsPoint(point))return;mesh.material.side=THREE.DoubleSide;solidRay.set(point,rayDirection);const hits=solidRay.intersectObject(mesh,false).filter(h=>h.distance>1e-6);const distances=hits.map(h=>h.distance).filter((d,i,a)=>!i||Math.abs(d-a[i-1])>1e-5);if(distances.length%2)inside=true;});return inside;}
let checked=0;
for(const [w,h,pos,fov]of[[1280,720,meta.camera.pos,33],[390,844,[10,10,7],50]]){
 const camera=new THREE.PerspectiveCamera(fov,w/h,.04,70);camera.position.set(...pos);camera.lookAt(new THREE.Vector3(...meta.camera.target));camera.updateMatrixWorld(true);
 for(let i=0;i<=120;i++){
  const t=i/120,amount=(t*6650-1550)/3200,k=ease(amount);
  const plug=ease((t*6650-150)/950);jack.position.copy(routePoint(path,plug));jack.quaternion.slerpQuaternions(jackQ,new THREE.Quaternion().setFromEuler(new THREE.Euler(...meta.jack.insertRotation)),plug);
  buds.forEach((o,j)=>{const start=o.parent.localToWorld(rests[j].position.clone()),p=earbudRoute(start,camera,playerBox,j?-1+2:-1,amount);o.position.copy(o.parent.worldToLocal(p));o.quaternion.slerpQuaternions(rests[j].quaternion,camera.quaternion,k);});scene.updateMatrixWorld(true);
  const budBoxes=buds.map(o=>new THREE.Box3().setFromObject(o)),jackBox=new THREE.Box3().setFromObject(jack);
  for(const b of budBoxes)assert.ok(!b.intersectsBox(playerBox),`earbud full geometry avoids player at ${w}px, frame ${i}`);
  assert.ok(!budBoxes[0].intersectsBox(budBoxes[1]),`earbuds stay separated at ${w}px, frame ${i}`);
  const exit=jack.localToWorld(new THREE.Vector3(...meta.jack.cable_exit_local)),direction=new THREE.Vector3(-1,0,0).transformDirection(jack.matrixWorld);
  const geometries=[cableGeometry(jackCablePoints(exit,playerBox,meta.earphones.remote_ports,junction,direction),playerBox,{raisedSurfaces:surfaces})];
  for(let j=0;j<buds.length;j++){const o=buds[j],anchor=o.localToWorld(new THREE.Vector3(...meta.earphones.cable_exit_local)),axis=new THREE.Vector3(0,0,1).transformDirection(o.matrixWorld);geometries.push(cableGeometry(earbudCablePoints(junction,anchor,axis,playerBox,j?1:-1),playerBox,{raisedSurfaces:surfaces}));}
  geometries.forEach((geometry,wire)=>{
   const positions=geometry.attributes.position;
   for(let v=0;v<positions.count;v++){
    const point=new THREE.Vector3().fromBufferAttribute(positions,v);
    assert.ok(!playerBox.containsPoint(point),`wire ${wire} thickness avoids player, ${w}px frame ${i}`);
    assert.ok(point.y>=.0376,`wire stays above the paper, ${w}px frame ${i}`);
    for(const surface of surfaces)if(point.x>surface.min.x+.025&&point.x<surface.max.x-.025&&point.z>surface.min.z+.025&&point.z<surface.max.z-.025)assert.ok(point.y>surface.max.y,`wire clears receipt at frame ${i}`);
    for(let b=0;b<budBoxes.length;b++)if(wire!==b+1)assert.ok(!budBoxes[b].containsPoint(point),`wire ${wire} avoids earbud ${b}, ${w}px frame ${i}: ${point.toArray()}`);
    if(wire===0&&v>35&&jackBox.containsPoint(point))assert.ok(!insideSolid(jack,point),`cord avoids the real jack surface, ${w}px frame ${i}, vertex ${v}`);
   }
   checked+=positions.count;geometry.dispose();
  });
 }
}
console.log(`Actual exported earbud bodies, cassette footprint, player/lid, receipt, jack outlet and ${checked} dynamic cable vertices pass in desktop and portrait.`);
