"""A physical blue-hour alley and bench set, inspired by IMG_1810.JPG.
Run Blender --background --factory-startup --python this_file -- SITE OUTPUTS.
The editable blend keeps individual stone, window, ironwork and set dressing meshes.
The web export bakes static surfaces and contains no modeled people.
"""
import bpy, math, random, json, sys, shutil, struct
from pathlib import Path
from mathutils import Vector, Matrix

# Reuse this project's geometry helpers and original generic adult sculptures.
# This prefix creates materials and functions only; it does not build the lounge.
source=Path(__file__).with_name('build_interior.py').read_text()
exec(compile(source.split('# A physical three-wall set')[0],str(__file__),'exec'))
random.seed(1810)
stone=[mat('Night limestone %02d'%i,(.27+.021*i,.30+.019*i,.285+.018*i),.9,noise=.2,scale=110) for i in range(6)]
wallpaint=[mat('Night faded lime plaster %d'%i,c,.93,noise=.22,scale=70) for i,c in enumerate([(.42,.38,.26),(.31,.40,.39),(.37,.35,.26),(.32,.34,.31)])]
cobble=[mat('Wet blue slate %d'%i,(.08+.012*i,.13+.012*i,.15+.012*i),.54,noise=.32,scale=25) for i in range(8)]
joint=mat('Mossy stone joints',(.032,.065,.065),.97)
iron=mat('Blue black wrought iron',(.022,.049,.058),.4,.65,noise=.12)
benchwood=mat('Weathered teal bench slats',(.055,.21,.225),.54,noise=.22,scale=9)
doorwood=mat('Old bottle green oak door',(.025,.075,.063),.62,noise=.32,scale=12)
shutter=mat('Dark slate green shutters',(.07,.12,.115),.82,noise=.15)
windowdark=mat('Recessed blue black glass',(.011,.026,.034),.21,.22)
amberglass=mat('NightLanternGlass',(.98,.64,.22),.39)
p=amberglass.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.62,.17,1);p.inputs['Emission Strength'].default_value=2.2
creamlight=mat('Night warm window',(.55,.31,.12),.44)
p=creamlight.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.66,.34,.1,1);p.inputs['Emission Strength'].default_value=.35
terracotta=mat('Chipped terracotta flower pots',(.27,.095,.047),.82,noise=.3)
pink=mat('Rose pink petals',(.65,.145,.30),.75)
red=mat('Burgundy rose petals',(.36,.012,.035),.69)
whiteflower=mat('Ivory rose petals',(.73,.63,.42),.82)
foliagemat=mat('Night green stems and leaves',(.027,.10,.044),.85)
coat=mat('Shared brown wool coat',(.24,.13,.065),.93,noise=.14,scale=230)
coatfold=mat('Brown coat seam edge',(.31,.19,.105),.93)
slate.diffuse_color=(.48,.35,.29,1);slate.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.48,.35,.29,1)
for node in slate.node_tree.nodes:
 if node.type=='VALTORGB':
  node.color_ramp.elements[0].color=(.43,.32,.26,1);node.color_ramp.elements[1].color=(.53,.39,.32,1)

# A finite, open-front soundstage: no backdrop photograph or flat scenery.
cube('Night stage foundation',(-.6,3.30,-.22),(13.9,15.5,.36),joint,.035)
for row in range(43):
 for col in range(26):
  x=-7.25+col*.535+(row%2)*.2675;y=-4.08+row*.359
  if x>6.22:continue
  o=cube('Individually bevelled cobblestone',(x,y,.008+random.uniform(-.008,.008)),(.519,.341,.069),random.choice(cobble),.012)
  o.rotation_euler.z=random.uniform(-.01,.01)
# A shallow gutter and grate across the foreground alley.
for y in [-.65,3.75,8.55]:
 cube('Drain frame',(1.68,y,.047),(.58,.35,.035),iron,.006)
 for x in [1.43+i*.056 for i in range(10)]:cube('Drain opening ribs',(x,y,.066),(.016,.29,.017),black,.002)
for x in [-.37,4.02]:cube('Street limestone curb',(x,6.15,.11),(.19,9.7,.16),stone[2],.018)

