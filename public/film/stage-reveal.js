// Continuous optical fades: no stochastic pixels, alpha hashing or screen-door dissolve.
export function configureStageReveal(engine){
  engine.stageReveal={value:0};engine.gearReveal={value:0};engine.revealMaterials=[];engine.revealMeshes=[];
  function fadeMaterial(material,inverse,uniform){
    const m=material.clone(),old=material.onBeforeCompile;
    m.transparent=true;m.depthWrite=false;engine.revealMaterials.push({material:m,inverse,uniform});
    m.onBeforeCompile=(shader,renderer)=>{
      if(old)old.call(material,shader,renderer);
      shader.uniforms.uStageReveal=uniform;
      shader.fragmentShader='uniform float uStageReveal;\n'+shader.fragmentShader;
      shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',`diffuseColor.a *= ${inverse?'1.0-uStageReveal':'uStageReveal'};\n#include <opaque_fragment>`);
    };
    m.customProgramCacheKey=()=>`continuous-reveal-${inverse}-${material.type}`;
    return m;
  }
  function visit(node,inherited=false){
    const background=inherited||!!node.userData.background;
    if(background&&node.isMesh){node.material=Array.isArray(node.material)?node.material.map(m=>fadeMaterial(m,false,engine.stageReveal)):fadeMaterial(node.material,false,engine.stageReveal);engine.revealMeshes.push({mesh:node,inverse:false,uniform:engine.stageReveal});}
    node.children.forEach(child=>visit(child,background));
  }
  visit(engine.model);
  engine.rig.traverse(o=>{if(o.isMesh){const uniform=/Velour|Curtain/i.test(o.name)?engine.stageReveal:engine.gearReveal;o.material=Array.isArray(o.material)?o.material.map(m=>fadeMaterial(m,true,uniform)):fadeMaterial(o.material,true,uniform);engine.revealMeshes.push({mesh:o,inverse:true,uniform});}});
}
