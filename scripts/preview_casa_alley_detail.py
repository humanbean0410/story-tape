"""Render the exported refined models, including the same unlit baked surfaces."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
kind=sys.argv[sys.argv.index('--')+1]
root=Path(__file__).resolve().parents[1];out=root.parents[1]/'outputs'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root/'dist/assets'/('casa-storefront.glb' if kind=='casa' else 'night-alley.glb')))
for o in bpy.data.objects:
    if o.type!='MESH' or not ('Baked_Static' in o.name or 'Backdrop_NightAlley' in o.name):continue
    for m in o.data.materials:
        if not m:continue
        p=m.node_tree.nodes.get('Principled BSDF')
        if not p:p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        if not p.inputs['Base Color'].is_linked:continue
        link=p.inputs['Base Color'].links[0];tex=link.from_socket
        m.node_tree.links.remove(link);p.inputs['Base Color'].default_value=(0,0,0,1)
        m.node_tree.links.new(tex,p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=1

def area(pos,target,power,size,color):
    d=bpy.data.lights.new('Preview soft light','AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(d.name,d);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

world=bpy.data.worlds.new('Preview atmosphere');world.use_nodes=True;bpy.context.scene.world=world
background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
background.inputs[0].default_value=(.12,.15,.19,1) if kind=='casa' else (.02,.065,.105,1)
background.inputs[1].default_value=.8
if kind=='casa':
    pos=(-5.6,-9.8,3.8);target=(-.5,-1.1,2.42);lens=35
    area((-4,-5,7),(0,-1,2),1100,6,(.87,.95,1));area((2,-4,5),(0,-1,1.5),500,4,(1,.88,.68))
else:
    pos=(2.9,-10.9,2.85);target=(-.65,3.1,1.68);lens=35
    area((1,3.8,6),(0,3,0),750,7,(.13,.48,.75));area((-3.5,-.7,3.1),(-2.1,1.6,1.3),170,2.1,(1,.64,.30))
    area((1,-4,3),(-2,1.6,1),80,4,(.31,.48,.61))
camd=bpy.data.cameras.new('RefinementPreview');cam=bpy.data.objects.new('RefinementPreview',camd);bpy.context.collection.objects.link(cam)
cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camd.lens=lens
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.max_bounces=4;scene.cycles.device='CPU'
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=1440;scene.render.resolution_y=800 if kind=='casa' else 602
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.render.filepath=str(out/(kind+'-detail-export-preview.png'));bpy.ops.render.render(write_still=True)
print('DETAIL_PREVIEW_READY',scene.render.filepath,flush=True)