def arch(name,cx,y,z,w,h,m,group=static,thick=.11):
 pts=[]
 for i in range(25):
  a=math.pi*i/24;pts.append((cx+w*.5*math.cos(a),y,z+h+w*.5*math.sin(a)))
 tube(name,[(cx+w*.5,y,z)]+pts+[(cx-w*.5,y,z)],thick,m,group,10)

def facade(name,width,height,color,at,angle=0,door=True,windows=2):
 start=len(static)
 cube(name+' lime masonry core',(0,.18,height/2),(width,.36,height),color,.012)
 cube(name+' dark stone plinth',(0,-.035,.28),(width,.10,.55),stone[1],.01)
 for z,depth,h in [(height-.32,.21,.12),(height-.19,.14,.075),(height-.08,.26,.09)]:cube(name+' layered cornice',(0,-depth*.3,z),(width+.13,depth,h),stone[3],.014)
 # Tactile blockwork corners with varying masonry lengths.
 for x in [-width*.5+.11,width*.5-.11]:
  for j in range(int(height/.27)):
   cube(name+' corner ashlar',(x,-.063,.17+j*.27),(.24 if j%2 else .36,.095,.245),stone[(j+1)%6],.008)
 # Faint lime patchwork and small masonry stress cracks, all geometric.
 for j in range(12):
  x=random.uniform(-width*.44,width*.44);z=random.uniform(.55,height-.58)
  cube(name+' old plaster patch',(x,-.009,z),(random.uniform(.12,.44),.016,random.uniform(.035,.13)),stone[j%6],.005)
 if door:
  dx=-width*.23;dw=1.05;dh=1.70
  cube(name+' door recessed opening',(dx,-.03,dh*.5),(dw+.19,.045,dh),windowdark,.025)
  cube(name+' solid oak door',(dx,-.082,.79),(dw,.095,1.52),doorwood,.012)
  for x in [dx-.36,dx,dx+.36]:
   for z in [.46,1.13]:
    cube(name+' recessed door panel',(x,-.136,z),(.29,.014,.48),windowdark,.009)
    for xx in [x-.13,x+.13]:cube(name+' carved panel stile',(xx,-.15,z),(.027,.022,.44),doorwood,.004)
    for zz in [z-.23,z+.23]:cube(name+' carved panel bead',(x,-.155,zz),(.28,.026,.03),doorwood,.004)
  cube(name+' brass mail slot',(dx,-.18,.93),(.26,.026,.045),brass,.006)
  ellipsoid(name+' door knob',(dx+.35,-.188,.98),(.043,.033,.043),brass,static,14,10)
  arch(name+' rounded stone door surround',dx,-.19,.03,dw+.22,dh,stone[4],thick=.105)
  for i in range(11):
   a=math.pi*i/10;x=dx+(dw*.5+.19)*math.cos(a);z=dh+(dw*.5+.19)*math.sin(a)
   o=cube(name+' arch wedge stone',(x,-.10,z),(.22,.24,.27),stone[i%6],.012);o.rotation_euler.y=a-math.pi*.5
  cube(name+' stone threshold',(dx,-.30,.065),(dw+.32,.6,.12),stone[1],.012)
  # Arched fanlight visible above the panelled door.
  for i in [-2,-1,0,1,2]:beam(name+' fanlight radiating grille',(dx,-.203,dh),(dx+i*.17,-.203,dh+.32+(.10 if abs(i)<2 else 0)),.014,iron,n=8)
 # Upper storey shuttered windows and ground-floor side aperture.
 locations=[(-width*.23,height-.95),(width*.25,height-.95)] if windows>=2 else [(width*.24,height-.95)]
 if width>3.5:locations.append((width*.25,1.48))
 for wi,(x,z) in enumerate(locations):
  ww=.67;hh=1.10
  cube(name+' window deep recess',(x,-.035,z),(ww+.18,.025,hh+.17),windowdark,.008)
  for sx in [-1,1]:
   cube(name+' stone window jamb',(x+sx*(ww*.5+.08),-.104,z),(.12,.17,hh+.23),stone[3],.014)
   cx=x+sx*.183
   cube(name+' shutter outer edge',(cx+sx*.13,-.15,z),(.025,.044,hh),shutter,.004)
   for j in range(13):
    sl=cube(name+' louvered shutter',(cx,-.136,z-.49+j*.077),(.258,.055,.036),shutter,.004);sl.rotation_euler.x=math.radians(-24)
  for zz in [z-hh*.5-.085,z+hh*.5+.085]:cube(name+' stone sill',(x,-.158,zz),(ww+.34,.28,.095),stone[4],.012)
  cube(name+' shutter meeting rail',(x,-.178,z),(.035,.033,hh),iron,.004)
  for zz in [z-.36,z+.36]:cube(name+' shutter pintle',(x-.32,-.175,zz),(.06,.048,.045),iron,.004)
  if wi==0:
   for xx in [-.19,0,.19]:beam(name+' window iron bar',(x+xx,-.20,z-.48),(x+xx,-.20,z+.47),.012,iron,n=8)
 # Old utility conduit and timber sign mount.
 tube(name+' exposed conduit',[(width*.45,-.16,.13),(width*.45,-.16,height*.63),(width*.35,-.16,height*.71)],.021,iron,static,8)
 cube(name+' wall house plaque',(width*.36,-.2,2.4),(.24,.04,.28),stone[1],.009)
 root=empty(name+' editable facade',at);root.rotation_euler.z=angle
 for o in static[start:]:o.parent=root
 return root

