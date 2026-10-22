import * as THREE from 'three';

// A 36 mm wide sensor: lens choice changes perspective projection, not a crop.
export const LENSES=[28,35,50,85];
export function updateLens(engine){
  const focal=engine.focalLength??LENSES[engine.lensIndex??1];
  const sensorHeight=engine.cinematic?36/engine.camera.aspect:(engine.mobile?36:24);
  engine.camera.fov=THREE.MathUtils.radToDeg(2*Math.atan(sensorHeight/(2*focal)));
  engine.camera.updateProjectionMatrix();
}
export function setLens(engine,index){engine.lensIndex=index;engine.focalLength=LENSES[index];updateLens(engine);}
function makeFilmPass(engine,width,height){
  const target=new THREE.WebGLRenderTarget(width,height,{minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter,depthBuffer:true});
  target.samples=engine.mobile?2:4;
  target.depthTexture=new THREE.DepthTexture(width,height,THREE.UnsignedIntType);
  const uniforms={image:{value:target.texture},depth:{value:target.depthTexture},texel:{value:new THREE.Vector2(1/width,1/height)},near:{value:engine.camera.near},far:{value:engine.camera.far},focus:{value:10},aperture:{value:1},lens:{value:50},time:{value:0}};
  const material=new THREE.ShaderMaterial({uniforms,depthTest:false,depthWrite:false,toneMapped:false,vertexShader:'varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position.xy,0.0,1.0);}',fragmentShader:`
    varying vec2 vUv;
    uniform sampler2D image,depth;
    uniform vec2 texel;
    uniform float near,far,focus,aperture,lens,time;
    float distanceAt(vec2 uv){float d=texture2D(depth,uv).x;return near*far/(far-d*(far-near));}
    void main(){
      float z=distanceAt(vUv);
      float coc=abs(z-focus)/max(z,.1)*lens*lens/(aperture*max(focus*1000.0-lens,1.0));
      float radius=clamp(coc/(36.0*texel.x)*.5,0.0,8.0);
      vec3 c=texture2D(image,vUv).rgb*2.0;
      for(int i=0;i<8;i++){
        float angle=float(i)*.785398;
        vec2 sampleUv=clamp(vUv+vec2(cos(angle),sin(angle))*texel*radius,texel,vec2(1.0)-texel);
        // Keep foreground silhouettes from bleeding into an in-focus subject.
        float sampleZ=distanceAt(sampleUv);
        float w=sampleZ<focus*.75&&z>focus?0.0:1.0;
        c+=mix(texture2D(image,vUv).rgb,texture2D(image,sampleUv).rgb,w);
      }
      c/=10.0;
      c*=vec3(1.035,1.006,.976);
      c=mix(vec3(dot(c,vec3(.2126,.7152,.0722))),c,.94);
      vec2 edge=(vUv-.5)*1.45;
      c*=1.0-.13*dot(edge,edge);

      gl_FragColor=vec4(max(c,vec3(0.0)),1.0);
      #include <colorspace_fragment>
    }`});
  const scene=new THREE.Scene();scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),material));
  return{target,uniforms,scene,camera:new THREE.OrthographicCamera(-1,1,1,-1,0,1),width,height};
}
export function renderFilm(engine){
  const renderer=engine.renderer,rect=engine.rect;
  const width=engine.canvas.width,height=engine.canvas.height;
  if(!engine.film)engine.film=makeFilmPass(engine,width,height);
  const film=engine.film;
  if(film.width!==width||film.height!==height){film.target.setSize(width,height);film.uniforms.texel.value.set(1/width,1/height);film.width=width;film.height=height;}
  film.uniforms.focus.value=engine.focusOverride??(engine.trainRun?Math.abs(new THREE.Vector3(0,1.2,3.72).applyMatrix4(engine.camera.matrixWorldInverse).z):engine.camera.position.distanceTo(engine.target));
  film.uniforms.aperture.value=engine.apertureOverride??(engine.shallowFocus?2.8:11);
  film.uniforms.lens.value=engine.focalLength??LENSES[engine.lensIndex??1];
  film.uniforms.time.value=engine.reducedMotion.matches?0:Math.floor(performance.now()/100)*.17;
  renderer.setScissorTest(false);renderer.setRenderTarget(film.target);renderer.render(engine.scene,engine.camera);
  renderer.setRenderTarget(null);renderer.setViewport(0,0,innerWidth,innerHeight);renderer.setClearColor('#08090a',1);renderer.clear();
  renderer.setScissorTest(true);renderer.setScissor(rect[0],innerHeight-rect[1]-rect[3],rect[2],rect[3]);renderer.setViewport(rect[0],innerHeight-rect[1]-rect[3],rect[2],rect[3]);renderer.render(film.scene,film.camera);
}
