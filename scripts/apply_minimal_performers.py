"""Save fully editable versions of the three scenes with the white actor library."""
import bpy, sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]);pairs=[('interior-room','InteriorPair',['ActorMan','ActorWoman']),('vintage-diner','DinerPair',['ActorManDiner','ActorWomanDiner']),('night-alley','AlleyPair',['ActorManAlley','ActorWomanAlley'])]
for file,pair,actors in pairs:
 bpy.ops.wm.open_mainfile(filepath=str(out/(file+'.blend')))
 old=[]
 for root in list(bpy.data.objects):
  if root.name in ['ActorMan','ActorWoman']:old.extend([root]+list(root.children_recursive))
 for o in old:
  if o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
 with bpy.data.libraries.load(str(out/'minimal-performers.blend')) as (source,target):
  allowed=[pair]+actors+[name+'Body' for name in actors]+[name+'Head' for name in actors]
  target.objects=[name for name in source.objects if name in allowed]
 for o in target.objects:
  if o and o.name not in bpy.context.scene.objects:bpy.context.collection.objects.link(o)
 bpy.ops.wm.save_as_mainfile(filepath=str(out/(file+'-minimal.blend')))
 print('Saved',file+'-minimal.blend')
