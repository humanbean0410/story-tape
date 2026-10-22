"""Build a reusable, genuinely three-dimensional film-stage rig in Blender.

No scene floor is included: the perimeter sits around the existing street/station
model. Blender coordinates are Z-up; the front of the stage is negative Y.
Run: Blender --background --factory-startup --python build_studio_rig.py
Optional positional arguments after -- are the site directory and output folder.
"""
import bpy, bmesh, math, json, sys
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
base=Path(__file__).resolve().parents[1]
SITE=Path(args[0]).resolve() if args else (base if (base/'dist').is_dir() else base/'casa')
OUT=Path(args[1]).resolve() if len(args)>1 else SITE.parent.parent/'outputs'
ASSETS=SITE/'dist/assets'
ASSETS.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
root=bpy.data.objects.new('StudioRig',None);bpy.context.collection.objects.link(root)
root['asset_role']='behind-the-scenes';root['front']='negative Blender Y / positive glTF Z'
parts=[]

def material(name,color,rough=.6,metal=0,emit=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if emit:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
    return m
cloth=material('RigBlackVelour',(.018,.021,.023),.97)
metal=material('RigGraphiteMetal',(.048,.053,.058),.32,.78)
silver=material('RigBrushedAluminium',(.30,.32,.33),.31,.80)
rubber=material('RigRubber',(.009,.011,.013),.92)
plywood=material('RigPlywood',(.26,.145,.062),.78)
plyedge=material('RigPlywoodLaminations',(.39,.26,.13),.76)
bulb=material('RigBulb',(1,.72,.37),.27,0,1.5)
diffuser=material('RigSoftboxDiffuser',(.80,.82,.77),.75)
lens=material('RigCameraLens',(.028,.060,.067),.12,.72)
white=material('RigClapperWhite',(.75,.74,.68),.63)
red=material('RigSafetyRed',(.35,.037,.018),.65)

def register(o,m):
    o.parent=root
    if m:o.data.materials.append(m)
    parts.append(o);return o
def cube(name,pos,size,m,bevel=.01):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
    if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=1,affect='EDGES',clamp_overlap=True)
    d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();d.update()
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos
    return register(o,m)
def cyl(name,pos,r,length,m,vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=length,location=pos)
    o=bpy.context.object;o.name=name
    for p in o.data.polygons:p.use_smooth=True
    return register(o,m)
def beam(name,a,b,r,m,vertices=10):
    a=Vector(a);b=Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,m,vertices)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def mesh(name,verts,faces,m):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update()
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);return register(o,m)
def cable(name,points,r=.012):
    for i,(a,b) in enumerate(zip(points,points[1:])):beam(name+'_'+str(i),a,b,r,rubber,6)

# Nineteen metre stage edge. The opening is completely empty, without a floor.
for name,pos,size in [('StageFrontPlywood',(1,-7.82,-.26),(19,.22,.5)),('StageBackPlywood',(1,4.80,-.26),(19,.22,.5)),('StageLeftPlywood',(-8.40,-1.51,-.26),(.22,12.85,.5)),('StageRightPlywood',(10.40,-1.51,-.26),(.22,12.85,.5))]:
    cube(name,pos,size,plywood,.018)
    for z in [-.43,-.31,-.19,-.07]:
        s=(size[0],size[1]+.009,.006) if 'Front' in name or 'Back' in name else (size[0]+.009,size[1],.006)
        cube(name+'_PlyEdge',(*pos[:2],z),s,plyedge,0)
# Tubular frame holds a very dark velour curtain. Geometry carries the pleating.
for x in [-8.25,1,10.25]:beam('CurtainFramePost',(x,4.66,-.45),(x,4.66,9.28),.048,metal)
beam('CurtainTopRail',(-8.35,4.65,9.28),(10.35,4.65,9.28),.06,metal)
verts=[];faces=[];nx=280;nz=9
for iz in range(nz+1):
    z=iz*9/nz
    for ix in range(nx+1):
        x=-8.2+ix*18.4/nx
        pleat=.11*math.sin(ix*math.tau/5)+.025*math.sin(ix*math.tau/2.5)
        sag=.035*math.sin(z*.9+ix*.12)
        verts.append((x,4.55+pleat+sag,z))
for iz in range(nz):
    for ix in range(nx):
        a=iz*(nx+1)+ix;faces.append((a,a+1,a+nx+2,a+nx+1))
curtain=mesh('RearVelourCurtain',verts,faces,cloth)
for p in curtain.data.polygons:p.use_smooth=True
for x in [-8.2+q*.92 for q in range(21)]:
    beam('CurtainTie',(x,4.57,8.9),(x,4.65,9.27),.014,rubber,6)
# A short black side return reveals the stage volume while preserving both views.
for x,name in [(-8.18,'Left'),(10.18,'Right')]:
    vs=[];fs=[]
    for z in [0,9]:
        for i in range(50):vs.append((x+.10*math.sin(i*math.tau/5),1.1+i*3.45/49,z))
    for i in range(49):fs.append((i,i+1,i+51,i+50))
    mesh(name+'VelourReturn',vs,fs,cloth)

