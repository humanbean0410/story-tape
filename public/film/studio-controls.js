import * as THREE from 'three';
import { loadGLTF,loadJSON } from './asset-loader.js?v=20261013-monologue';
import { renderFilm } from './camera-kit.js?v=20261014-previs-v2';

export function bindStudioControls(engine){
  const canvas=engine.canvas;engine.enabled=true;engine.pointerContacts=new Map();
  canvas.addEventListener('pointermove',event=>{
    if(!engine.enabled)return;
    if(engine.pointerContacts.has(event.pointerId)){const old=engine.pointerContacts.get(event.pointerId);engine.gestureDistance=(engine.gestureDistance||0)+Math.hypot(event.clientX-old.x,event.clientY-old.y);if(engine.gestureDistance>8)engine.dragged=true;}
    if(engine.backstage&&engine.pointerContacts.has(event.pointerId)){
      ensureOrbit(engine);
      const old=engine.pointerContacts.get(event.pointerId),dx=event.clientX-old.x,dy=event.clientY-old.y;
      engine.pointerContacts.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(engine.pointerContacts.size===2){const p=[...engine.pointerContacts.values()];const distance=Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y);if(engine.pinchDistance)engine.orbit.distance=THREE.MathUtils.clamp(engine.orbit.distance*engine.pinchDistance/distance,8,48);engine.pinchDistance=distance;}
      else if(engine.orbit){engine.orbit.yaw=THREE.MathUtils.clamp(engine.orbit.yaw-dx*.005,-1.5,1.5);engine.orbit.pitch=THREE.MathUtils.clamp(engine.orbit.pitch+dy*.004,.12,1.2);}
      engine.flight=null;applyOrbit(engine);return;
    }
    if(engine.pointerContacts.has(event.pointerId))engine.pointerContacts.set(event.pointerId,{x:event.clientX,y:event.clientY});
    engine.pick(event);
  });
  canvas.addEventListener('pointerleave',()=>{if(engine.enabled){engine.hover=null;engine.onHover(null);}});
  canvas.addEventListener('pointerdown',event=>{if(!engine.enabled)return;if(!engine.pointerContacts.size){engine.down={x:event.clientX,y:event.clientY,id:event.pointerId};engine.dragged=false;engine.multiTouch=false;engine.gestureDistance=0;}else engine.multiTouch=true;engine.pointerContacts.set(event.pointerId,{x:event.clientX,y:event.clientY});if(engine.backstage){if(engine.flight)engine.orbit=null;ensureOrbit(engine);canvas.setPointerCapture(event.pointerId);}});
  const release=event=>{const click=engine.down?.id===event.pointerId&&!engine.dragged&&!engine.multiTouch&&Math.hypot(event.clientX-engine.down.x,event.clientY-engine.down.y)<=8;engine.pointerContacts.delete(event.pointerId);engine.pinchDistance=null;if(!engine.enabled||!engine.interactive||!click)return;engine.down=null;const id=engine.pick(event);if(id)engine.onVisit(id);};
  canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',()=>{engine.pointerContacts.clear();engine.pinchDistance=null;engine.down=null;engine.dragged=true;});
  canvas.addEventListener('wheel',event=>{if(!engine.enabled||!engine.backstage)return;event.preventDefault();if(engine.flight)engine.orbit=null;ensureOrbit(engine);engine.orbit.distance=THREE.MathUtils.clamp(engine.orbit.distance*Math.exp(event.deltaY*.001),8,48);engine.flight=null;applyOrbit(engine);},{passive:false});
}
function ensureOrbit(engine){if(engine.orbit)return;const d=engine.position.clone().sub(engine.target);engine.orbit={yaw:Math.atan2(d.x,d.z),pitch:Math.asin(d.y/d.length()),distance:d.length(),target:engine.target.clone()};}
function applyOrbit(engine){if(!engine.orbit)return;const o=engine.orbit;engine.target.copy(o.target);engine.position.set(Math.sin(o.yaw)*Math.cos(o.pitch)*o.distance,Math.sin(o.pitch)*o.distance,Math.cos(o.yaw)*Math.cos(o.pitch)*o.distance).add(o.target);}
export async function loadStudioRig(engine){
  const result=await loadGLTF('assets/studio-rig.glb');engine.rig=result.scene;engine.rig.visible=false;
  engine.rig.traverse(o=>{if(o.isMesh){o.castShadow=false;o.receiveShadow=false;const material=o.material;if(/RigBulb/i.test(material.name)){material.emissive=new THREE.Color('#fff3d4');material.emissiveIntensity=2;}}});engine.scene.add(engine.rig);
}
export function backstageFrame(engine){
  const frame=engine.studioFrame?{pos:new THREE.Vector3(...engine.studioFrame.pos),target:new THREE.Vector3(...engine.studioFrame.target)}:engine.kind==='interior'?{pos:new THREE.Vector3(-9.5,6.5,17),target:new THREE.Vector3(0,1.6,-.5)}:engine.kind==='station'?{pos:new THREE.Vector3(14,10,24),target:new THREE.Vector3(.8,1.4,1.8)}:{pos:new THREE.Vector3(-10,8.2,20),target:new THREE.Vector3(.8,3.15,.5)};
  if(engine.mobile)frame.pos.sub(frame.target).multiplyScalar(2.1).add(frame.target);
  return frame;
}
export function setBackstage(engine,value){
  engine.backstage=value;engine.recording=false;if(value)engine.cinematic=false;engine.camera.fov=engine.mobile?44:(engine.kind==='station'?36:35);engine.camera.updateProjectionMatrix();engine.orbit=null;engine.active=null;engine.hover=null;engine.onHover(null);if(engine.rig)engine.rig.visible=value;
  const clipping=value?[new THREE.Plane(new THREE.Vector3(0,0,1),engine.kind==='courtyard'?7.4:6),new THREE.Plane(new THREE.Vector3(1,0,0),8.2),new THREE.Plane(new THREE.Vector3(-1,0,0),9.8),new THREE.Plane(new THREE.Vector3(0,0,-1),8.3)]:[];
  engine.renderer.localClippingEnabled=true;
  engine.model?.traverse(o=>{if(o.userData.background)o.visible=engine.stageReveal?true:!value;if(o.isMesh){for(const m of Array.isArray(o.material)?o.material:[o.material]){m.clippingPlanes=clipping;m.needsUpdate=true;}}});
  const frame=value?backstageFrame(engine):engine.home();const delta=frame.pos.clone().sub(frame.target);engine.orbitSeed={yaw:Math.atan2(delta.x,delta.z),pitch:Math.asin(delta.y/delta.length()),distance:delta.length(),target:frame.target.clone()};engine.flyTo(null,1450);if(value&&!engine.flight)ensureOrbit(engine);
}
export function updateStudioCamera(engine,now,dt,pointer,depthAmount=1){
  if(engine.flight){const f=engine.flight,t=Math.min(1,(now-f.start)/f.duration),k=t*t*(3-2*t);if(f.via){engine.position.copy(f.fromPos).multiplyScalar((1-k)**2).addScaledVector(f.via,2*(1-k)*k).addScaledVector(f.pos,k*k);}else engine.position.lerpVectors(f.fromPos,f.pos,k);engine.target.lerpVectors(f.fromTarget,f.target,k);if(t===1){engine.flight=null;if(engine.backstage){engine.orbit=null;ensureOrbit(engine);}}}
  const responsive=1-Math.exp(-dt*4);engine.drift.lerp(new THREE.Vector2(...pointer),responsive);engine.camera.position.copy(engine.position);
  if(!engine.reducedMotion.matches&&!engine.flight&&!engine.backstage&&!engine.recording){const d=engine.position.clone().sub(engine.target);d.applyAxisAngle(new THREE.Vector3(0,1,0),engine.drift.x*.035*depthAmount);engine.camera.position.copy(engine.target).add(d);engine.camera.position.y+=engine.drift.y*.075*depthAmount;}
  engine.camera.lookAt(engine.target);engine.camera.updateMatrixWorld(true);
}
export function renderStudio(engine){for(const f of engine.revealMeshes||[])f.mesh.visible=(f.inverse?1-f.uniform.value:f.uniform.value)>.001;for(const f of engine.revealMaterials||[])f.material.depthWrite=(f.inverse?1-f.uniform.value:f.uniform.value)>.999;if(engine.recording&&!engine.backstage){renderFilm(engine);return;}const r=engine.rect;engine.renderer.setRenderTarget(null);engine.renderer.setScissorTest(false);engine.renderer.setViewport(0,0,innerWidth,innerHeight);engine.renderer.clear();engine.renderer.setScissorTest(true);engine.renderer.setScissor(r[0],innerHeight-r[1]-r[3],r[2],r[3]);engine.renderer.setViewport(r[0],innerHeight-r[1]-r[3],r[2],r[3]);engine.renderer.render(engine.scene,engine.camera);}
export function captureStudio(engine){renderStudio(engine);if(!engine.cinematic)return engine.canvas.toDataURL('image/jpeg',.94);const r=engine.rect,scale=engine.canvas.width/innerWidth,canvas=document.createElement('canvas');canvas.width=Math.round(r[2]*scale);canvas.height=Math.round(r[3]*scale);canvas.getContext('2d').drawImage(engine.canvas,Math.round(r[0]*scale),Math.round(r[1]*scale),canvas.width,canvas.height,0,0,canvas.width,canvas.height);return canvas.toDataURL('image/jpeg',.94);}
