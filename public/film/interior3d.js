import { replacePerformers } from './performers.js?v=20261013-monologue';
import * as THREE from 'three';
import { loadGLTF,loadJSON } from './asset-loader.js?v=20261013-monologue';
import { Scene3D } from './scene3d.js?v=20261014-previs-v2';
import { loadStudioRig,updateStudioCamera,renderStudio } from './studio-controls.js?v=20261014-previs-v2';
import { updateLens } from './camera-kit.js?v=20261014-previs-v2';
import { shotFrame } from './production-config.js?v=20261014-previs-v2';

export class Interior3D extends Scene3D {
  async load(){
    this.kind='interior';this.daySky.set('#282521');this.nightSky.set('#151410');this.scene.background.copy(this.daySky);this.scene.fog.near=35;this.scene.fog.far=75;
    this.hemi=this.scene.children.find(o=>o.isHemisphereLight);this.hemi.color.set('#ded5bf');this.hemi.groundColor.set('#463129');this.sun.color.set('#ffe2ac');this.sun.position.set(-3,7,7);
    this.practicals.forEach(l=>this.scene.remove(l));this.practicals=[];this.glows=[];this.atlasLight={value:1};
    try{
      const result=await loadGLTF('assets/interior-room.glb?v=20261013-monologue');this.model=result.scene;this.scene.add(this.model);this.model.updateMatrixWorld(true);await replacePerformers(this,'InteriorPair');
      this.model.traverse(o=>{
        if(o.name.startsWith('Anchor_'))this.anchors[o.userData.category||o.name.slice(7)]=o.getWorldPosition(new THREE.Vector3());
        if(!o.isMesh)return;
        if(o.name==='Interior_Baked_Static'){
          const material=new THREE.MeshBasicMaterial({map:o.material.map});
          material.onBeforeCompile=shader=>{shader.uniforms.uRoomLight=this.atlasLight;shader.fragmentShader='uniform float uRoomLight;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\ndiffuseColor.rgb *= uRoomLight;');};o.material=material;
        }
        if(/bulb|light_surface|flame/i.test(o.name+' '+o.material.name)){const material=o.material.clone();material.emissive=new THREE.Color('#ffcd83');material.emissiveIntensity=.08;o.material=material;this.glows.push(o);}
        if(/glass/i.test(o.material.name)){o.material=new THREE.MeshPhysicalMaterial({color:'#829c86',transparent:true,opacity:.055,roughness:.14,metalness:.08,depthWrite:false,side:THREE.DoubleSide});}
      });
      for(const position of [[-2.84,3.45,-2.01],[3.53,3.45,-2.01],[3.23,2.69,-.24]]){const light=new THREE.PointLight('#ffd19a',0,6.5,2);light.position.set(...position);this.scene.add(light);this.practicals.push(light);}
      const key=new THREE.SpotLight('#ffdec0',0,20,Math.PI/5,.7,1.4);key.position.set(-3.2,4.2,4.8);key.target.position.set(0,1.3,-1.4);this.scene.add(key,key.target);this.key=key;
      await loadStudioRig(this);this.ready=true;this.resize();this.onReady();
    }catch(error){this.onError(error);}
  }
  baseHome(){return{pos:new THREE.Vector3(0,1.85,8.1),target:new THREE.Vector3(0,1.4,-1.25)};}
  frame(id){const shot=shotFrame(this,id);return shot||this.home();}
  stopPerformance(){}
  update(now,dt,{light,mode,pointer}){
    if(!this.ready)return;this.interactive=false;const work=this.backstage?1:1-(this.cinemaAmount??1);this.scene.background.copy(this.nightSky).lerp(this.daySky,work);this.scene.fog.color.copy(this.scene.background);this.scene.fog.near=this.backstage&&this.mobile?80:35;this.scene.fog.far=this.backstage&&this.mobile?100:75;this.sun.intensity=.55+light*.4+work*(1.55-light*.4);this.hemi.intensity=.65+work*.6;this.key.intensity=light*34;this.practicals.forEach(l=>l.intensity=light*12);this.glows.forEach(o=>o.material.emissiveIntensity=.08+light*2.6);this.atlasLight.value=.56+light*.52+work*(.44-light*.52);this.renderer.toneMappingExposure=1.08+work*.04;
    if(this.recording)updateLens(this);updateStudioCamera(this,now,dt,pointer);
    renderStudio(this);
  }
}
