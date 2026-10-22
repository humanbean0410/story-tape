import * as THREE from 'three';
import { loadGLTF,loadJSON } from './asset-loader.js?v=20261013-monologue';
import { bindStudioControls,loadStudioRig,setBackstage,backstageFrame,updateStudioCamera,renderStudio,captureStudio } from './studio-controls.js?v=20261014-previs-v2';
import { setLens,updateLens } from './camera-kit.js?v=20261014-previs-v2';
import { shotFrame,fitViewport } from './production-config.js?v=20261014-previs-v2';

export class Scene3D {
  constructor(canvas,{onReady,onError,onVisit,onHover,reducedMotion,sceneOnly=false,renderer=null}){
    this.canvas=canvas;this.onReady=onReady;this.onError=onError;this.onVisit=onVisit;this.onHover=onHover;this.reducedMotion=reducedMotion;
    this.sceneOnly=sceneOnly;this.kind='casa';this.backstage=false;
    this.ready=false;this.anchors={};this.hitAreas=[];this.hover=null;this.flight=null;this.light={value:0};this.xray={value:0};this.pointer=new THREE.Vector2();this.drift=new THREE.Vector2();this.ray=new THREE.Raycaster();this.projected=new THREE.Vector3();
    this.scene=new THREE.Scene();this.daySky=new THREE.Color('#b6bdb7');this.nightSky=new THREE.Color('#172a35');this.scene.background=this.daySky.clone();this.scene.fog=new THREE.Fog(this.daySky,22,55);
    this.camera=new THREE.PerspectiveCamera(35,1,.08,100);this.position=new THREE.Vector3(-6.4,4.4,9.3);this.target=new THREE.Vector3(-.25,2.55,1);
    try{this.renderer=renderer||new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'high-performance'});}catch(e){onError(e);return;}
    this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.12;
    this.scene.add(new THREE.HemisphereLight('#dce3e4','#544f3d',1.4));this.sun=new THREE.DirectionalLight('#e9e5cf',2.2);this.sun.position.set(-4,8,6);this.scene.add(this.sun);
    this.practicals=[];[[-.3,3.38,2],[2.1,3.38,2],[-.6,2.87,-.3],[1.5,2.87,-.3],[-3.72,2.58,-.85],[-3.72,2.58,-2.45]].forEach(p=>{const light=new THREE.PointLight('#ffad54',0,4,2);light.position.set(...p);this.scene.add(light);this.practicals.push(light);});
    bindStudioControls(this);
    this.load();
  }
  async load(){
    try{
      const result=await loadGLTF('assets/casa-storefront.glb?v=20261013-monologue');this.model=result.scene;
      const night=await new THREE.TextureLoader().loadAsync('assets/casa-night-baked.jpg');night.flipY=false;night.colorSpace=THREE.SRGBColorSpace;
      this.glazing=[];const doorGrain=this.makeWood();
      this.model.traverse(o=>{
        if(o.name.startsWith('Anchor_')){this.anchors[o.userData.category||o.name.slice(7)]=o.getWorldPosition(new THREE.Vector3());}
        if(o.name==='DoorPivot')this.door=o;
        if(!o.isMesh)return;
        o.frustumCulled=true;
        if(o.name==='Storefront_Baked_Static'){
          const old=o.material;const m=new THREE.MeshBasicMaterial({map:old.map});m.toneMapped=true;
          m.onBeforeCompile=shader=>{shader.uniforms.uNight={value:night};shader.uniforms.uLight=this.light;shader.uniforms.uXray=this.xray;shader.fragmentShader='uniform sampler2D uNight; uniform float uLight; uniform float uXray;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`vec4 sampledDiffuseColor=mix(texture2D(map,vMapUv),texture2D(uNight,vMapUv),uLight); diffuseColor*=sampledDiffuseColor;`).replace('#include <color_fragment>',`#include <color_fragment>\ndiffuseColor.rgb=mix(diffuseColor.rgb,vec3(.17,.27,.20),uXray*.55);`);};
          o.material=m;this.staticMesh=o;
        }else if(/glass/i.test(o.name)&&!/lamp_glass|Lantern_glass/i.test(o.name)){
          const fascia=/Fascia/i.test(o.name);o.material=new THREE.MeshPhysicalMaterial({color:fascia?'#5b6d61':'#293a31',roughness:fascia?.12:.075,metalness:fascia?.3:.05,transparent:true,opacity:fascia?.24:.53,ior:1.5,clearcoat:1,clearcoatRoughness:.09,envMapIntensity:fascia?1.05:.8,side:THREE.DoubleSide,depthWrite:false});this.glazing.push(o);
        }else if(/bulb|lamp_glass|Lantern_glass/i.test(o.name)){
          o.material=new THREE.MeshStandardMaterial({color:'#ffe0a0',emissive:'#ffa442',emissiveIntensity:.4,roughness:.2});this.glows??=[];this.glows.push(o);
        }else if(/^Door/i.test(o.name)){
          const metal=/handle/i.test(o.name);o.material=new THREE.MeshStandardMaterial({color:metal?'#ba8843':'#584034',map:metal?null:doorGrain,roughness:metal?.32:.72,metalness:metal?.6:0});
        }
      });
      this.scene.add(this.model);this.model.updateMatrixWorld(true);
      // Empties retain their Blender metadata through glTF's extras.
      this.model.traverse(o=>{if(o.name.startsWith('Anchor_'))this.anchors[o.userData.category||o.name.slice(7)]=o.getWorldPosition(new THREE.Vector3());});
      this.captureReflections();
      const boxes={prologue:[6.7,.85,.22],'ai-product':[2.30,2.3,.12],film:[2.30,2.3,.12],editorial:[1.05,1.25,.14],research:[2.05,.70,.55],about:[.16,2.68,1.20]};
      Object.entries(boxes).forEach(([id,size])=>{const box=new THREE.Mesh(new THREE.BoxGeometry(...size),new THREE.MeshBasicMaterial({visible:false}));box.position.copy(this.anchors[id]);box.userData.category=id;this.scene.add(box);this.hitAreas.push(box);});
      this.wire=new THREE.LineSegments(new THREE.WireframeGeometry(this.staticMesh.geometry),new THREE.LineBasicMaterial({color:'#c4cfb0',transparent:true,opacity:0}));this.wire.position.copy(this.staticMesh.position);this.wire.quaternion.copy(this.staticMesh.quaternion);this.scene.add(this.wire);
      this.particles=this.makeDust();this.scene.add(this.particles);
      await loadStudioRig(this);this.ready=true;this.resize();this.onReady();
    }catch(e){this.onError(e);}
  }
  makeWood(){const c=document.createElement('canvas');c.width=256;c.height=1024;const ctx=c.getContext('2d');ctx.fillStyle='#c0a488';ctx.fillRect(0,0,256,1024);let seed=27;const random=()=>{seed=(seed*16807)%2147483647;return(seed-1)/2147483646;};for(let i=0;i<1700;i++){const x=random()*256,y=random()*1024;ctx.strokeStyle=`rgba(44,26,17,${random()*.14})`;ctx.lineWidth=random()*1.3+.3;ctx.beginPath();ctx.moveTo(x,y);ctx.bezierCurveTo(x+random()*3,y+24,x-2,y+80,x+random()*4,y+90+random()*150);ctx.stroke();}const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=4;return tex;}
  captureReflections(){
    this.glazing.forEach(o=>o.visible=false);const target=new THREE.WebGLCubeRenderTarget(128,{type:THREE.HalfFloatType});const camera=new THREE.CubeCamera(.12,55,target);camera.position.set(-.7,2.65,2.2);const pmrem=new THREE.PMREMGenerator(this.renderer);pmrem.compileCubemapShader();
    camera.update(this.renderer,this.scene);this.reflectionDay=pmrem.fromCubemap(target.texture);
    this.light.value=.82;this.scene.background.copy(this.nightSky);this.scene.fog.color.copy(this.nightSky);this.sun.intensity=.6;this.practicals.forEach(l=>l.intensity=7);
    camera.update(this.renderer,this.scene);this.reflectionNight=pmrem.fromCubemap(target.texture);
    this.light.value=0;this.scene.background.copy(this.daySky);this.scene.fog.color.copy(this.daySky);this.sun.intensity=2.2;this.practicals.forEach(l=>l.intensity=0);this.glazing.forEach(o=>{o.visible=true;o.material.envMap=this.reflectionDay.texture;});target.dispose();pmrem.dispose();
  }
  makeDust(){const geo=new THREE.BufferGeometry();const pos=[];for(let i=0;i<90;i++)pos.push(-3+Math.random()*6,.7+Math.random()*3,1.8+Math.random()*.6);geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));return new THREE.Points(geo,new THREE.PointsMaterial({color:'#ffc789',size:.012,transparent:true,opacity:0,depthWrite:false}));}
  resize({preserveView=false}={}){
    fitViewport(this);if(this.cinematic)updateLens(this);else{this.camera.fov=this.mobile?43:35;this.camera.updateProjectionMatrix();}
    if(!preserveView){if(this.active)this.flyTo(this.active,0);else this.flyTo(null,0);}
  }
  baseHome(){return this.mobile?{pos:new THREE.Vector3(-10.0,6.2,16.5),target:new THREE.Vector3(-.40,2.9,.9)}:this.sceneOnly?{pos:new THREE.Vector3(-6.0,4.15,9.7),target:new THREE.Vector3(-.18,2.40,1.0)}:{pos:new THREE.Vector3(-6.4,4.4,9.3),target:new THREE.Vector3(-.25,2.55,1)};}
  home(){if(this.backstage)return backstageFrame(this);const frame=this.baseHome();if(this.recording){frame.pos.lerp(frame.target,this.mobile?.035:.045);}return frame;}
  setShooting(value){if(this.backstage)setBackstage(this,false);this.recording=value;this.flyTo(null,1600);}
  setBackstage(value){setBackstage(this,value);}
  setLens(index){setLens(this,index);}
  capture(){return captureStudio(this);}
  frame(id){
    const shot=shotFrame(this,id);if(shot)return shot;
    if(!id||!this.anchors[id])return this.home();
    const anchor=this.anchors[id].clone();const deltas={prologue:[-1,.3,3.5],'ai-product':[-.45,.25,3.3],film:[-.4,.25,3.3],editorial:[-.45,.20,2.15],research:[-.65,1.1,3.0],about:[-3.2,.55,1.0]};
    if(this.sceneOnly){deltas.prologue=[-1,.15,this.mobile?9.0:6.1];deltas['ai-product']=[-.65,.15,4.2];deltas.film=[-.55,.15,4.2];deltas.about=[-4.2,.55,1.0];if(id==='ai-product'||id==='film')anchor.y+=.35;}
    const delta=new THREE.Vector3(...deltas[id]);const pos=anchor.clone().add(delta),target=anchor.clone();
    if(this.sceneOnly)return{pos,target};
    const direction=target.clone().sub(pos).normalize();const right=direction.clone().cross(new THREE.Vector3(0,1,0)).normalize();const distance=pos.distanceTo(target);
    if(!this.mobile){const desired=(innerWidth*.28-this.rect[0])/this.rect[2];const offset=(.5-desired)*2*distance*Math.tan(THREE.MathUtils.degToRad(this.camera.fov/2))*this.camera.aspect;pos.addScaledVector(right,offset);target.addScaledVector(right,offset);}
    else{const offset=.38*2*distance*Math.tan(THREE.MathUtils.degToRad(this.camera.fov/2));pos.y-=offset;target.y-=offset;}
    return{pos,target};
  }
  flyTo(id,duration=1350){this.active=id;this.flyFrame(this.frame(id),duration);}
  flyFrame(f,duration=1350,via=null){this.orbit=null;if(this.reducedMotion.matches||!duration){this.position.copy(f.pos);this.target.copy(f.target);this.flight=null;return;}this.flight={start:performance.now(),duration,fromPos:this.position.clone(),fromTarget:this.target.clone(),pos:f.pos.clone(),target:f.target.clone(),via:via?.clone()};}
  project(id){if(!this.anchors[id])return[-999,-999];this.projected.copy(this.anchors[id]).project(this.camera);return[this.rect[0]+(this.projected.x*.5+.5)*this.rect[2],this.rect[1]+(-this.projected.y*.5+.5)*this.rect[3]];}
  pick(e){if(!this.enabled||!this.ready||!this.interactive)return null;const r=this.rect;this.pointer.set((e.clientX-r[0])/r[2]*2-1,-((e.clientY-r[1])/r[3]*2-1));this.ray.setFromCamera(this.pointer,this.camera);const hit=this.ray.intersectObjects(this.hitAreas,false)[0];const id=hit?.object.userData.category||null;if(id!==this.hover){this.hover=id;this.canvas.style.cursor=id?'pointer':'default';this.onHover(id);}return id;}
  update(now,dt,{light,mode,pointer,depthView,depthAmount}){
    if(!this.ready)return;this.interactive=false;this.light.value=light*.82;this.xray.value=depthView;this.renderer.toneMappingExposure=1.12+light*.12;
    this.scene.background.copy(this.daySky).lerp(this.nightSky,light);if(this.backstage)this.scene.background.set('#17191a');else if(this.stageReveal)this.scene.background.lerp(new THREE.Color('#17191a'),1-this.stageReveal.value);this.scene.fog.color.copy(this.scene.background);this.scene.fog.near=this.backstage?(this.mobile?80:42):22;this.scene.fog.far=this.backstage?(this.mobile?100:80):55;this.glazing.forEach(o=>{const env=light>.5?this.reflectionNight.texture:this.reflectionDay.texture;if(o.material.envMap!==env){o.material.envMap=env;o.material.needsUpdate=true;}});
    const responsive=1-Math.exp(-dt*4);if(this.recording)updateLens(this);updateStudioCamera(this,now,dt,pointer,depthAmount);
    this.sun.intensity=this.backstage?3.4:2.2-light*1.6;this.practicals.forEach(l=>l.intensity=light*7);(this.glows||[]).forEach(o=>o.material.emissiveIntensity=.12+light*2.5);
    if(this.door){const open=mode==='room'&&this.active==='about'?-.9:0;this.door.rotation.y=THREE.MathUtils.lerp(this.door.rotation.y,open,responsive);}
    this.wire.visible=depthView>.005;this.wire.material.opacity=depthView*.18;this.particles.material.opacity=light*.33;if(!this.reducedMotion.matches)this.particles.position.y=Math.sin(now*.0002)*.06;
    renderStudio(this);
  }
}