facade('Bench corner house',5.6,4.8,wallpaint[0],(-3.08,2.73,0),0)
facade('Alley west house',3.65,5.25,wallpaint[1],(-.27,4.57,0),math.pi/2)
facade('Alley west rear house',4.4,5.85,wallpaint[2],(-.27,8.60,0),math.pi/2)
facade('Alley east front house',4.1,5.70,wallpaint[2],(4.06,3.8,0),-math.pi/2)
facade('Alley east rear house',4.3,5.20,wallpaint[3],(4.06,8.0,0),-math.pi/2)
facade('Alley far house',4.3,5.75,wallpaint[1],(1.88,10.95,0),0)
# Roof silhouettes, chimney flues and wall-tied phone wire add real spatial depth.
for x,y,z,sx,sy in [(-3.08,2.86,4.88,5.85,.74),(-.47,6.60,5.88,.65,8.75),(4.35,5.9,5.85,.63,8.60),(1.8,11.12,5.95,4.5,.61)]:
 cube('Aged terracotta coping',(x,y,z),(sx,sy,.11),terracotta,.018)
for x,y,z in [(-.55,6.3,6.13),(4.30,8.5,5.6),(2.9,11.1,6.15)]:
 cube('Rooftop chimney stack',(x,y,z),(.38,.39,.8),stone[1],.01);cube('Chimney cap',(x,y,z+.45),(.54,.54,.15),terracotta,.01)
tube('Sagging overhead cable',[(-.1,3.6,4.45),(.72,4.0,4.32),(1.85,4.12,4.27),(3.8,4.28,4.39)],.012,iron,static,6)
tube('Old rainpipe',[(-.20,2.65,4.5),(-.20,2.45,3.9),(-.20,2.45,.3),(-.05,2.3,.1)],.048,iron,static,10)
for z in [.65,2.2,3.5]:cube('Rainpipe retaining strap',(-.20,2.5,z),(.16,.06,.046),iron,.008)

# Real curved iron armrests and individually shaped slats for the shared bench.
bx=-2.06;by=1.77
for x in [bx-1.06,bx+1.06]:
 for y in [by-.40,by+.34]:
  tube('Bench curved iron leg',[(x,y-.10,.07),(x,y,.17),(x,y,.44),(x,y+.025,.59)],[.034,.045,.044,.041],iron,static,12)
  cube('Bench iron foot',(x,y-.08,.045),(.20,.24,.055),iron,.015)
 tube('Bench curved back bracket',[(x,by-.34,.56),(x,by+.36,.58),(x,by+.49,.80),(x,by+.56,1.24)],.046,iron,static,12)
 tube('Bench curled armrest',[(x,by-.51,.70),(x,by-.53,.84),(x,by-.40,.94),(x,by+.2,.91),(x,by+.44,.85)],.045,iron,static,14)
 for yy in [by-.35,by+.30]:ellipsoid('Bench exposed brass bolt',(x+.045,yy,.58),(.012,.027,.027),brass,static,12,8)
for j in range(5):cube('Bench teal seat slat',(bx,by-.39+j*.18,.57),(2.47,.156,.065),benchwood,.016)
for j in range(4):
 o=cube('Bench teal back slat',(bx,by+.45+j*.025,.78+j*.145),(2.47,.062,.12),benchwood,.018);o.rotation_euler.x=-.13
