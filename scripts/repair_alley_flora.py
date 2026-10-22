"""Repair inward rose/soil/finial surfaces and export a compact live-lit floral layer."""
import bpy,bmesh,sys,json
from pathlib import Path
ROOT=Path('/Users/wqr/Documents/Codex/2026-10-10/gpt-site-casa-de-las-bellas');SITE=ROOT/'work/casa';ASSETS=SITE/'dist/assets';OUT=ROOT/'outputs'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'alley-detailed.blend'));flora=[];fixed=0
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 if bm.calc_volume(signed=True)<-1e-10:
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);o.data.update();fixed+=1
 bm.free()
 if o.name.startswith(('Terracotta tapered flower pot','Terracotta pot lip','Flower soil','Rose stalk','Rose pointed leaf','Layered rose petal','Rose flower heart','Lantern ornamental finial','Lantern bottom finial')):flora.append(o)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'alley-detailed.blend'))
for o in list(bpy.data.objects):
 if o not in flora:bpy.data.objects.remove(o,do_unlink=True)
for o in flora:
 for p in o.data.polygons:p.use_smooth=True
 for m in o.data.materials:
  if not m:continue
  bs=m.node_tree.nodes.get('Principled BSDF')
  if not bs:continue
  for link in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(link)
  bs.inputs['Base Color'].default_value=m.diffuse_color
  if 'petal' in m.name.lower():bs.inputs['Coat Weight'].default_value=.08;bs.inputs['Roughness'].default_value=.65
# Keep small flowers to eight material batches rather than hundreds of draw calls.
groups={}
for o in flora:groups.setdefault(o.data.materials[0].name,[]).append(o)
for name,objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name='Flora_'+name
path=ASSETS/'night-alley-flora.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_yup=True,export_extras=True,export_apply=True,export_cameras=False,export_lights=False)
sys.path.insert(0,str(SITE/'scripts'))
from compact_cassette_glb import compact
compact(path)
print('ALLEY_FLORA_REPAIRED',json.dumps({'fixed_meshes':fixed,'layer_batches':len(groups),'bytes':path.stat().st_size}),flush=True)
