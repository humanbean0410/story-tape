"""Update the physical printed track list without changing docking interfaces."""
import bpy, json, struct, sys
from pathlib import Path

SITE=Path(__file__).resolve().parents[1]
OUT=SITE.parents[1]/'outputs'
ASSETS=SITE/'dist/assets'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'cassette-deck-detailed.blend'))
font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Andale Mono.ttf')
for name,body,size in [
 ('Envelope date marker','A FILM IN SIX TRACKS',.086),
 ('Mixtape title','SIX TRACKS / ONE DATE',.074),
 ('Printed track index 1','03 WINDOW  04 COURTYARD',.076),
 ('Printed track index 2','05 DINNER  06 WALK HOME',.076)
]:
 old=bpy.data.objects[name]
 parent,location,rotation,scale=old.parent,old.location.copy(),old.rotation_euler.copy(),old.scale.copy()
 materials=list(old.data.materials)
 bpy.data.objects.remove(old,do_unlink=True)
 curve=bpy.data.curves.new(name,'FONT');curve.body=body;curve.font=font;curve.size=size;curve.extrude=.0008;curve.bevel_depth=.00035;curve.bevel_resolution=1;curve.space_character=1.08
 for m in materials:curve.materials.append(m)
 obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);obj.parent=parent;obj.location=location;obj.rotation_euler=rotation;obj.scale=scale
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH')
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
path=ASSETS/'cassette-deck.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_yup=True,export_cameras=False,export_lights=False,export_animations=False,export_image_format='AUTO')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compact_cassette_glb import compact
compact(path)
raw=path.read_bytes();doc=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
assert {'Cassette','ReelLeft','ReelRight','CassetteBay','DoorPivot','ButtonPlay','ButtonStop','ButtonRewind','ButtonForward','JackPlug'} <= {n.get('name') for n in doc['nodes']}
meta=json.loads((ASSETS/'cassette-deck-info.json').read_text());meta.update(track_count=6,file_size_bytes=len(raw),triangles=sum(len(p.vertices)-2 for o in bpy.data.objects if o.type=='MESH' for p in o.data.polygons))
(ASSETS/'cassette-deck-info.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('SIX_PHYSICAL_TRACKS_READY',len(raw),'bytes; all docking, hinge, reel and transport nodes preserved.')
