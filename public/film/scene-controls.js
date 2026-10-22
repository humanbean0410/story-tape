import * as THREE from 'three';
import { SETS,shotFrame } from './production-config.js?v=20261013-monologue';
// Each scene has fixed physical camera setups. The small labels appear only nearby.
export class SceneControls{
  constructor({select,action,book,locked}){Object.assign(this,{select,action,book,locked});this.root=document.getElementById('world-controls');this.hint=document.getElementById('scene-hint');this.pointer={x:-999,y:-999};this.focused=null;addEventListener('pointermove',e=>this.pointer={x:e.clientX,y:e.clientY});addEventListener('pointerout',e=>{if(!e.relatedTarget)this.pointer={x:-999,y:-999};});}
  clear(){this.pointer={x:-999,y:-999};this.focused=null;this.hint.hidden=true;}
  attach(engine){
    this.clear();
    this.engine=engine;this.root.replaceChildren();this.points=[];
    if(!engine.cameraSet){engine.cameraSet=new THREE.Group();engine.cameraSet.name='AuthoredCameraSet';engine.rig.add(engine.cameraSet);SETS[engine.kind].shots.forEach((shot,i)=>{const frame=shotFrame(engine,`shot:${shot.id}`);engine.cameraSet.add(makeCamera(frame,i));});}
    SETS[engine.kind].shots.forEach((shot,i)=>this.add(`shot:${shot.id}`,shot.name,`${shot.size} · ${shot.angle} · ${shot.focal} mm`,()=>this.select(shot.id),()=>this.ready?shotFrame(engine,`shot:${shot.id}`).pos.clone():this.subjectPoint(shot,i),'camera'));
    this.add('action','开拍','缓慢推进，灯光就位',this.action,()=>new THREE.Vector3(5,.76,5.2),'action');
    this.add('book','借你一段路 · 独白本','六幕独白与配乐候选',this.book,()=>new THREE.Vector3(5,.44,5.65),'book');
    if(!engine.paper){const paper=new THREE.Mesh(new THREE.BoxGeometry(.5,.012,.32),new THREE.MeshStandardMaterial({color:'#c9c1a5',roughness:.95}));paper.position.set(5,.39,5.65);paper.rotation.y=.12;engine.rig.add(paper);engine.paper=paper;}
  }
  subjectPoint(shot,i){
    const cues={
      interior:{master:[-3.4,2.1,-2], 'two-shot':[2.55,1,-1.3],man:[-.63,1.13,-1.995],woman:[.68,1.13,-1.995],detail:[-.12,.99,-1.27],window:[2.15,2.6,-1.99]},
      diner:{master:[-2.1,.95,-.2],'two-shot':[.05,1.25,-.6],man:[-.72,1.2,-.3],woman:[.72,1.2,-.3],table:[.62,1.12,.55],jukebox:[0,2.05,-2.1]},
      alley:{master:[-2.8,2.4,-2.7],'two-shot':[-2.2,1.35,-1.7],close:[-1.9,.75,-1.5],profile:[-.85,.85,-1.3],flowers:[-3.74,.48,-1.67],street:[2.9,3.4,-5.4]},
      station:{master:[-6.4,2.7,.05],seats:[-3.5,1.1,-.3],low:[-.5,.48,2.2],passing:[5.1,2.7,-.2],blossom:[2.5,3.25,-5.5],high:[0,3.8,-.3],axis:[4.8,1.6,-.9],reverse:[-5.2,1.6,-.9],crossing:[8.3,1.2,2.1],'seat-detail':[1.2,1.1,-.3]},
      courtyard:{master:[-3.8,2.7,-5.5],path:[0,.24,-2.7],corridor:[3.3,1.8,-2.4],pine:[-1.4,2.6,-3.6],door:[-.45,1.6,-6.3],lantern:[3.91,2.98,.24],window:[5.19,1.8,.1]}
    };const pos=cues[this.engine.kind]?.[shot.id];return pos?new THREE.Vector3(...pos):shotFrame(this.engine,`shot:${shot.id}`).target.clone();
  }
  add(id,label,spec,click,position,kind){const b=document.createElement('button');b.className='world-point';b.dataset.kind=kind;b.setAttribute('aria-label',`${label}，${spec}`);b.addEventListener('click',()=>{if(!this.locked())click();});b.addEventListener('focus',()=>this.focused=b.matches(':focus-visible')?id:null);b.addEventListener('blur',()=>this.focused=null);this.root.append(b);this.points.push({id,label,spec,b,position,kind});}
  update({phase,selected,hidden}){
    if(!this.engine?.ready)return;this.ready=phase==='ready';let nearest=null,best=110;
    for(const p of this.points){
      const v=p.position().project(this.engine.camera),r=this.engine.rect,x=r[0]+(v.x*.5+.5)*r[2],y=r[1]+(-v.y*.5+.5)*r[3],hide=hidden||!['ready','recording'].includes(phase)||(!this.ready&&p.kind!=='camera')||v.z>1||v.z<-1||x<r[0]+12||x>r[0]+r[2]-12||y<r[1]+12||y>r[1]+r[3]-12;
      p.b.hidden=hide;if(hide)continue;p.b.style.left=`${x}px`;p.b.style.top=`${y}px`;p.b.disabled=this.locked();p.b.setAttribute('aria-current',String(p.id===`shot:${selected}`));p.x=x;p.y=y;const d=Math.hypot(this.pointer.x-x,this.pointer.y-y);p.b.classList.toggle('near',d<80||this.focused===p.id);if(this.focused===p.id){nearest=p;best=-1;}else if(d<best){nearest=p;best=d;}
    }
    this.hint.hidden=!nearest;if(nearest){this.hint.textContent=`${nearest.label}\n${nearest.spec}`;this.hint.style.left=`${Math.min(innerWidth-215,Math.max(14,nearest.x+18))}px`;this.hint.style.top=`${Math.max(16,nearest.y-46)}px`;}
  }
}
function makeCamera(frame,index){
  const root=new THREE.Group(),metal=new THREE.MeshStandardMaterial({color:'#343936',roughness:.42,metalness:.65}),rubber=new THREE.MeshStandardMaterial({color:'#151a19',roughness:.6}),glass=new THREE.MeshStandardMaterial({color:'#437572',metalness:.75,roughness:.15});root.name=`CameraPosition_${index+1}`;
  const h=frame.pos.y,base=frame.pos.clone();base.y=.1;
  const rod=(a,b,r)=>{const d=b.clone().sub(a),m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,d.length(),8),metal);m.position.copy(a).add(b).multiplyScalar(.5);m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());root.add(m);};
  for(let i=0;i<3;i++){const a=base.clone().add(new THREE.Vector3(Math.cos(i*2.094)*.37,0,Math.sin(i*2.094)*.37)),b=frame.pos.clone();b.y-=.2;rod(a,b,.016);}rod(base,frame.pos.clone().add(new THREE.Vector3(0,-.15,0)),.028);
  const body=new THREE.Group();body.position.copy(frame.pos);body.lookAt(frame.target);const cube=(size,pos,mat)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(...size),mat);m.position.set(...pos);body.add(m);};cube([.26,.22,.37],[0,0,0],rubber);cube([.04,.06,.26],[0,.17,-.02],metal);cube([.14,.13,.08],[0,0,-.22],rubber);const lens=new THREE.Mesh(new THREE.CylinderGeometry(.085,.085,.19,24),metal);lens.rotation.x=Math.PI/2;lens.position.z=.25;body.add(lens);const face=new THREE.Mesh(new THREE.CircleGeometry(.068,24),glass);face.position.z=.35;body.add(face);root.add(body);return root;
}
