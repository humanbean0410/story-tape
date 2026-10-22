// The sets are deliberately unoccupied. This also strips actors from older cached assets.
export async function replacePerformers(engine){
  const removed=[];
  engine.model.traverse(o=>{if(/^(Actor|InteriorPair|DinerPair|AlleyPair|MinimalPerformer)/i.test(o.name))removed.push(o);});
  removed.forEach(o=>o.removeFromParent());
  engine.model.updateMatrixWorld(true);
}