def tripod(prefix,position,height,span=.8):
    x,y=position
    beam(prefix+'_MainColumn',(x,y,.28),(x,y,height),.032,silver)
    beam(prefix+'_LowerSleeve',(x,y,.23),(x,y,height*.56),.043,metal)
    for z in [height*.54,height*.77]:
        cyl(prefix+'_LockCollar',(x,y,z),.061,.08,metal)
        beam(prefix+'_Knob',(x,y,z),(x+.105,y,z),.022,rubber)
    for angle in [0,math.tau/3,2*math.tau/3]:
        foot=(x+span*math.cos(angle),y+span*math.sin(angle),.035)
        beam(prefix+'_Leg',(x,y,.56),foot,.028,metal)
        beam(prefix+'_Brace',(x,y,.25),(x+span*.57*math.cos(angle),y+span*.57*math.sin(angle),.25),.014,silver)
        cyl(prefix+'_RubberFoot',foot,.048,.04,rubber)

def localpos(origin,q,local):return Vector(origin)+q@Vector(local)
def light_box(prefix,origin,target,rectangular=False):
    q=(Vector(target)-Vector(origin)).to_track_quat('Z','Y')
    def block(n,loc,size,mat,bevel=.01):
        o=cube(prefix+'_'+n,localpos(origin,q,loc),size,mat,bevel);o.rotation_euler=q.to_euler();return o
    def disk(n,loc,r,dep,mat):
        o=cyl(prefix+'_'+n,localpos(origin,q,loc),r,dep,mat,24);o.rotation_euler=q.to_euler();return o
    if rectangular:
        block('SoftboxHousing',(0,0,0),(1.2,.82,.30),metal,.055)
        block('SoftboxDiffuser',(0,0,.16),(1.11,.73,.018),diffuser,.01)
        block('LightSurface',(0,0,.17),(1.05,.67,.01),bulb,0)
        for yy in [-.31,-.10,.10,.31]:block('DiffuserGrid',(0,yy,.188),(1.11,.009,.011),silver,0)
        for xx in [-.45,-.23,0,.23,.45]:block('DiffuserGrid',(xx,0,.188),(.009,.73,.011),silver,0)
        for xx in [-.67,.67]:block('YokeUpright',(xx,0,-.10),(.055,.055,.35),metal)
        block('YokeCrossbar',(0,0,-.30),(1.38,.055,.055),metal)
    else:
        disk('FresnelBody',(0,0,-.12),.29,.48,metal)
        for zz in [-.34,-.26,-.18,-.10,-.02,.05]:disk('CoolingRing',(0,0,zz),.306,.018,metal)
        disk('ReflectorRim',(0,0,.13),.32,.05,silver)
        disk('LightSurface',(0,0,.166),.26,.012,bulb)
        for angle in [0,math.pi/2,math.pi,math.pi*1.5]:
            # Four separate barn doors, opened away from the light beam.
            loc=(.40*math.cos(angle),.40*math.sin(angle),.25)
            o=block('BarnDoor',loc,(.34,.20,.018),metal)
            o.rotation_euler.rotate_axis('Z',angle);o.rotation_euler.rotate_axis('Y',-.35)
        for xx in [-.38,.38]:block('YokeUpright',(xx,0,-.13),(.045,.05,.44),metal)
        block('YokeCrossbar',(0,0,-.37),(.80,.05,.05),metal)
    block('RearCableSocket',(0,-.10,-.30),(.11,.11,.10),rubber)

lights=[('RigKey',(-5.65,-4.0),4.8,(-.2,0,2.2),True),('RigFill',(7.5,-3.5),3.7,(1,0,2.0),False),('RigRim',(6.6,3.7),5.8,(.5,-.7,2.7),False)]
for prefix,xy,h,target,rect in lights:
    tripod(prefix,xy,h-.30,1.0)
    light_box(prefix,(xy[0],xy[1],h),target,rect)
    cable(prefix+'_PowerCable',[(xy[0],xy[1],h-.40),(xy[0],xy[1],.07),(xy[0]+.5,xy[1]+.18,.03),(xy[0]+1.4,xy[1]-.40,.03),(9.95,-6.8,.035)],.017)
    cube(prefix+'_Sandbag',(xy[0]+.55,xy[1]+.15,.12),(.50,.30,.20),rubber,.065)

# Two low steel rails and spaced sleepers. No broad slab covers either scene.
for y in [-6.7,-5.65]:
    beam('CameraDollyTrack',(-5.7,y,.075),(5.6,y,.075),.028,silver,12)
for x in [-5.4,-3.4,-1.4,.6,2.6,4.6]:cube('TrackSleeper',(x,-6.175,.023),(.12,1.25,.034),plywood,.005)
cx,cy=-3.5,-6.175
cube('DollyDeck',(cx,cy,.20),(1.15,1.15,.09),metal,.025)
for x in [cx-.48,cx+.48]:
    for y in [-6.7,-5.65]:
        o=cyl('DollyWheel',(x,y,.15),.10,.095,rubber);o.rotation_euler.x=math.pi/2
