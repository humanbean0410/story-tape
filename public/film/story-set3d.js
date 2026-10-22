import { replacePerformers } from './performers.js?v=20261013-monologue';
import * as THREE from 'three';
import { loadGLTF,loadJSON } from './asset-loader.js?v=20261013-monologue';
import { Scene3D } from './scene3d.js?v=20261014-previs-v2';
import { loadStudioRig,updateStudioCamera,renderStudio } from './studio-controls.js?v=20261014-previs-v2';
import { updateLens } from './camera-kit.js?v=20261014-previs-v2';
import { shotFrame } from './production-config.js?v=20261014-previs-v2';

const SPECS={
  diner:{file:'vintage-diner',work:'#302f29',night:'#15201a',fill:'#d9e6bf',sun:'#ffe6be',lightPower:16,studio:{pos:[-9,6,17],target:[0,1.6,-.8]}},
  alley:{file:'night-alley',work:'#262e32',night:'#081c30',fill:'#76bddb',sun:'#70b5db',lightPower:28,studio:{pos:[9,7,21],target:[-.5,2,-3]}}
};
class StorySet3D extends Scene3D{
  async load(){
    this.kind=this.setId;const spec=SPECS[this.kind];this.studioFrame=spec.studio;this.daySky.set(spec.work);this.nightSky.set(spec.night);
    this.hemi=this.scene.children.find(o=>o.isHemisphereLight);this.hemi.color.set(spec.fill);this.hemi.groundColor.set(this.kind==='alley'?'#162b3c':'#61533c');this.sun.color.set(spec.sun);this.sun.position.set(-3,8,6);
    this.practicals.forEach(l=>this.scene.remove(l));this.practicals=[];this.glows=[];this.atlasLight={value:1};
    try{
      const [result,meta]=await Promise.all([loadGLTF(`assets/${spec.file}.glb?v=20261013-monologue`),loadJSON(`assets/${spec.file}-info.json?v=20261013-monologue`)]);this.meta=meta;this.model=result.scene;this.scene.add(this.model);this.model.updateMatrixWorld(true);await replacePerformers(this);if(this.kind==='alley'){replaceOldFlora(this.model);const flora=await loadGLTF('assets/night-alley-flora.glb?v=20261013-monologue');this.model.add(flora.scene);}else{replaceOldBoothBacks(this.model);const seating=await loadGLTF('assets/diner-upholstery.glb?v=20261013-monologue');this.model.add(seating.scene);}
      this.model.traverse(o=>{
        if(o.name.startsWith('Anchor_'))this.anchors[o.userData.category||o.name.slice(7)]=o.getWorldPosition(new THREE.Vector3());
        if(!o.isMesh)return;
        if(/Baked_Static|Backdrop_NightAlley/.test(o.name)){
          const old=o.material,material=new THREE.MeshBasicMaterial({map:old.map,color:old.color});material.onBeforeCompile=shader=>{shader.uniforms.uRoomLight=this.atlasLight;shader.fragmentShader='uniform float uRoomLight;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\ndiffuseColor.rgb *= uRoomLight;');};o.material=material;
        }
        if(/Practical.*Glow|DinerPractical|lamp_glow/i.test(o.name)){o.material=o.material.clone();o.material.emissive=new THREE.Color('#ffd08b');o.material.emissiveIntensity=.1;this.glows.push(o);}
      });
      const fallback=this.kind==='alley'?{couple:[-2.2,1.65,-2],flowers:[-3.5,.5,-1.6]}:{man:[-1.55,1.55,-.3],woman:[1.55,1.55,-.3],table:[0,1.07,-.3],jukebox:[0,2.25,-2.15]};
      Object.entries(fallback).forEach(([key,p])=>{this.anchors[key]??=new THREE.Vector3(...p);});
      const positions=meta.practicalPositions||meta.lightPositions||meta.practical_lights_gltf||(this.kind==='alley'?[[-2.8,3.2,-2.6]]:[[-1.15,2.3,-2.0],[1.15,2.3,-2.0]]);
      positions.forEach(p=>{const light=new THREE.PointLight(p.color||'#ffc779',0,9,2);light.position.set(...(Array.isArray(p)?p:p.position));light.userData.power=p.intensity||spec.lightPower;this.scene.add(light);this.practicals.push(light);});
      this.key=new THREE.SpotLight('#ffd5a5',0,22,.7,.8,1.5);this.key.position.set(this.kind==='alley'?-3:-2,4.6,3.2);this.key.target.position.copy(this.anchors.couple||new THREE.Vector3(0,1.4,-.3));this.scene.add(this.key,this.key.target);
      await loadStudioRig(this);this.ready=true;this.resize();this.onReady();
    }catch(error){this.onError(error);}
  }
  baseHome(){return{pos:new THREE.Vector3(...(this.kind==='alley'?[1.8,2.35,9.1]:[0,2.1,8.5])),target:new THREE.Vector3(...(this.kind==='alley'?[.25,1.65,-2.7]:[0,1.65,-1]))};}
  frame(id){return shotFrame(this,id)||this.home();}
  stopPerformance(){}
  update(now,dt,{light,pointer}){
    if(!this.ready)return;this.interactive=false;const spec=SPECS[this.kind],work=this.backstage?1:1-(this.cinemaAmount??1);this.scene.background.copy(this.nightSky).lerp(this.daySky,work);this.scene.fog.color.copy(this.scene.background);this.scene.fog.near=this.backstage&&this.mobile?85:40;this.scene.fog.far=this.backstage&&this.mobile?110:85;
    this.sun.intensity=(this.kind==='alley'?.45:.75)+work*1.3;this.hemi.intensity=(this.kind==='alley'?.7:.9)+work*.6;this.key.intensity=light*(this.kind==='alley'?18:24);this.practicals.forEach(l=>l.intensity=light*l.userData.power);this.glows.forEach(o=>o.material.emissiveIntensity=.1+light*2.5);this.atlasLight.value=this.kind==='alley'?.64+light*.36+work*(.36-light*.36):.56+light*.3+work*(.44-light*.3);this.renderer.toneMappingExposure=this.kind==='alley'?1.06:1.12;
    if(this.recording)updateLens(this);updateStudioCamera(this,now,dt,pointer);
    renderStudio(this);
  }
}
export class Diner3D extends StorySet3D{get setId(){return'diner';}}
export class Alley3D extends StorySet3D{get setId(){return'alley';}}

