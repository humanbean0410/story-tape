import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import ts from 'typescript';
import { webcrypto } from 'node:crypto';
import * as zod from 'zod';
const context=vm.createContext({crypto:webcrypto,console,Set,JSON,String});const modules=new Map();
const z=new vm.SyntheticModule(Object.keys(zod),function(){for(const key of Object.keys(zod))this.setExport(key,zod[key]);},{context});
async function compile(name){if(modules.has(name))return modules.get(name);const source=ts.transpileModule(await fs.readFile(name,'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;const m=new vm.SourceTextModule(source,{context,identifier:name});modules.set(name,m);await m.link(async spec=>spec==='zod'?z:compile(path.resolve(path.dirname(name),spec+'.ts')));return m;}
const m=await compile(path.resolve('lib/previs-model.ts'));await m.evaluate();const {PrevisProjectSchema,makePrevisProject,makePrevisScene,scenePlanMarkdown,movementOffsets,previsSequence}=m.namespace;
for(const id of ['casa','station','interior','courtyard','diner','alley'])assert.equal(PrevisProjectSchema.safeParse(makePrevisProject(id)).success,true);
const p=JSON.parse(JSON.stringify(makePrevisProject('station')));p.scenes.push(JSON.parse(JSON.stringify(makePrevisScene('alley'))));const selected=p.scenes[0].shots[1];assert.equal(selected.trainAt,1);assert.equal(selected.seconds,15,'passing take covers pre-warning + passage');
const before=JSON.parse(JSON.stringify(p));selected.focal=85;assert.deepEqual(p.scenes[0].references,before.scenes[0].references);assert.equal(p.scenes[0].shots[1].trainAt,before.scenes[0].shots[1].trainAt,'lens edits preserve event timing');assert.equal(p.scenes[1].shots[0].focal,before.scenes[1].shots[0].focal,'a shot edit preserves other scenes');
p.scenes.reverse();assert.equal(p.scenes[1].shots[1].trainAt,1,'scene reorder carries camera and event data');const roundtrip=PrevisProjectSchema.parse(JSON.parse(JSON.stringify(p)));assert.equal(roundtrip.scenes[1].shots[1].focal,85);assert.match(scenePlanMarkdown(roundtrip),/85mm/);
for(const mutate of [p=>p.scenes[0].shots[0].focal=0,p=>p.scenes[0].shots[0].startOffset=[999,0,0],p=>p.scenes[0].shots[0].preset='nonexistent',p=>p.scenes[0].shots[1].id=p.scenes[0].shots[0].id,p=>p.scenes[0].shots[0].aspect='fake']){const bad=JSON.parse(JSON.stringify(roundtrip));mutate(bad);assert.equal(PrevisProjectSchema.safeParse(bad).success,false);}
assert.deepEqual(Array.from(movementOffsets('push')),[0,0,-1.2]);
const sceneA=roundtrip.scenes[0],sceneB=roundtrip.scenes[1];
assert.equal(previsSequence(roundtrip,sceneB.id,sceneB.shots[1].id,'shot').length,1);
assert.equal(previsSequence(roundtrip,sceneB.id,sceneB.shots[1].id,'shot')[0].sceneOffset,sceneB.shots[0].seconds);
assert.equal(previsSequence(roundtrip,sceneA.id,sceneA.shots[0].id,'scene').length,sceneA.shots.length);
assert.equal(previsSequence(roundtrip,sceneA.id,sceneA.shots[0].id,'project').length,6);
assert.deepEqual(Array.from(movementOffsets('push',[2,1,3])),[2,1,1.8],'movement starts relative to edited starting camera');
assert.equal(makePrevisScene('interior').shots[0].movement,'push','new scenes demonstrate authored motion');
assert.equal(PrevisProjectSchema.parse({...roundtrip,scenes:[{...sceneA,shots:sceneA.shots.map(s=>({...s,movement:'hold'}))}]}).scenes[0].shots[0].movement,'hold','old fixed shots remain fixed');
console.log('PASS: all six plans, valid camera contracts, edits preserve event/scene data, reorder/JSON/Markdown deliverables, malformed imports rejected.');
