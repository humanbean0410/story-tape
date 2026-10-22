"""Replace over-beveled dark booth backs with properly rounded, stitched upholstered geometry."""
import bpy,bmesh,math,sys,json
from pathlib import Path
ROOT=Path('/Users/wqr/Documents/Codex/2026-10-10/gpt-site-casa-de-las-bellas');SITE=ROOT/'work/casa';ASSETS=SITE/'dist/assets';OUT=ROOT/'outputs'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'vintage-diner-detailed.blend'));new=[]
for o in list(bpy.data.objects):
 if o.name.startswith(('Booth soft padded back','Booth rolled arm rest','Booth chrome back piping','Booth tuft button','Diner back panel double stitch')):bpy.data.objects.remove(o,do_unlink=True)
def material(n,c,r=.6,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=next((v for v in m.node_tree.nodes if v.type=='BSDF_PRINCIPLED'),None)
 if p is None:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=r;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=.08;return m
vinyl=material('Booth repaired forest green vinyl',(.062,.145,.09),.47);thread=material('Booth repaired linen seam',(.23,.29,.17),.86);dark=material('Booth repaired deeper sidewall',(.032,.078,.043),.6);chrome=material('Booth repaired brushed chrome',(.40,.44,.42),.25,.65)
def cube(n,p,d,m,b=.03):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:v.co.x*=d[0];v.co.y*=d[1];v.co.z*=d[2]
 bmesh.ops.bevel(bm,geom=list(bm.edges),offset=b,segments=5,affect='EDGES',clamp_overlap=True);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));me=bpy.data.meshes.new(n);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.location=p;o.data.materials.append(m);new.append(o);return o
def rod(n,a,b,r,m):
 from mathutils import Vector
 a=Vector(a);b=Vector(b);t=(b-a).normalized();u=t.cross(Vector((0,0,1)))
 if u.length<.001:u=t.cross(Vector((0,1,0)))
 u.normalize();v=t.cross(u);N=8;vs=[tuple(p+r*(math.cos(i*math.tau/N)*u+math.sin(i*math.tau/N)*v)) for p in [a,b] for i in range(N)]
 fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.data.materials.append(m);new.append(o);return o
for s in [-1,1]:
 cube('Repaired booth continuous back shell',(s*2.72,.1,1.22),(.10,2.45,1.4),dark,.025)
 for yy in [-.95,-.45,.05,.55,1.05]:
  cube('Repaired booth softly rounded channel',(s*2.575,yy,1.24),(.27,.475,1.32),vinyl,.045)
  for dy in [-.203,.203]:
   for j in range(27):
    z=.64+j*.044;rod('Repaired booth saddle stitch',(s*2.432,yy+dy,z),(s*2.432,yy+dy,z+.014),.0013,thread)
 # Gentle solid side padding, rather than free-floating tubular arms.
 for yy in [-1.05,1.42]:
  profile=[(s*1.245,.655),(s*2.70,.655),(s*2.70,1.42),(s*2.48,1.36),(s*1.245,.985)];N=len(profile);vs=[(x,yy+d,z) for d in [-.085,.085] for x,z in profile];fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
  me=bpy.data.meshes.new('Booth padded side');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Repaired booth curved solid arm',me);bpy.context.collection.objects.link(o);o.data.materials.append(vinyl);mod=o.modifiers.new('Proper gentle bevel','BEVEL');mod.width=.035;mod.segments=5;bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();new.append(o)
 rod('Repaired booth upper chrome lip',(s*2.735,-1.09,1.94),(s*2.735,1.49,1.94),.012,chrome)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'vintage-diner-detailed.blend'))
for o in list(bpy.data.objects):
 if o not in new:bpy.data.objects.remove(o,do_unlink=True)
groups={}
for o in new:groups.setdefault(o.data.materials[0].name,[]).append(o)
for n,objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name='Upholstery_'+n
path=ASSETS/'diner-upholstery.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_yup=True,export_apply=True,export_extras=True,export_cameras=False,export_lights=False)
sys.path.insert(0,str(SITE/'scripts'));from compact_cassette_glb import compact;compact(path)
print('REPAIRED_DINER_BOOTH',json.dumps({'parts':len(new),'batches':len(groups),'bytes':path.stat().st_size}),flush=True)
