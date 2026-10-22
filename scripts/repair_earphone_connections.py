"""Rebuild physically connected, separated earphone wires in the editable opening scene."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
SITE=Path(__file__).resolve().parents[1];OUT=SITE.parents[1]/'outputs';ASSETS=SITE/'dist/assets'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'cassette-deck-detailed.blend'))
root=bpy.data.objects['CassetteOpening'];earphones=bpy.data.objects['Earphones']
def gltf(p):return [p.x,p.z,-p.y]
def blender(p):return Vector((p[0],-p[2],p[1]))
if root.get('earphoneConnections')!='relaxed-curves-20261013-r5':
 for o in list(earphones.children):
  if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
 if not root.get('earphoneConnections'):
  for name in ['EarbudLeft','EarbudRight']:
   bpy.data.objects[name].location.y-=.35
  bpy.data.objects['JackPlug'].location.y-=.35
 jack=bpy.data.objects['JackPlug']
 remote=bpy.data.objects['EarphoneRemote'];remote.location=blender((-2.04,.125,2.32));remote.rotation_euler=(0,0,0)
 bpy.context.view_layer.update()
 red=bpy.data.materials['Earphones — deep red flexible vinyl']
 def samples(segments,count=40):
  points=[]
  for segment in segments:
   a,b,c,d=map(Vector,segment)
   for i in range(count):
    t=i/count;s=1-t;points.append(a*s**3+b*(3*s*s*t)+c*(3*s*t*t)+d*t**3)
  points.append(Vector(segments[-1][-1]));return points
 def tube(name,points,r):
  verts=[];faces=[];n=12
  for i,p in enumerate(points):
   tangent=(points[min(len(points)-1,i+1)]-points[max(0,i-1)]).normalized();u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u)
   for k in range(n):verts.append(tuple(blender(p+r*(math.cos(k*math.tau/n)*u+math.sin(k*math.tau/n)*v))))
  for i in range(len(points)-1):
   for k in range(n):a=i*n+k;b=i*n+(k+1)%n;faces.append((a,b,b+n,a+n))
  faces.extend([tuple(range(n-1,-1,-1)),tuple((len(points)-1)*n+k for k in range(n))])
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();mesh.materials.append(red)
  o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.parent=earphones
  for p in mesh.polygons:p.use_smooth=True
  # Reapply the PBR UVs at a small repeating scale.
  uv=mesh.uv_layers.new(name='UVMap')
  for polygon in mesh.polygons:
   for index in polygon.loop_indices:
    vi=mesh.loops[index].vertex_index;uv.data[index].uv=(vi%n/n,vi//n*.09)
  return o
 exit=Vector(gltf(jack.matrix_world@Vector((-.309,0,0))))
 junction=Vector((-2.04,.16,2.76))
 main=samples([
  [exit,(-1.7,.13,3.12),(-3.10,.12,3.36),(-3.34,.12,2.65)],
  [(-3.34,.12,2.65),(-3.62,.12,2.08),(-2.93,.125,1.74),(-2.49,.125,1.88)],
  [(-2.49,.125,1.88),(-2.20,.125,1.97),(-2.04,.125,1.97),(-2.04,.125,2.055)],
  [(-2.04,.125,2.055),(-2.04,.125,2.22),(-2.04,.125,2.44),(-2.04,.125,2.585)],
  [(-2.04,.125,2.585),(-2.04,.135,2.65),(-2.04,.15,2.70),junction],
 ])
 tube('EarphoneCable',main,.012)
 paths=[main]
 for i,name in enumerate(['EarbudLeft','EarbudRight']):
  bud=bpy.data.objects[name];anchor=Vector(gltf(bud.matrix_world@Vector((0,-.218,.012))));tail=Vector(gltf(bud.matrix_world@Vector((0,-.43,.012))))
  control=(-2.92,.185,2.72) if i==0 else (-1.23,.185,2.85)
  path=samples([[junction,control,tail,anchor]])
  tube(name+' cord',path,.012);paths.append(path)
 root['earphoneWirePaths']=json.dumps([[list(p) for p in path] for path in paths]);root['earphoneConnections']='relaxed-curves-20261013-r5'
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
meta=json.loads((ASSETS/'cassette-deck-info.json').read_text())
meta['jack']['start']['position']=gltf(bpy.data.objects['JackPlug'].location);meta['jack']['cable_exit_local']=[-.309,0,0]
meta['earphones'].update({'cable_exit_local':[0,.012,.218],'junction':[-2.04,.16,2.76],'remote_ports':[[-2.04,.125,2.055],[-2.04,.125,2.585]]});meta['earphones'].pop('wire_paths',None)
meta['earphone_layout']='Complete earbud meshes clear the cassette. Non-crossing wires attach at strain-relief exits; inline remote sits on the trunk.'
meta['file_size_bytes']=path.stat().st_size
(ASSETS/'cassette-deck-info.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('EARPHONE_CONNECTIONS_REPAIRED',meta['jack']['start']['position'],path.stat().st_size)