function replaceOldFlora(model){
  model.traverse(o=>{
    if(!o.isMesh||o.name!=='NightAlley_Baked_Static')return;
    const g=o.geometry,indices=g.index,positions=g.attributes.position;if(!indices)return;const keep=[],p=new THREE.Vector3(),a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
    for(let i=0;i<indices.count;i+=3){
      const ids=[indices.getX(i),indices.getX(i+1),indices.getX(i+2)];a.fromBufferAttribute(positions,ids[0]);b.fromBufferAttribute(positions,ids[1]);c.fromBufferAttribute(positions,ids[2]);p.copy(a).add(b).add(c).multiplyScalar(1/3).applyMatrix4(o.matrixWorld);
      const benchEnd=p.x>-3.36&&p.x<-3.1&&p.z<-1.27&&p.y>.43;
      const flowers=!benchEnd&&p.x>-4.35&&p.x<-3.12&&p.z>-1.99&&p.z<-.72&&p.y>.025&&p.y<1.1;
      const finial=Math.abs(p.x+2.56)<.043&&Math.abs(p.z+2.05)<.043&&((p.y>3.405&&p.y<3.575)||(p.y>2.705&&p.y<2.835));
      if(!flowers&&!finial)keep.push(...ids);
    }
    g.setIndex(keep);g.computeBoundingSphere();
  });
}

function replaceOldBoothBacks(model){
  model.traverse(o=>{
    if(!o.isMesh||o.name!=='Diner_Baked_Static')return;
    const g=o.geometry,ix=g.index,attr=g.attributes.position;if(!ix)return;const keep=[],p=new THREE.Vector3(),a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
    for(let i=0;i<ix.count;i+=3){const ids=[ix.getX(i),ix.getX(i+1),ix.getX(i+2)];a.fromBufferAttribute(attr,ids[0]);b.fromBufferAttribute(attr,ids[1]);c.fromBufferAttribute(attr,ids[2]);p.copy(a).add(b).add(c).multiplyScalar(1/3).applyMatrix4(o.matrixWorld);const x=Math.abs(p.x),back=p.y>.94&&x>2.28&&x<2.85&&p.z>-1.60&&p.z<1.30,arm=p.y>.94&&x>1.17&&x<2.75&&(Math.abs(p.z-.97)<.16||Math.abs(p.z+1.37)<.16);if(!back&&!arm)keep.push(...ids);}
    g.setIndex(keep);g.computeBoundingSphere();
  });
}
