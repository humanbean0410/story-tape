import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {StoryPlayback,buildTimeline,DIRECTION} from '../public/film/story-cues.js';
import {SCRIPT} from '../public/film/script-book.js';
import * as THREE from '../public/film/vendor/three.module.js';
import {plugRoute,earbudRoute,routePoint,cableGeometry} from '../public/film/tape-motion.js';
const config=readFileSync(new URL('../public/film/production-config.js',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replace(/export /g,'');
const {SETS}=new Function('THREE',config+';return {SETS};')(THREE);
for(const scene of SCRIPT.scenes){
  assert.ok(DIRECTION[scene.id].every(c=>SETS[scene.id].shots.some(s=>s.id===c[1])));
  const dialogue=[],sounds=[],shots=[],ends=[];const play=new StoryPlayback({subtitle:b=>{if(b)dialogue.push([b.who,b.text]);},shot:s=>shots.push(s),sound:s=>sounds.push(s),ended:id=>ends.push(id)});
  play.start(scene.id,0);const duration=buildTimeline(scene.id).at(-1).end+5000;
  for(let t=100;t<duration+30000;t+=100)play.update(t);
  assert.deepEqual(dialogue,scene.lines.filter(([who])=>!['动作','结尾'].includes(who)),`${scene.id}: all dialogue appears once in script order`);
  assert.equal(ends.length,1);assert.equal(sounds.filter(s=>s==='arrival').length,scene.id==='station'?1:0,'arrival cue only accompanies the scripted train');
}
let changes=0;const manual=new StoryPlayback({subtitle(){},sound(){},shot(){changes++;},ended(){}});manual.start('interior',0);manual.manual=true;for(let t=100;t<30000;t+=100)manual.update(t);assert.equal(changes,0);manual.follow();assert.equal(changes,1);const elapsed=manual.elapsed;manual.update(30100,true);assert.equal(manual.elapsed,elapsed,'paper book pauses the script clock');
const box=new THREE.Box3(new THREE.Vector3(-.7,.1,-1.9),new THREE.Vector3(3,1.45,1.4)),start=new THREE.Vector3(-.64,.145,1.95),end=new THREE.Vector3(3.18,.474,-1.17),path=plugRoute(start,end,box);
for(let i=0;i<=500;i++)assert.ok(!box.clone().expandByScalar(.04).containsPoint(routePoint(path,i/500)),'jack route goes above and around the case');
for(const [w,h,pos,fov] of [[1280,720,[0,8.4,7.3],33],[390,844,[10,10,7],50]]){
 const camera=new THREE.PerspectiveCamera(fov,w/h,.04,70);camera.position.set(...pos);camera.lookAt(new THREE.Vector3(-.1,.37,-.12));camera.updateMatrixWorld(true);
 for(const side of [-1,1])for(let i=0;i<=100;i++){const p=earbudRoute(new THREE.Vector3(side<0?-2.7:-1.05,.17,side<0?1.59:1.76),camera,box,side,i/100);assert.ok(!box.clone().expandByScalar(.02).containsPoint(p));}
}
const geometry=cableGeometry([new THREE.Vector3(3.4,.5,-1.17),new THREE.Vector3(3.5,.25,2),new THREE.Vector3(-1.2,.25,2.3)],box),p=geometry.attributes.position;
for(let i=0;i<p.count;i++)assert.ok(!box.containsPoint(new THREE.Vector3().fromBufferAttribute(p,i)),'wire thickness also clears the body');
console.log('All six acts subtitle every spoken line once; scene hold, manual camera override, script resume, one train arrival and desktop/mobile collision-safe earphones passed.');