tripod('CameraTripod',(cx,cy),1.54,.44)
cube('CameraFluidHead',(cx,cy,1.57),(.28,.25,.18),metal,.025)
beam('CameraPanHandle',(cx,cy-.05,1.62),(cx+.18,cy-.54,1.48),.021,metal)
cube('CameraBody',(cx,cy,1.89),(.48,.60,.37),metal,.032)
cube('CameraShoulderPad',(cx,cy,1.65),(.50,.44,.06),rubber,.018)
camera_lens=beam('CameraZoomLens',(cx,cy+.30,1.91),(cx,cy+.68,1.91),.145,metal,24)
beam('CameraLensGlass',(cx,cy+.68,1.91),(cx,cy+.688,1.91),.13,lens,24)
for y in [cy+.35,cy+.48,cy+.60]:beam('CameraLensFocusRing',(cx,y,1.91),(cx,y+.035,1.91),.155,rubber,24)
cube('CameraMatteBox',(cx,cy+.72,1.91),(.43,.09,.33),metal,.015)
cube('CameraMatteBoxOpening',(cx,cy+.769,1.91),(.30,.006,.20),lens,0)
cube('CameraBattery',(cx,cy-.35,1.85),(.34,.19,.30),rubber,.018)
cube('CameraTopHandle',(cx,cy,2.17),(.065,.48,.06),metal,.016)
for y in [cy-.17,cy+.17]:cube('CameraTopHandleLeg',(cx,y,2.105),(.06,.06,.13),metal,.01)
cube('CameraMonitor',(cx-.32,cy,2.09),(.05,.37,.26),metal,.015)
cube('CameraMonitorGlass',(cx-.348,cy,2.09),(.005,.31,.20),lens,0)
cable('CameraTether',[(cx-.28,cy-.2,1.89),(cx-.50,cy-.5,1.15),(cx-.5,cy-.5,.03),(-.2,-7.3,.03),(8,-7.3,.03)],.012)

# A physical clapperboard with only diagonal black-and-white bars.
board=cube('ClapperBoard',(5.0,-5.2,.63),(.80,.045,.51),rubber,.018)
board.rotation_euler.z=-.13
cube('ClapperHinge',(4.63,-5.2,.94),(.08,.06,.18),metal,.008)
cube('ClapperLowerBar',(5.0,-5.225,.895),(.80,.06,.075),white,.005)
o=cube('ClapperUpperBar',(5.0,-5.2,.99),(.80,.065,.09),white,.005);o.rotation_euler.y=-.10
for i in range(5):
    x=4.66+i*.155
    mesh('ClapperDiagonalStripe',[(x,-5.26,.855),(x+.067,-5.26,.855),(x+.122,-5.26,.934),(x+.055,-5.26,.934)],[(0,1,2,3)],rubber)
    mesh('ClapperDiagonalStripe',[(x,-5.238,.95),(x+.067,-5.238,.95),(x+.122,-5.238,1.034),(x+.055,-5.238,1.034)],[(0,1,2,3)],rubber)
cube('ClapperCrate',(5.0,-5.20,.18),(.91,.55,.35),plywood,.015)
for x in [4.57,5.43]:cube('ClapperCrateEdge',(x,-5.48,.18),(.04,.015,.32),plyedge,.002)
cube('PowerDistributionBox',(9.9,-6.85,.23),(.46,.48,.40),metal,.025)
for i in range(3):cyl('PowerSocket',(9.75+i*.14,-7.1,.24),.04,.035,rubber)

# Model is deliberately portable: no cameras, lights, images, bake or dependencies.
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
scene.world.color=(.05,.05,.05)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'studio-rig.blend'))
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'studio-rig.glb'),export_format='GLB',use_selection=True,export_yup=True,export_extras=True,export_apply=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
notes={'root':'StudioRig','units':'metres','blender_bounds':{'x':[-8.51,10.51],'y':[-7.93,4.91],'z':[-.51,9.34]},'gltf_y_up_bounds':{'x':[-8.51,10.51],'y':[-.51,9.34],'z':[-4.91,7.93]},'front':'positive glTF Z','perimeter_inner_opening':{'x':[-8.29,10.29],'gltf_z':[-4.69,7.71]},'light_material':'RigBulb','light_mesh_prefixes':['RigKey','RigFill','RigRim'],'light_origins_gltf':{'RigKey':[-5.65,4.8,4.0],'RigFill':[7.5,3.7,3.5],'RigRim':[6.6,5.8,-3.7]},'camera_origin_gltf':[-3.5,1.89,6.175],'mesh_objects':len(parts),'glb_bytes':(ASSETS/'studio-rig.glb').stat().st_size}
(SITE.parent/'model/studio-rig-notes.json').write_text(json.dumps(notes,indent=2))
print('STUDIO_RIG_RESULT '+json.dumps(notes))