for x in [bx-1.1,bx+1.1]:
 for z in [.77,.915,1.06,1.205]:ellipsoid('Bench slat round fastener',(x,by+.412+(z-.77)*.18,z),(.023,.008,.023),iron,static,10,8)

# Flower pots and rose bouquets made from petals, stems and leaves.
def flowerpot(cx,cy,height,radius,seed):
 random.seed(seed);pts=[(cx,cy,.045),(cx,cy,height*.12),(cx,cy,height*.93),(cx,cy,height)]
 tube('Terracotta tapered flower pot',pts,[radius*.60,radius*.7,radius,radius*1.04],terracotta,static,24)
 tube('Terracotta pot lip',[(cx,cy,height-.035),(cx,cy,height+.005)],[radius*1.06,radius*1.06],terracotta,static,24)
 ellipsoid('Flower soil',(cx,cy,height+.007),(radius*.87,radius*.87,.024),soil,static,20,8)
 for f in range(8):
  a=random.uniform(0,math.tau);r=random.uniform(.02,radius*.7);x=cx+r*math.cos(a);y=cy+r*math.sin(a);z=height+random.uniform(.20,.38)
  beam('Rose stalk',(x,y,height),(x+.04,y,z),.008,foliagemat,n=7)
  for s in [-1,1]:ellipsoid('Rose pointed leaf',(x+s*.065,y-.02,z-.12),(.077,.032,.012),foliagemat,static,12,8)
  petal=[pink,whiteflower,red][f%3]
  for ring in range(2):
   for k in range(7):
    a=k*math.tau/7+ring*.4;rr=.025+ring*.021
    ellipsoid('Layered rose petal',(x+.04+rr*math.cos(a),y+rr*math.sin(a),z+ring*.012),(.034,.024,.028),petal,static,12,8)
  ellipsoid('Rose flower heart',(x+.04,y,z+.028),(.023,.023,.026),petal,static,12,8)
for x,y,h,r,s in [(-3.74,1.67,.31,.23,47),(-3.47,1.09,.25,.20,31),(-3.97,1.02,.24,.17,9)]:flowerpot(x,y,h,r,s)

# Wrought iron wall lantern, with translucent warm panes and curled scrollwork.
lx=-2.56;ly=2.29;lz=3.12
cube('Lantern wall rosette',(lx,2.64,lz+.34),(.15,.09,.26),iron,.024)
tube('Lantern swept arm',[(lx,2.64,lz+.28),(lx,2.45,lz+.38),(lx,2.14,lz+.52),(lx,1.95,lz+.46),(lx,1.97,lz+.32)],.025,iron,static,12)
scroll=[]
for i in range(32):
 t=i/31;a=t*math.pi*3.0;r=.14*(1-t)+.035;scroll.append((lx+.02,2.40-r*math.cos(a),lz+.2+r*math.sin(a)))
tube('Lantern iron supporting scroll',scroll,.015,iron,static,8)
cube('Lantern top pitched cap',(lx,2.05,lz+.27),(.32,.30,.075),iron,.025)
cube('Lantern lower tray',(lx,2.05,lz-.27),(.24,.24,.05),iron,.016)
for x in [lx-.125,lx+.125]:
 for y in [1.93,2.17]:beam('Lantern corner iron rail',(x,y,lz-.24),(x+(.018 if x<lx else -.018),y,lz+.23),.015,iron,n=8)
cube('PracticalLampGlow',(lx,2.05,lz),(.215,.207,.45),amberglass,.018,live)
ellipsoid('Lantern ornamental finial',(lx,2.05,lz+.37),(.035,.035,.08),iron,static,16,10)
ellipsoid('Lantern bottom finial',(lx,2.05,lz-.35),(.023,.023,.06),iron,static,12,10)
# Secondary lanterns along the receding street.
for x,y,z in [(-.05,5.4,3.28),(3.81,8.42,3.65)]:
 cube('Secondary lamp cage',(x,y,z),(.22,.22,.32),iron,.024)
 cube('PracticalLampGlow',(x-.015,y-.13,z),(.17,.018,.23),creamlight,.01,live)

# An empty bench carries traces of a date without any humanoid sculpture.
# Cloth rests on the actual seat rather than suspending over absent bodies.
for i in range(3):
 cube('Folded wool scarf layer',(-1.63,1.72,.635+i*.022),(.49-.02*i,.31,.020),coat,.012)
