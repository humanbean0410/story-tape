"""Reusable, featureless matte-white performers, posed in Blender for three sets."""
import bpy, math, sys, json
from mathutils import Vector
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];site=Path(args[0]);out=Path(args[1]);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
white=bpy.data.materials.new('Matte ivory / minimal performer');white.use_nodes=True;white.diffuse_color=(.83,.82,.79,1);p=white.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=white.diffuse_color;p.inputs['Roughness'].default_value=.68

def empty(name,parent=None,pos=(0,0,0)):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.parent=parent;o.location=pos;return o

def oval(name,pos,size,objects):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=pos);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(white)
 for f in o.data.polygons:f.use_smooth=True
 objects.append(o);return o

def link(name,a,b,r,objects):
 mid=(Vector(a)+Vector(b))/2;delta=Vector(b)-Vector(a);o=oval(name,mid,(r,r,delta.length/2+r*.5),objects);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return o

def merge(objects,name,parent):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.parent=parent
 return o

def person(name,parent,pos,rotation=0,scale=1,low=False,lean=False,table=False):
 root=empty(name,parent,pos);root.rotation_euler.z=rotation;root.scale=(scale,)*3;root['performer']='featureless matte-white studio miniature';parts=[]
 def point(v):
  x,y,z=v
  if low:z=z*.7 if z<.85 else z-.255
  return (x,y,z)
 def egg(n,v,s):return oval(name+n,point(v),s,parts)
 def bone(n,a,b,r):return link(name+n,point(a),point(b),r,parts)
 egg(' torso',(0,.40,1.41),(.23,.16,.32));egg(' pelvis',(0,.40,1.0),(.23,.19,.14));bone(' neck',(0,.39,1.60) if lean else (0,.39,1.65),(-.12,.39,1.74) if lean else (0,.39,1.83),.071)
 for side in [-1,1]:
  x=side*.14
  bone(' thigh',(x,.40,.98),(x,-.25,.78),.103);egg(' knee',(x,-.25,.78),(.108,.102,.105));bone(' calf',(x,-.25,.76),(x,-.40,.17),.07);egg(' foot',(x,-.50,.085),(.087,.155,.075))
  shoulder=(side*.21,.40,1.62);elbow=(side*.18,.45,1.28) if low else (side*.28,.12,1.35);wrist=(side*.10,.38,1.05) if low else (side*.08,-.02,1.14 if not table else 1.35)
  bone(' upper arm',shoulder,elbow,.075);egg(' elbow',elbow,(.078,.076,.078));bone(' forearm',elbow,wrist,.058);egg(' hand',(wrist[0],wrist[1]-.075,wrist[2]),(.048,.075,.029))
 body=merge(parts,name+'Body',root);bpy.context.view_layer.objects.active=body
 rem=body.modifiers.new('Continuous sculptural silhouette','REMESH');rem.mode='VOXEL';rem.voxel_size=.018;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
 smooth=body.modifiers.new('Soft joins','SMOOTH');smooth.factor=1.5;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
 dec=body.modifiers.new('Web silhouette','DECIMATE');dec.ratio=.32;bpy.ops.object.modifier_apply(modifier=dec.name)
 headparts=[];oval(name+' smooth oval',(0,0,0),(.153,.143,.195),headparts);head=merge(headparts,name+'Head',root);head.location=point((-.19 if lean else 0,.39,1.92-.065 if lean else 1.92));head.rotation_euler.y=math.radians(-21 if lean else 0)
 return root
interior=empty('InteriorPair');person('ActorMan',interior,(-.83,1.08,0));person('ActorWoman',interior,(.73,1.08,0))
diner=empty('DinerPair');person('ActorManDiner',diner,(-1.19,.18,0),math.pi/2,.82,table=True);person('ActorWomanDiner',diner,(1.19,.18,0),-math.pi/2,.82,table=True)
alley=empty('AlleyPair');person('ActorManAlley',alley,(-2.30,1.31,0),low=True);person('ActorWomanAlley',alley,(-1.81,1.31,0),low=True,lean=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'minimal-performers.blend'))
bpy.ops.export_scene.gltf(filepath=str(site/'dist/assets/minimal-performers.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_yup=True)
print(json.dumps({'status':'complete','bytes':(site/'dist/assets/minimal-performers.glb').stat().st_size,'actors':6,'style':'featureless white silhouettes','triangles':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH')}))
