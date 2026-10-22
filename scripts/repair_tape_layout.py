"""Move the physical red earphone still-life clear of the tape and player."""
import bpy,json,struct,sys
from pathlib import Path
from mathutils import Vector
SITE=Path(__file__).resolve().parents[1];OUT=SITE.parents[1]/'outputs';ASSETS=SITE/'dist/assets'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'cassette-deck-detailed.blend'))
root=bpy.data.objects['CassetteOpening'];earphones=bpy.data.objects['Earphones']
def point(v):
 v=v.copy();v.x-=.38*max(0,min(1,(v.x+1.2)/.55));v.y=-(1.58+(-v.y+.37)*.43);return v
if root.get('earphoneLayout')!='outside-body-front-20261012':
 bpy.context.view_layer.update()
 for o in list(bpy.data.objects):
  if o.parent!=earphones:continue
  if o.type=='MESH':
   inverse=o.matrix_world.inverted()
   for v in o.data.vertices:v.co=inverse@point(o.matrix_world@v.co)
   o.data.update()
  elif o.type=='EMPTY':o.location=point(o.location)
 # Retain the same wire-to-jack connection offset after remapping the coil.
 bpy.data.objects['JackPlug'].location=point(Vector((-.84,-1.95,.091)))+Vector((.2,0,.054))
 root['earphoneLayout']='outside-body-front-20261012'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'cassette-deck-detailed.blend'))
groups={}
for o in bpy.data.objects:
 if o.type=='MESH':groups.setdefault(o.parent.name if o.parent else None,[]).append(o)
for pa,objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name=(pa or 'Opening')+'_static'
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type in {'MESH','EMPTY'}:o.select_set(True)
path=ASSETS/'cassette-deck.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_yup=True,export_cameras=False,export_lights=False,export_animations=False,export_image_format='AUTO')
sys.path.insert(0,str(Path(__file__).resolve().parent));from compact_cassette_glb import compact;compact(path)
meta=json.loads((ASSETS/'cassette-deck-info.json').read_text());jack=bpy.data.objects['JackPlug'].location
meta['jack']['start']['position']=[jack.x,jack.z,-jack.y];meta['file_size_bytes']=path.stat().st_size;meta['earphone_layout']='Both buds and looping wires lie on the front paper, clear of the cassette, envelope and player.'
(ASSETS/'cassette-deck-info.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('EARPHONE_LAYOUT_REPAIRED',meta['jack']['start']['position'],path.stat().st_size)