for j in range(10):
 tube('Folded scarf short fringe',[(-1.845+j*.042,1.555,.666),(-1.852+j*.042,1.50,.649)],.0028,coat,static,7)
cube('Letter left on empty bench',(-2.66,1.61,.607),(.31,.19,.005),linen,.002)

# A small canvas bag on the empty part of the bench.
cube('Folded leather shoulder bag',(-.98,1.65,.75),(.43,.31,.30),boots,.065)
tube('Bag leather loop',[(-1.18,1.6,.85),(-1.15,1.56,1.01),(-.94,1.56,1.03),(-.79,1.60,.85)],.014,boots,static,10)

anchors={'master':(-.70,3.1,1.6),'two-shot':(-2.05,1.6,1.44),'embrace':(-2.07,1.7,1.69),'coat':(-2.07,1.05,.83),'flowers':(-3.62,1.35,.49),'alley':(1.83,7.6,1.65),'lamp':(lx,2.05,lz)}
for key,point in anchors.items():o=empty('Anchor_'+key,point);o['category']=key
def area(name,pos,target,power,size,c):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=c;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Blue-hour overhead',(.7,3.7,6.8),(.5,3.5,.0),1650,7.5,(.13,.48,.75))
area('Blue alley rim',(3.7,9.0,4.5),(-1.0,3.3,1.2),750,4.0,(.15,.5,.85))
area('Warm bench cinematic key',(-3.5,-.7,3.1),(-2.1,1.6,1.3),170,2.1,(1,.64,.30))
area('Quiet camera fill',(1.0,-4.5,3.0),(-2,1.6,1.4),80,4.5,(.31,.48,.61))
practical=[(lx,2.1,lz-.16),(-.05,5.3,3.28),(3.71,8.42,3.65)]
for i,point in enumerate(practical):
 d=bpy.data.lights.new('Night practical %d'%i,'POINT');d.energy=95 if i==0 else 25;d.shadow_soft_size=.12;d.color=(1,.64,.26);o=bpy.data.objects.new(d.name,d);bpy.context.collection.objects.link(o);o.location=point
world=bpy.data.worlds.new('Blue hour atmosphere');world.use_nodes=True;bpy.context.scene.world=world;world.node_tree.nodes['Background'].inputs[0].default_value=(.012,.043,.071,1);world.node_tree.nodes['Background'].inputs[1].default_value=.30
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=3
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=1600;scene.render.resolution_y=670;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
d=bpy.data.cameras.new('NightAlleyCamera');cam=bpy.data.objects.new('NightAlleyCamera',d);bpy.context.collection.objects.link(cam);cam.location=(2.9,-10.9,2.85);cam.rotation_euler=(Vector((-.65,3.1,1.68))-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=35;scene.camera=cam
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'night-alley.blend'))
print('NIGHT_MODEL_READY',len(static),len(live),flush=True)
# Static lighting and weathering in a compact 2K texture; lanterns remain separate.
combined=join(static,'NightAlley_Baked_Static');bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(67),island_margin=.0025);bpy.ops.object.mode_set(mode='OBJECT');combined.data.uv_layers.active.name='BakedUV'
img=bpy.data.images.new('night-alley-baked',width=2048,height=2048,alpha=False)
for material in combined.data.materials:
 if material:node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;node.select=True;material.node_tree.nodes.active=node
