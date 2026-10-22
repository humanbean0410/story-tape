import * as THREE from './vendor/three.module.js';
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
export function routePoint(points,t){const n=points.length-1,k=Math.max(0,Math.min(1,t))*n,i=Math.min(n-1,Math.floor(k));return points[i].clone().lerp(points[i+1],ease(k-i));}
export function plugRoute(start,end,box){const x=Math.max(end.x+.4,box.max.x+.4),z=Math.max(start.z,box.max.z+.45),y=box.max.y+.65;return[start.clone(),new THREE.Vector3(start.x,y,z),new THREE.Vector3(x,y,z),new THREE.Vector3(x,y,end.z),new THREE.Vector3(x,end.y,end.z),end.clone()];}
export function earbudRoute(start,camera,box,side,amount){
  const k=ease(amount),distance=1.6,edge=Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*camera.aspect*distance;
  const x=side*edge*(.65+Math.max(0,k-.88)*8),listener=new THREE.Vector3(x,-.04,-distance).applyMatrix4(camera.matrixWorld),high=box.max.y+.85;
  return routePoint([start.clone(),new THREE.Vector3(start.x,high,start.z),new THREE.Vector3(box.min.x-(side<0?1.7:.7),high+(side<0?.2:.4),box.max.z+(side<0?1.35:1.85)),listener],k);
}
export function jackCablePoints(exit,box,ports,junction,direction){
  const k=THREE.MathUtils.clamp((exit.x+1.18)/4.67,0,1),blend=(a,b)=>new THREE.Vector3(...a).lerp(new THREE.Vector3(...b),k);
  return[exit.clone(),exit.clone().addScaledVector(direction,.13),exit.clone().addScaledVector(direction,.38),blend([-3.4,.13,2.9],[box.max.x+.9,.18,.45]),blend([-3.3,.13,2.45],[box.max.x+.65,.14,2.15]),blend([-2.35,.135,2.45],[.45,.19,2.80]),new THREE.Vector3(-2.38,.14,2.85),new THREE.Vector3(-2.38,.14,1.80),new THREE.Vector3(-2.04,.125,1.80),...ports.map(p=>new THREE.Vector3(...p)),junction.clone()];
}
export function earbudCablePoints(junction,anchor,direction,box,side){
  const height=Math.max(0,anchor.y-junction.y),relax=THREE.MathUtils.clamp(height/3,0,1),low=new THREE.Vector3(side<0?-2.65:-1.35,.14,2.98);
  const sag=junction.clone().lerp(anchor,.58);sag.y=Math.max(.10,sag.y-Math.min(.65,height*.32));sag.z=Math.max(box.max.z+.45,sag.z);low.lerp(sag,relax);
  return[junction.clone(),new THREE.Vector3(junction.x+(side<0?-.13:.13),.15,junction.z+.12),low,anchor.clone().addScaledVector(direction,.30),anchor.clone().addScaledVector(direction,.12),anchor.clone()];
}
// Sampled centerline is kept outside the player; the wire radius also has clearance.
export function cableGeometry(points,box,{floorY=.055,raisedSurfaces=[]}={}){
  const curve=new THREE.CatmullRomCurve3(points,false,'centripetal'),safe=box.clone().expandByScalar(.12),samples=[];
  const segments=160;
  for(let i=0;i<=segments;i++){
    const p=curve.getPoint(i/segments);p.y=Math.max(p.y,floorY);if(p.y<=safe.max.y&&p.x>=safe.min.x&&p.x<=safe.max.x&&p.z<safe.max.z)p.z=safe.max.z;
    for(const surface of raisedSurfaces)if(p.x>=surface.min.x-.04&&p.x<=surface.max.x+.04&&p.z>=surface.min.z-.04&&p.z<=surface.max.z+.04)p.y=Math.max(p.y,surface.max.y+.045);samples.push(p);
  }
  class Line extends THREE.Curve{getPoint(t,target=new THREE.Vector3()){const k=Math.min(.999999,Math.max(0,t))*segments,i=Math.floor(k);return target.copy(samples[i]).lerp(samples[i+1],k-i);}}
  return new THREE.TubeGeometry(new Line(),segments,.012,8,false);
}
