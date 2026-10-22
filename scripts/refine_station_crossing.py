import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/wqr/Documents/Codex/2026-10-10/gpt-site-casa-de-las-bellas');ASSET=ROOT/'work/casa/dist/assets'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ASSET/'hasedera-station.glb'))
# Replace the previous fixed crossing additions; preserve the authored platform.
for o in list(bpy.data.objects):
 if o.name.startswith(('Crossing_Detail_','GatePivot_','GateArm_')):bpy.data.objects.remove(o,do_unlink=True)
objects=[]
def mat(n,c,metal=0,rough=.5):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
metal=mat('Crossing enamel green',(.14,.24,.22),.5,.4);black=mat('Crossing black',(.024,.029,.023),.1,.7);yellow=mat('Crossing faded yellow',(.67,.52,.13),.1,.62);red=mat('Crossing signal red',(.45,.026,.018),.05,.25);stone=mat('Crossing approach concrete',(.26,.28,.24),0,.9);wood=mat('Crossing old bench',(.26,.115,.053),0,.76);cream=mat('Crossing notice cream',(.59,.59,.47),0,.78)
def cube(n,p,d,m,b=.01):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=n;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if b:mod=o.modifiers.new('Soft worn edges','BEVEL');mod.width=b;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 objects.append(o);return o
def rod(n,a,b,r,m,v=20):
 mid=(Vector(a)+Vector(b))*.5;d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d.length,location=mid);o=bpy.context.object;o.name=n;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 objects.append(o);return o
# The road crosses perpendicular to the rails, not along them. Posts stand
# 2.55 m either side of the track center, beyond the vehicle swept envelope.
# Opposite arms fold from opposite corners. Each is a real pivoted assembly.
for index,(x,y,side) in enumerate([(8.18,-1.17,1),(11.28,-6.27,-1)]):
 cube('Crossing pole base',(x,y,.05),(.46,.46,.20),stone)
 rod('Crossing striped pole',(x,y,.13),(x,y,3.58),.057,black)
 for z in [.26+i*.28 for i in range(11)]:rod('Crossing pole amber stripe',(x,y,z),(x,y,z+.12),.058,yellow)
 # Crossing crossbuck and weatherproof hoods, rather than one horizontal bar.
 for sign in [-1,1]:rod('Crossing crossbuck',(x-.32,y,3.42+sign*.27),(x+.32,y,3.42-sign*.27),.043,yellow)
 for xx in [x-.23,x+.23]:
  rod('Signal hood',(xx,y,2.96),(xx,y+side*.20,2.96),.115,black,32)
  rod('Signal red lens',(xx,y+side*.205,2.96),(xx,y+side*.209,2.96),.08,red,32)
 cube('Barrier motor enclosure',(x,y-.02,.85),(.36,.31,.56),metal,.028)
 rod('Barrier axis boss',(x,y-.23,1.075),(x,y+.20,1.075),.085,black,32)
 hinge=bpy.data.objects.new('GatePivot_'+('Entry' if index==0 else 'Exit'),None);bpy.context.collection.objects.link(hinge);hinge.location=(x,y,1.075);hinge['gateSide']=side
 added=len(objects)
 rod('Barrier tapered arm',(x,y,1.075),(x+side*3.04,y,1.075),.041,yellow)
 for j in range(8):
  xx=x+side*(.22+j*.35);rod('Barrier black diagonal band',(xx,y,1.075),(xx+side*.15,y,1.075),.0425,black)
 for dist in [.53,2.50]:
  xx=x+side*dist;rod('Barrier white warning ring',(xx,y,1.075),(xx+side*.12,y,1.075),.044,cream)
  rod('Barrier red warning ring',(xx+side*.035,y,1.075),(xx+side*.079,y,1.075),.045,red)
 cube('Barrier end cap',(x+side*3.04,y,1.075),(.035,.10,.10),red,.01)
 for o in objects[added:]:
  bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=hinge;o.matrix_world=world
 # Keep road edges and mechanical cabinet clear of rail heads.
 cube('Signal relay box',(x-side*.23,y-side*.22,.47),(.28,.20,.38),metal,.02)
for y in [-3.72]:cube('Crossing grooved rubber road',(9.73,y,.10),(3.10,1.22,.17),black,.01)
for y in [-1.87,-5.57]:cube('Crossing approach asphalt',(9.73,y,.075),(3.10,2.02,.20),stone,.012)
for x in [8.28,11.18]:
 for y in [-.25,-.95,-6.95,-7.65]:cube('Road edge white paint',(x,y,.178),(.065,.35,.006),cream,.001)
for y in [-.40,-7.0]:cube('Road stop line',(9.73,y,.18),(2.78,.11,.006),cream,.001)
# Narrow drainage channels sit beside the path, without a fence across the rails.
for x in [8.10,11.36]:
 cube('Road side drainage slot',(x,-3.72,.04),(.12,6.50,.06),black,.005)
# A weathered wooden bench at the right end, as in the new platform reference.
for i in range(5):cube('Platform wood seat slat',(5.92,-.25+i*.105,.71),(2.05,.083,.07),wood,.015)
for i in range(4):cube('Platform wood back slat',(5.92,.4,1.02+i*.12),(2.05,.07,.083),wood,.012)
for x in [5.12,6.72]:
 rod('Bench front leg',(x,-.23,.22),(x,-.23,.7),.038,metal);rod('Bench back leg',(x,.4,.22),(x,.4,1.47),.037,metal);rod('Bench arm',(x,-.23,.94),(x,.4,.94),.027,metal)
 for z in [1.02,1.14,1.26,1.38]:rod('Wood slat recessed bolt',(x,.36,z),(x,.352,z),.014,cream,12)
# A useful prop for one close-up, no mannequin in any seat.
cube('Folded timetable',(6.12,-.1,.758),(.27,.2,.012),cream,.004)
# Merge added parts by material so detail does not cost hundreds of draw calls.
groups={}
for o in objects:groups.setdefault((o.data.materials[0],o.parent.name if o.parent else None),[]).append(o)
for (material,parent),group in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in group:o.select_set(True)
 bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join();bpy.context.object.name=('GateArm_' if parent else 'Crossing_Detail_')+material.name
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/hasedera-station-crossing.blend'))
bpy.ops.export_scene.gltf(filepath=str(ASSET/'hasedera-station.glb'),export_format='GLB',export_yup=True,export_extras=True,export_apply=True,export_cameras=False,export_lights=False)
print('CROSSING_REFINEMENT_COMPLETE: opposite pivoted arms, 2.55 m rail-center clearance, transverse road and rail-head-level infill')