bpy.context.view_layer.objects.active=combined;combined.select_set(True);scene.render.bake.use_clear=True;scene.render.bake.margin=4
bpy.ops.object.bake(type='COMBINED');img.filepath_raw=str(ASSETS/'night-alley-baked.jpg');img.file_format='JPEG';img.save()
baked=mat('NightAlley_Cycles_Baked_Atlas',(1,1,1),1);node=baked.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;baked.node_tree.links.new(node.outputs['Color'],baked.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);combined.data.materials.clear();combined.data.materials.append(baked)
for p in combined.data.polygons:p.material_index=0
print('NIGHT_BAKE_READY',flush=True)
# Runtime renders the atlas unlit; mirror that interpretation for the preview.
p=baked.node_tree.nodes.get('Principled BSDF');link=next(l for l in baked.node_tree.links if l.to_socket==p.inputs['Base Color']);baked.node_tree.links.remove(link);p.inputs['Base Color'].default_value=(0,0,0,1);baked.node_tree.links.new(node.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=1
scene.render.filepath=str(OUT/'night-alley-preview.png');bpy.ops.render.render(write_still=True)
for link in list(baked.node_tree.links):
 if link.to_socket==p.inputs['Emission Color']:baked.node_tree.links.remove(link)
p.inputs['Emission Strength'].default_value=0;baked.node_tree.links.new(node.outputs['Color'],p.inputs['Base Color'])
for o in list(bpy.data.objects):
 if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
# The receding street is a separate geometric background for the stage reveal.
bpy.ops.object.select_all(action='DESELECT');combined.select_set(True);bpy.context.view_layer.objects.active=combined
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for face in combined.data.polygons:face.select=(combined.matrix_world @ face.center).y>4.05
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
background=next(o for o in bpy.context.selected_objects if o!=combined);background.name='Backdrop_NightAlley';background['background']=True
# Keep the editable architecture intact, while reducing redundant bevel segments
# in the website meshes after the baked weathering and shadows are finished.
for surface in [combined,background]:
 bpy.ops.object.select_all(action='DESELECT');surface.select_set(True);bpy.context.view_layer.objects.active=surface
 modifier=surface.modifiers.new('Website bevel simplification','DECIMATE');modifier.ratio=.60;modifier.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=modifier.name)
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(ASSETS/'night-alley.glb'),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False,export_materials='EXPORT',export_apply=True)
# glTF cannot translate procedural noise: retain its intended linear base colour.
export_file=ASSETS/'night-alley.glb';glb=export_file.read_bytes();json_size=struct.unpack_from('<I',glb,12)[0];gltf=json.loads(glb[20:20+json_size])
for material in gltf.get('materials',[]):
 runtime=material.setdefault('pbrMetallicRoughness',{});original=bpy.data.materials.get(material.get('name',''))
 if original and 'baseColorTexture' not in runtime and 'baseColorFactor' not in runtime:runtime['baseColorFactor']=list(original.diffuse_color)
chunk=json.dumps(gltf,separators=(',',':')).encode();chunk+=b' '*((-len(chunk))%4);binary=glb[20+json_size:];export_file.write_bytes(struct.pack('<III',0x46546c67,2,20+len(chunk)+len(binary))+struct.pack('<II',len(chunk),0x4e4f534a)+chunk+binary)
# Compact attribute encoding supported directly by the bundled GLTFLoader.
# Position precision is 1/1024 metre; UVs retain 16-bit normalized precision.
glb=export_file.read_bytes();json_size=struct.unpack_from('<I',glb,12)[0];gltf=json.loads(glb[20:20+json_size]);bin_length=struct.unpack_from('<I',glb,20+json_size)[0];oldbin=glb[28+json_size:28+json_size+bin_length]
attribute_ids={key:{primitive['attributes'][key] for model in gltf['meshes'] for primitive in model['primitives'] if key in primitive['attributes']} for key in ['POSITION','NORMAL','TEXCOORD_0']}
replacement={}
for key,ids in attribute_ids.items():
 for ai in sorted(ids):
  accessor=gltf['accessors'][ai];vi=accessor['bufferView'];view=gltf['bufferViews'][vi]
  if accessor['componentType']!=5126:continue
  assert all(a.get('bufferView')!=vi or a is accessor for a in gltf['accessors'])
  count=3 if key in ['POSITION','NORMAL'] else 2;stride=view.get('byteStride',count*4);start=view.get('byteOffset',0)+accessor.get('byteOffset',0);encoded=bytearray();values=[]
  for i in range(accessor['count']):
   value=struct.unpack_from('<%df'%count,oldbin,start+i*stride)
   if key=='POSITION':
    q=[round(v*1024) for v in value];assert max(q)<32768 and min(q)>=-32768;encoded.extend(struct.pack('<4h',*q,0));values.append(q)
   elif key=='NORMAL':encoded.extend(struct.pack('<4b',*[max(-127,min(127,round(v*127))) for v in value],0))
   else:
    assert min(value)>=-.00001 and max(value)<=1.00001
    encoded.extend(struct.pack('<2H',*[max(0,min(65535,round(v*65535))) for v in value]))
  replacement[vi]=bytes(encoded);view['byteStride']=8 if key=='POSITION' else 4;accessor['byteOffset']=0;accessor['componentType']=5122 if key=='POSITION' else 5120 if key=='NORMAL' else 5123
  if key=='POSITION':
   accessor.pop('normalized',None);accessor['min']=[min(v[i] for v in values) for i in range(3)];accessor['max']=[max(v[i] for v in values) for i in range(3)]
  else:accessor['normalized']=True;accessor.pop('min',None);accessor.pop('max',None)
