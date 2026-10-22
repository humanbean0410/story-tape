import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const read=f=>readFileSync(new URL('../dist/'+f,import.meta.url),'utf8');
const motion=new Function(read('film-motion.js').replace(/export /g,'')+'; return {opening,retreat,DOLLY_MS,CROP_MS};')();
assert.equal(motion.CROP_MS,850);assert.equal(motion.DOLLY_MS,4800);
assert.equal(motion.opening(850/4800).crop,1);assert.ok(motion.opening(850/4800).lens<.1,'lens continues slowly after rapid frame narrowing');
let last={crop:0,lens:0,background:0,gear:0};for(let i=0;i<=1000;i++){const now=motion.opening(i/1000);for(const k of Object.keys(last)){assert.ok(now[k]>=last[k]&&now[k]>=0&&now[k]<=1);assert.ok(now[k]-last[k]<.02);}last=now;}
assert.deepEqual(last,{crop:1,lens:1,background:1,gear:1});
assert.ok(!/revealThreshold|discard|alphaHash|gl_FragCoord/.test(read('stage-reveal.js')),'background uses continuous transparency');
assert.ok(!/c\+=.*random/.test(read('camera-kit.js')),'no film-grain noise added');
assert.ok(!/monitor/i.test(read('index.html')+read('scene-only.js')+read('studio-controls.js')),'no monitor feature remains');
const html=read('index.html');assert.ok(!/entry-action|shot-strip|next-set|shot-prev|shot-next/.test(html),'no duplicate navigation or large transport UI');
assert.ok(!/loadAsync|GLTFLoader/.test(read('performers.js')),'no humanoid library loaded');
assert.ok(/duration:10000/.test(read('station3d.js')));assert.ok(/if\(state.trainDue&&now>=state.trainDue\)/.test(read('scene-only.js')),'train runs without a performance click');
assert.equal((read('scene-only.js').match(/addEventListener\('keydown'/g)||[]).length,1,'one global keyboard dispatcher only');
console.log('Rapid crop / slow lens, monotone smooth reveal, automatic 10 s train, no grain, no monitor, no actor loading, minimal entry and keyboard regression checks passed.');
