import * as THREE from 'three';
import { Scene3D } from './scene3d.js?v=20261014-previs-v2';
import { loadGLTF,loadJSON } from './asset-loader.js?v=20261013-monologue';
import { loadStudioRig,updateStudioCamera,renderStudio } from './studio-controls.js?v=20261014-previs-v2';
import { updateLens } from './camera-kit.js?v=20261014-previs-v2';
import { shotFrame } from './production-config.js?v=20261014-previs-v2';

// One walkable Blender reconstruction; every angle sees the same architecture.
export class Courtyard3D extends Scene3D{
  async load(){
    this.kind='courtyard';this.studioFrame={pos:[8.6,10.5,20.8],target:[0,1.9,-2.8]};
    this.daySky.set('#282d29');this.nightSky.set('#b7bca5');
    this.hemi=this.scene.children.find(o=>o.isHemisphereLight);this.hemi.color.set('#eee8cd');this.hemi.groundColor.set('#535346');
    this.sun.color.set('#ffe8ba');this.sun.position.set(-5,8,4);
    this.practicals.forEach(l=>this.scene.remove(l));this.practicals=[];this.glows=[];
    try{
      const [result,meta]=await Promise.all([loadGLTF('assets/chinese-courtyard.glb?v=20261013-monologue'),loadJSON('assets/chinese-courtyard-info.json?v=20261013-monologue')]);
      this.meta=meta;this.model=result.scene;this.scene.add(this.model);this.model.updateMatrixWorld(true);
      this.model.traverse(o=>{
        if(meta.environmentNames?.some(name=>o.name===name))o.userData.background=true;
        if(o.name.startsWith('Anchor_'))this.anchors[o.userData.category||o.name.slice(7)]=o.getWorldPosition(new THREE.Vector3());
        if(!o.isMesh)return;o.castShadow=true;o.receiveShadow=true;
        const materials=Array.isArray(o.material)?o.material:[o.material];
        materials.forEach(m=>{if(m.map)m.map.anisotropy=Math.min(8,this.renderer.capabilities.getMaxAnisotropy());if(/lantern.*paper|PracticalGlow/i.test(m.name)){m.emissive=new THREE.Color('#ffc276');m.emissiveIntensity=.12;this.glows.push(m);}});
      });
      for(const p of meta.practicalPositions||[[3.6,3.2,-1.5],[3.6,3.2,-4.6]]){
        const lamp=new THREE.PointLight('#ffd09a',0,6,2);lamp.position.set(...(Array.isArray(p)?p:p.position));this.scene.add(lamp);this.practicals.push(lamp);
      }
      this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;
      this.sun.castShadow=true;this.sun.shadow.mapSize.set(2048,2048);Object.assign(this.sun.shadow.camera,{left:-8,right:8,top:8,bottom:-8,near:.5,far:30});this.sun.shadow.bias=-.0002;this.sun.shadow.normalBias=.025;
      this.sun.target.position.set(0,1.5,-3.5);this.scene.add(this.sun.target);
      this.key=new THREE.SpotLight('#ffd7a6',0,24,.72,.8,1.5);this.key.position.set(-3,5.5,3);this.key.target.position.set(0,1.3,-3);this.scene.add(this.key,this.key.target);
      await loadStudioRig(this);this.ready=true;this.resize();this.onReady();
    }catch(error){this.onError(error);}
  }
  baseHome(){return{pos:new THREE.Vector3(0,2.4,10.8),target:new THREE.Vector3(0,1.65,-3)};}
  frame(id){return shotFrame(this,id)||this.home();}
  stopPerformance(){}
  update(now,dt,{light,pointer}){
    if(!this.ready)return;this.interactive=false;const work=this.backstage?1:1-(this.stageReveal?.value??1);
    this.scene.background.copy(this.nightSky).lerp(this.daySky,work);this.scene.fog.color.copy(this.scene.background);this.scene.fog.near=45;this.scene.fog.far=90;
    this.sun.intensity=2.2+work*.6;this.hemi.intensity=.95+work*.35;this.key.intensity=light*13;this.practicals.forEach(l=>l.intensity=light*13);this.glows.forEach(m=>m.emissiveIntensity=.08+light*1.8);this.renderer.toneMappingExposure=1.02;
    if(this.recording)updateLens(this);updateStudioCamera(this,now,dt,pointer);renderStudio(this);
  }
}
