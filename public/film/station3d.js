import * as THREE from 'three';
import { loadGLTF,loadJSON } from './asset-loader.js?v=20261013-monologue';
import { Scene3D } from './scene3d.js?v=20261014-previs-v2';
import { loadStudioRig,updateStudioCamera,renderStudio } from './studio-controls.js?v=20261014-previs-v2';
import { updateLens } from './camera-kit.js?v=20261014-previs-v2';
import { shotFrame } from './production-config.js?v=20261014-previs-v2';

export class Station3D extends Scene3D {
  async load(){
    this.kind='station';this.daySky.set('#aabec5');this.nightSky.set('#19262f');this.scene.background.copy(this.daySky);this.scene.fog.near=22;this.scene.fog.far=80;this.wind=0;this.windTarget=0;this.trainRun=null;this.seatViews=[];this.surfaces=[];
    this.hemi=this.scene.children.find(o=>o.isHemisphereLight);this.hemi.intensity=1.15;this.sun.color.set('#fff0d0');this.sun.position.set(-6,9,8);
    this.practicals.forEach(l=>this.scene.remove(l));this.practicals=[];
    for(const p of [[-3.1,3.42,.26],[2.6,3.42,.26]]){const light=new THREE.PointLight('#ffc77f',0,8,2);light.position.set(...p);this.scene.add(light);this.practicals.push(light);}
    try{
      const result=await loadGLTF('assets/hasedera-station.glb?v=20261013-monologue');this.model=result.scene;this.scene.add(this.model);this.model.updateMatrixWorld(true);
      this.gates=['GatePivot_Entry','GatePivot_Exit'].map(name=>this.model.getObjectByName(name)).filter(Boolean);this.gates.forEach((g,i)=>g.rotation.z=(i===0?1:-1)*Math.PI/2);this.gateClose=0;
      this.model.traverse(o=>{
        if(o.name.startsWith('Anchor_'))this.anchors[o.userData.category||o.name.slice(7)]=o.getWorldPosition(new THREE.Vector3());
        if(o.name==='AnimatedTrain'){this.legacyTrain=o;o.visible=false;}
        if(o.name==='BlossomCanopy'){this.blossom=o;this.blossomRotation=o.rotation.clone();}
        if(!o.isMesh)return;
        if(o.name==='Station_Baked_Static'){const old=o.material;o.material=new THREE.MeshStandardMaterial({map:old.map,color:'#dedbcd',roughness:.88});this.staticMesh=o;this.surfaces.push(o.material);}
        if(/^Seat_\d+/.test(o.name)){const index=Number(o.name.match(/^Seat_(\d+)/)[1])-1;const center=new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());center.y=.92;this.seatViews[index]=center;const material=o.material.clone();material.roughness=.3;material.metalness=.04;o.material=material;}
        if(/StationTubeLamp/.test(o.name)){o.material=new THREE.MeshStandardMaterial({color:'#fff8e1',emissive:'#ffda99',emissiveIntensity:.35});this.glows??=[];this.glows.push(o);}
        if(/NoticeBoardGlass/i.test(o.name)){o.material=new THREE.MeshPhysicalMaterial({color:'#7c8e85',roughness:.14,metalness:.12,transparent:true,opacity:.2,clearcoat:1,side:THREE.DoubleSide,depthWrite:false});}
      });
      // Anchor coordinates come from authored Blender empty nodes, not screen-space approximations.
      const boxes={board:[1.3,1.35,.24],sign:[2.35,.74,.24],blossom:[4.3,3.2,2.6],roof:[8.8,.8,2.4]};
      Object.entries(boxes).forEach(([id,size])=>this.addHit(id,this.anchors[id],size));
      this.seatViews.forEach((position,index)=>{const id=`seat-${index+1}`;this.anchors[id]=position;this.addHit(id,position,[.72,1.05,.85]);});
      const trainResult=await loadGLTF('assets/passenger-train.glb');this.train=trainResult.scene;this.train.position.set(0,0,3.72);this.train.visible=false;this.scene.add(this.train);this.trainLength=new THREE.Box3().setFromObject(this.train).getSize(new THREE.Vector3()).x;
      this.makePetals();await loadStudioRig(this);this.ready=true;this.resize();this.onReady();
    }catch(error){this.onError(error);}
  }
  addHit(id,position,size){if(!position)return;const mesh=new THREE.Mesh(new THREE.BoxGeometry(...size),new THREE.MeshBasicMaterial({visible:false}));mesh.position.copy(position);mesh.userData.category=id;this.scene.add(mesh);this.hitAreas.push(mesh);}
  baseHome(){return this.mobile?{pos:new THREE.Vector3(-1.4,2.25,9.2),target:new THREE.Vector3(-.4,1.85,-1.3)}:{pos:new THREE.Vector3(-.4,2.15,10.7),target:new THREE.Vector3(-.4,1.85,-1.2)};}
  frame(id){
    const shot=shotFrame(this,id);if(shot)return shot;
    if(!id||!this.anchors[id]||id==='platform')return this.home();
    const anchor=this.anchors[id].clone();let pos,target=anchor;
    if(id.startsWith('seat-')){
      const index=Number(id.slice(5))-1;
      // Each chair selects an authored camera setup: diagonal, low, eye-level or high.
      const setups=[[-5.4,1.7,4.8],[anchor.x,1.0,5.1],[-2.5,2.15,6.5],[anchor.x,1.45,5.7],[2.7,1.7,5.2],[3.7,3.65,5.5],[5.3,1.75,3.6]];
      pos=new THREE.Vector3(...setups[index]);target=new THREE.Vector3(anchor.x,1.25,-.9);
    }
    else if(id==='blossom'){pos=anchor.clone().add(new THREE.Vector3(-3.0,-.30,9.4));target.y-=.3;}
    else if(id==='roof'){pos=anchor.clone().add(new THREE.Vector3(1.0,-.65,6.5));target.y-=.18;}
    else{pos=anchor.clone().add(new THREE.Vector3(-.3,.05,this.mobile?6.5:4.6));}
    return{pos,target};
  }
  startTrain(){if(!this.train)return;this.trainRun={start:performance.now(),duration:10000};this.train.visible=true;this.train.position.x=-this.trainLength*.5-14;}
  stopPerformance(){this.trainRun=null;if(this.train)this.train.visible=false;this.windTarget=0;this.gateClose=0;this.trainQueued=false;}
  prepareTrain(){this.gateClose=1;}
  toggleWind(){this.windTarget=this.windTarget>.5?0:1;}
  makePetals(){let seed=72;const random=()=>{seed=seed*16807%2147483647;return(seed-1)/2147483646;};const positions=[];this.petalSeeds=[];for(let i=0;i<120;i++){const x=-2+random()*9,y=.6+random()*5.7,z=-9+random()*6.5;positions.push(x,y,z);this.petalSeeds.push({x,y,z,speed:.18+random()*.35,phase:random()*Math.PI*2});}const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));this.petals=new THREE.Points(geometry,new THREE.PointsMaterial({color:'#ffe5df',size:.045,transparent:true,opacity:0,depthWrite:false}));this.scene.add(this.petals);}
  resize(options={}){super.resize(options);if(!this.cinematic){this.camera.fov=this.mobile?44:36;this.camera.updateProjectionMatrix();}}
  update(now,dt,{light,mode,pointer,depthAmount=1}){
    if(!this.ready)return;this.interactive=false;this.scene.background.copy(this.daySky).lerp(this.nightSky,light);if(this.backstage)this.scene.background.set('#151719');else if(this.stageReveal)this.scene.background.lerp(new THREE.Color('#151719'),1-this.stageReveal.value);this.scene.fog.color.copy(this.scene.background);this.scene.fog.near=this.backstage?(this.mobile?80:42):22;this.scene.fog.far=this.backstage?90:80;
    this.renderer.toneMappingExposure=this.backstage?1.1:1.02;this.sun.intensity=this.backstage?2.8:2.6-light*2.2;this.hemi.intensity=this.backstage?1.45:1.05-light*.6;this.practicals.forEach(l=>l.intensity=light*18);(this.glows||[]).forEach(o=>o.material.emissiveIntensity=.15+light*2.2);
    if(this.recording)updateLens(this);updateStudioCamera(this,now,dt,pointer,depthAmount);
    this.wind+=(this.windTarget-this.wind)*(1-Math.exp(-dt*2));this.petals.material.opacity=this.wind*.75;
    if(!this.reducedMotion.matches){const time=now*.001;const attr=this.petals.geometry.attributes.position;this.petalSeeds.forEach((p,i)=>{attr.setXYZ(i,p.x+Math.sin(time*.65+p.phase)*.25+this.wind*Math.sin(time*.27+p.phase)*.95,(p.y-time*p.speed*this.wind+90)%6.3,p.z+Math.sin(time*.45+p.phase)*.2);});attr.needsUpdate=true;if(this.blossom){this.blossom.rotation.z=this.blossomRotation.z+Math.sin(time*.55)*.018*this.wind;this.blossom.rotation.x=this.blossomRotation.x+Math.sin(time*.8)*.007*this.wind;}}
    if(this.trainRun){const t=Math.min(1,(now-this.trainRun.start)/this.trainRun.duration);this.train.position.x=-this.trainLength*.5-14+t*(this.trainLength+28);if(t===1){this.train.visible=false;this.trainRun=null;}}
    if(this.gates){if(this.trainRun)this.gateClose=1;else if(this.gateClose===1&&this.train?.visible===false&&!this.trainQueued)this.gateClose=0;this.gates.forEach((g,i)=>g.rotation.z=THREE.MathUtils.lerp(g.rotation.z,(i===0?1:-1)*(1-this.gateClose)*Math.PI/2,1-Math.exp(-dt*2.2)));}
    renderStudio(this);
  }
}