for node in gltf['nodes']:
 if 'mesh' in node:
  if 'matrix' in node:
   for i in list(range(0,3))+list(range(4,7))+list(range(8,11)):node['matrix'][i]/=1024
  else:node['scale']=[s/1024 for s in node.get('scale',[1,1,1])]
newbin=bytearray()
for vi,view in enumerate(gltf['bufferViews']):
 while len(newbin)%4:newbin.append(0)
 data=replacement.get(vi,oldbin[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);view['byteOffset']=len(newbin);view['byteLength']=len(data);newbin.extend(data)
while len(newbin)%4:newbin.append(0)
gltf['buffers'][0]['byteLength']=len(newbin)
for key in ['extensionsUsed','extensionsRequired']:
 gltf.setdefault(key,[])
 if 'KHR_mesh_quantization' not in gltf[key]:gltf[key].append('KHR_mesh_quantization')
chunk=json.dumps(gltf,separators=(',',':')).encode();chunk+=b' '*((-len(chunk))%4);export_file.write_bytes(struct.pack('<III',0x46546c67,2,28+len(chunk)+len(newbin))+struct.pack('<II',len(chunk),0x4e4f534a)+chunk+struct.pack('<II',len(newbin),0x004e4942)+newbin)
conv=lambda point:[point[0],point[2],-point[1]]
frames={
 'master':{'position':[2.9,2.85,10.9],'target':[-.65,1.68,-3.1],'focal':35,'angle':'街口右侧 14° · 微俯 5°','scale':'全景'},
 'two-shot':{'position':[-.2,1.72,4.3],'target':[-2.05,1.40,-1.65],'focal':50,'angle':'右侧 17°','scale':'双人中景'},
 'embrace':{'position':[-.70,1.78,3.20],'target':[-2.07,1.65,-1.69],'focal':85,'angle':'右侧 16°','scale':'相依近景'},
 'coat':{'position':[-1.24,1.50,1.75],'target':[-2.07,.85,-1.05],'focal':85,'angle':'俯视 13° · 右侧 17°','scale':'衣襟特写'},
 'flowers':{'position':[-1.48,1.20,1.25],'target':[-3.65,.50,-1.35],'focal':85,'angle':'低机位 · 右侧 40°','scale':'花束特写'},
 'alley':{'position':[1.66,1.68,1.1],'target':[1.80,1.63,-7.70],'focal':35,'angle':'平视 · 街巷纵深','scale':'空镜全景'}
}
objects=[o for o in bpy.data.objects if o.type=='MESH']
info={'source_reference':'IMG_1810.JPG','blender':bpy.app.version_string,'static_parts':len(static),'meshes':len(objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),'glb_bytes':export_file.stat().st_size,'atlas':'night-alley-baked.jpg','atlas_size':2048,'nodes':{'static':'NightAlley_Baked_Static','background':'Backdrop_NightAlley','actors':[],'practical':'PracticalLampGlow'},'encoding':'KHR_mesh_quantization, 1/1024 metre positions; normalized signed-byte normals and 16-bit UVs','anchors_gltf_y_up':{key:conv(value) for key,value in anchors.items()},'frames_gltf_y_up':frames,'home':frames['master'],'practical_lights_gltf':[{'position':conv(point),'color':'#ffc16f','intensity':18 if i==0 else 6} for i,point in enumerate(practical)],'key':{'position':[-3.5,3.1,.7],'target':[-2.1,1.3,-1.6],'color':'#ffcd92','intensity':3.0},'note':'Actual cobbled alley, six constructed facades with sculpted door arches, panelled doors, shutter slats, ironwork lanterns, curled bench, flowers and an empty bench with a folded scarf and letter. No photograph backdrop.'}
(ASSETS/'night-alley-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));shutil.copy2(export_file,OUT/'night-alley.glb');shutil.copy2(__file__,OUT/'build_night_alley.py');print('NIGHT_EXPORT_READY',json.dumps(info),flush=True)
