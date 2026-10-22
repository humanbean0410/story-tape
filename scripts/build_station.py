"""Hasedera waiting platform, reconstructed as editable Blender geometry.
The three photographic crops are surface graphics on modeled notice/sign boards;
no photograph is used as the scene/background. CPU Cycles bakes the architecture.
Run: Blender --background --factory-startup --python build_station.py -- SITE OUTPUTS
"""
import bpy,bmesh,math,random,json,sys,shutil
from pathlib import Path
from mathutils import Vector
random.seed(44)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
base=Path(__file__).resolve().parents[1]
SITE=Path(args[0]).resolve() if args else (base if (base/'dist').is_dir() else base/'casa')
OUT=Path(args[1]).resolve() if len(args)>1 else SITE.parent.parent/'outputs'
REF=SITE/'scripts/station-textures';ASSETS=SITE/'dist/assets'
ASSETS.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
architecture=[];live=[];forest=[]

def mat(name,color,rough=.7,metal=0,noise=0,scale=50):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if noise:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*[c*(1-noise) for c in color],1);ramp.color_ramp.elements[1].color=(*[min(1,c*(1+noise)) for c in color],1)
  l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.012
  l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
 return m
cement=mat('Platform weathered concrete',(.23,.23,.205),noise=.3,scale=110)
steel=mat('Old turquoise steel',(.115,.26,.28),rough=.62,metal=.38,noise=.35)
rust=mat('Rust at iron joints',(.075,.026,.011),noise=.7,scale=32)
black=mat('Dark truss iron',(.065,.064,.052),metal=.25,noise=.5)
cream=mat('Molded ivory seat',(.58,.53,.36),rough=.22)
cream2=mat('Seat aged ivory',(.48,.46,.33),rough=.26)
metal=mat('Galvanised seat support',(.22,.24,.23),rough=.35,metal=.68)
blue=mat('Glazed blue-green roof tile',(.135,.37,.405),rough=.24,metal=.06,noise=.22,scale=23)
blue2=mat('Roof tile deep patina',(.07,.255,.29),rough=.3,noise=.4)
blue3=mat('Roof tile light weathering',(.23,.46,.47),rough=.33)
wood=mat('Notice board aged timber',(.24,.17,.105),noise=.4,scale=10)
ivory=mat('Station sign pale backing',(.74,.71,.59),rough=.55)
glass=mat('NoticeBoardGlass',(.31,.36,.34),rough=.1,metal=.12)
p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Alpha'].default_value=.12
try:glass.surface_render_method='DITHERED'
except:pass
yellow=mat('Tactile ochre paving',(.66,.40,.055),noise=.12,scale=65)
rail=mat('Rail polished steel',(.22,.24,.24),rough=.26,metal=.8)
stone=mat('Ballast gray',(.14,.15,.14),noise=.5)
sleep=mat('Rail sleeper timber',(.08,.075,.055),noise=.4,scale=14)
wall=mat('Roofed house pale blue wall',(.29,.39,.40),rough=.75,noise=.2)
bark=mat('Cherry bark',(.105,.071,.053),rough=.88,noise=.45)
trainGreen=mat('Train deep forest green',(.055,.17,.10),rough=.28,metal=.25)
trainCream=mat('Train cream waist',(.73,.68,.52),rough=.35,metal=.15)
trainGlass=mat('Train blue tinted window',(.10,.22,.25),rough=.15,metal=.5)
red=mat('Train tail lamp',(.56,.035,.015),rough=.28)
petals=[mat('Cherry petal %02d'%i,c,rough=.63) for i,c in enumerate([(.91,.80,.81),(.84,.72,.76),(.94,.90,.84),(.72,.61,.66),(.99,.93,.92)])]
leaves=[mat('Forest crown %02d'%i,(.036+i*.010,.095+i*.014,.070+i*.008),rough=.9) for i in range(9)]
terrainm=[mat('Mountain ridge %02d'%i,(.055+i*.016,.13+i*.014,.11+i*.014),rough=1) for i in range(5)]

def reg(o,m,group=architecture):
 if m:o.data.materials.append(m)
 group.append(o);return o

def mesh(name,verts,faces,m,group=architecture,uvs=None):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update()
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
 if uvs:
  uv=d.uv_layers.new(name='UVMap')
  for poly in d.polygons:
   for li in poly.loop_indices:uv.data[li].uv=uvs[d.loops[li].vertex_index]
 return reg(o,m,group)

def cube(name,pos,size,m,bevel=.012,group=architecture):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=2,affect='EDGES',clamp_overlap=True)
 d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();d.update()
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos
 return reg(o,m,group)

def beam(name,a,b,r,m,group=architecture,n=8):
 a=Vector(a);b=Vector(b);v=b-a;w=v.normalized();u=w.cross(Vector((0,0,1)))
 if u.length<.01:u=w.cross(Vector((0,1,0)))
 u.normalize();q=w.cross(u)
 vs=[tuple(p+r*(math.cos(i*2*math.pi/n)*u+math.sin(i*2*math.pi/n)*q)) for p in [a,b] for i in range(n)]
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh(name,vs,fs,m,group)
 for f in o.data.polygons:f.use_smooth=True
 return o

def ico(name,pos,r,m,group=forest,scale=(1,1,1),sub=1):
 bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=sub,radius=r)
 for v in bm.verts:v.co.x=v.co.x*scale[0]+pos[0];v.co.y=v.co.y*scale[1]+pos[1];v.co.z=v.co.z*scale[2]+pos[2]
 d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
 for p in d.polygons:p.use_smooth=True
 return reg(o,m,group)

def join_group(objs,name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 return o

def texture_mat(name,path):
 m=mat(name,(1,1,1),.75)
 im=bpy.data.images.load(str(path));im.pack();n=m.node_tree.nodes;l=m.node_tree.links
 tex=n.new('ShaderNodeTexImage');tex.image=im;l.new(tex.outputs['Color'],n.get('Principled BSDF').inputs['Base Color'])
 return m

def front(name,cx,y,cz,w,h,m,group=live):
 return mesh(name,[(cx-w/2,y,cz-h/2),(cx+w/2,y,cz-h/2),(cx+w/2,y,cz+h/2),(cx-w/2,y,cz+h/2)],[(0,1,2,3)],m,group,[(0,0),(1,0),(1,1),(0,1)])

# Thick elevated platform and railway: the foreground remains tangible in closeup.
cube('Platform foundation',(0,.45,-.045),(15.4,5.2,.46),cement,.03)
cube('Platform worn rim',(0,-2.16,.24),(15.5,.18,.20),cement,.02)
for row in range(3):
 for col in range(46):
  x=-7.4+col*.33;y=-1.91+row*.16
  cube('Tactile warning tile',(x,y,.202),(.32,.148,.028),yellow,.007)
  for dx in [-.105,0,.105]:
   for dy in [-.043,.043]:cube('Tactile raised dot',(x+dx,y+dy,.225),(.035,.035,.015),yellow,.006)
# Directional tactile strip through the right columns.
for i in range(17):
 y=-1.63+i*.24
 cube('Tactile route tile',(4.85,y,.207),(.31,.23,.025),yellow,.006)
 for x in [4.76,4.85,4.94]:cube('Tactile longitudinal rib',(x,y,.227),(.028,.216,.015),yellow,.005)
# Expansion joints and patched floor wear.
for x in [-6,-3,0,3,6]:cube('Concrete slab joint',(x,.35,.196),(.008,4.50,.004),black,0)
for y in [-.5,1.3]:cube('Concrete slab joint',(0,y,.196),(15,.008,.004),black,0)
for i in range(55):
 x=random.uniform(-7.2,7.2);y=random.uniform(-1.5,2.4)
 cube('Floor age fleck',(x,y,.201),(random.uniform(.02,.15),random.uniform(.01,.035),.002),stone,0)
cube('Track ballast',(0,-3.7,-.23),(25,2.75,.24),stone,.02)
for x in [-11.5+i*.54 for i in range(45)]:cube('Rail sleeper',(x,-3.7,-.06),(.16,2.1,.15),sleep,.01)
for y in [-4.4,-2.95]:
 cube('Rail web',(0,y,.07),(25,.055,.18),rail,.007)
 cube('Rail head',(0,y,.17),(25,.087,.045),rail,.012)
for i in range(110):ico('Ballast stone',(random.uniform(-11,11),random.uniform(-4.9,-2.55),-.06),random.uniform(.04,.09),stone,architecture,scale=(1.4,1,.65))

# Shelter: structural uprights, bolts, triangular steel webs and corrugated roof.
for x in [-6.75,4.72,5.58,6.8]:
 y=.92 if x>4 else 1.48
 cube('Steel column flange',(x,y,2.10),(.17,.23,3.84),steel,.009)
 cube('Steel column base',(x,y,.275),(.40,.42,.13),metal,.008)
 cube('Steel column vertical web',(x,y,2.05),(.07,.34,3.75),steel,.006)
 for z in [.43,1.6,3.58]:
  for dx in [-.085,.085]:ico('Column rivet',(x+dx,y-.181,z),.025,metal,architecture,sub=1)
 for i in range(15):
  z=random.uniform(.6,3.5);xx=x+random.uniform(-.07,.07)
  cube('Column peeling rust',(xx,y-.181,z),(random.uniform(.025,.075),.007,random.uniform(.045,.30)),rust,.004)
 for side in [-1,1]:beam('Shelter curved support brace',(x,y,2.9),(x+side*.70,y,3.85),.052,black)
# Roof visible underneath, rather than a flat horizon plane.
cube('Shelter dark roof underside',(0,.56,4.06),(15.0,5.52,.16),black,.018)
cube('Shelter front fascia',(0,-2.22,3.98),(15.05,.15,.28),rust,.012)
cube('Shelter rear eaves',(0,3.32,4.02),(15.05,.12,.18),steel,.01)
for x in [-7.25+i*.49 for i in range(31)]:cube('Shelter corrugated roof rib',(x,.52,4.172),(.095,5.45,.085),steel,.014)
for y in [-1.98,1.32,2.88]:
 cube('Truss upper chord',(0,y,3.94),(14.65,.07,.065),black,.003)
 cube('Truss lower chord',(0,y,3.60),(14.65,.075,.075),black,.004)
 for i in range(34):
  x=-7.25+i*.43
  beam('Triangular truss web',(x,y,3.61),(x+.22,y,3.94),.023,black)
  beam('Triangular truss web',(x+.22,y,3.94),(x+.43,y,3.61),.023,black)
for x in [-5.8,-2.7,.3,3.5,6.2]:cube('Roof transverse bearer',(x,.51,3.88),(.08,5.2,.16),black,.006)
# Warm fluorescent fittings; runtime may animate these standard-mat meshes.
lampmat=mat('Station fluorescent diffuser',(.85,.88,.78),.2)
p=lampmat.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.85,.91,.83,1);p.inputs['Emission Strength'].default_value=.35
for x in [-3.1,2.6]:
 cube('Shelter lamp casing',(x,.26,3.73),(1.50,.26,.085),steel,.015)
 cube('StationTubeLamp',(x,.26,3.676),(1.32,.13,.028),lampmat,.009,live)

# Rear guardrail separates the foreground stage from tiled roofs and blossom layers.
for z in [.64,1.94]:beam('Railing horizontal tube',(-7.4,2.18,z),(7.4,2.18,z),.034,steel)
for x in [-7.35+i*.44 for i in range(34)]:beam('Railing vertical picket',(x,2.18,.31),(x,2.18,1.94),.019,steel)
for x in [-7.4,-3.7,0,3.7,7.4]:beam('Railing upright',(x,2.18,.25),(x,2.18,2.01),.042,steel)
# Slight dents and old turquoise paint expose rust in the tube joints.
for x in [-5.4,-1.4,3.4,6.5]:beam('Railing rusty joint',(x,2.175,1.94),(x+.11,2.175,1.94),.037,rust)

# Seven molded shell chairs: a continuous compound curved shell, not boxes.
cube('Seat shared crossbeam',(-1.14,.38,.61),(5.75,.105,.085),metal,.012)
for x in [-3.52,-1.15,1.22]:
 for y in [.17,.61]:beam('Seat metal support leg',(x,y,.22),(x,y,.63),.035,metal)
 beam('Seat metal leg foot',(x,-.02,.225),(x,.78,.225),.039,metal)
section=[(-.36,.71,.30),(-.33,.67,.31),(-.22,.64,.31),(-.05,.64,.32),(.14,.68,.31),(.29,.78,.30),(.35,1.04,.29),(.40,1.30,.26),(.37,1.40,.22)]
for i in range(7):
 cx=-3.54+i*.80;cy=.34;verts=[];faces=[];across=16;th=.026
 for side in [0,1]:
  for y,z,halfwidth in section:
   for k in range(across+1):
    t=-1+2*k/across;xx=t*halfwidth
    # Deep bowl, raised sides and rounded top corners.
    zz=z+(-.065 if z>1.35 else .045)*t*t-(th if side else 0)
    yy=y+(.018*t*t)+(th*.5 if side else 0)
    verts.append((cx+xx,cy+yy,zz))
 stride=across+1;rows=len(section);off=stride*rows
 for side in [0,1]:
  for j in range(rows-1):
   for k in range(across):
    a=side*off+j*stride+k;f=(a,a+1,a+1+stride,a+stride)
    faces.append(f if side==0 else tuple(reversed(f)))
 for j in range(rows-1):
  for k in [0,across]:
   a=j*stride+k;b=a+stride;faces.append((a,b,b+off,a+off))
 for j in [0,rows-1]:
  for k in range(across):
   a=j*stride+k;faces.append((a,a+off,a+off+1,a+1))
 o=mesh('Seat_%02d'%(i+1),verts,faces,cream if i%3 else cream2,live);o['effect']='camera-seat';o['seat_index']=i
 for f in o.data.polygons:f.use_smooth=True
 # Real metal brackets and mounting bolts below the shell.
 cube('Seat under-shell bracket',(cx,.50,.615),(.16,.30,.052),metal,.01)
 for xx in [cx-.115,cx+.115]:ico('Seat fixing bolt',(xx,.18,.682),.014,metal,architecture)
 # Small shadows and gloss edges remain geometry under relighting.

# Notice boards: wooden frame depth + separate reflective panes.
largeGraphic=texture_mat('Authentic photographed timetable',REF/'station-board.png')
noticeGraphic=texture_mat('Authentic photographed notices',REF/'station-notices.png')
signGraphic=texture_mat('Authentic Hasedera station sign',REF/'station-sign.png')
def board(name,cx,y,cz,w,h,graphic):
 cube(name+'_body',(cx,y+.04,cz),(w,.15,h),wood,.015)
 front(name+'_graphic',cx,y-.049,cz,w-.09,h-.10,graphic)
 for x in [cx-w/2,cx+w/2]:cube(name+'_frame',(x,y-.075,cz),(.047,.055,h+.03),metal,.008)
 for z in [cz-h/2,cz+h/2]:cube(name+'_frame',(cx,y-.075,z),(w+.045,.055,.045),metal,.008)
 g=front(name+'Glass',cx,y-.10,cz,w-.09,h-.10,glass);g['effect']='notice-board'
 return g
board('NoticeBoard',-3.11,1.54,2.07,1.56,1.75,largeGraphic)
for x in [-3.69,-2.52]:beam('Tall notice-board support',(x,1.57,.24),(x,1.57,2.1),.039,steel)
board('LowNotice',.38,1.74,1.69,2.80,1.08,noticeGraphic)
for x in [-.73,1.55]:beam('Low notice-board support',(x,1.74,.22),(x,1.74,1.80),.035,steel)
# Suspended station sign: separate object retains its identity for navigation.
cube('Station sign aluminium box',(1.10,1.08,3.12),(2.10,.14,.87),ivory,.018)
stationSign=front('StationSign',1.10,.998,3.12,2.025,.795,signGraphic);stationSign['effect']='next-stage'
for x in [.22,1.98]:beam('Sign suspension rod',(x,1.08,3.56),(x,1.08,3.88),.015,black)
# Photo's weathered right access panel and drain.
cube('Platform right gate panel',(6.54,1.68,1.11),(1.55,.12,1.54),steel,.018)
for x in [5.73,7.33]:beam('Gate rounded frame',(x,1.63,.29),(x,1.63,2.02),.048,steel)
beam('Gate handrail',(5.73,1.63,2.02),(7.33,1.63,2.02),.048,steel)
for x in [4.76,5.60]:
 beam('Rain downpipe',(x,2.74,.27),(x,2.74,3.93),.042,steel)
 for z in [.60,1.75,3.05]:cube('Downpipe metal strap',(x,2.73,z),(.15,.10,.045),rust,.004)

# Two tile-roof buildings beyond the rail: every corrugated tile is actual geometry.
def roof_building(name,cx,cy,width,depth,height):
 cube(name+'_wall',(cx,cy,height/2),(width-.36,depth-.35,height),wall,.015)
 for x in [cx-width*.25,cx+width*.25]:
  cube(name+'_window',(x,cy-depth/2-.014,height*.50),(.78,.015,.88),trainGlass,.005)
  cube(name+'_window_sill',(x,cy-depth/2-.035,height*.5-.46),(.85,.085,.05),ivory,.007)
 cols=int(width/.25);rows=int(depth/.37)
 for side in [-1,1]:
  for row in range(rows//2+1):
   yy=cy+side*(row+.20)*.37;zz=height+.73-row*.155
   for col in range(cols):
    xx=cx-width/2+col*.25;verts=[];faces=[]
    # Concave/convex Japanese S-profile spanning a row, with overlapping lips.
    for j in range(5):
     vy=yy+side*(j/4*.40)
     for k in range(7):
      vx=xx+k/6*.27
      vz=zz-j/4*.166+.037*math.cos(k/6*2*math.pi)
      verts.append((vx,vy,vz))
    for j in range(4):
     for k in range(6):
      a=j*7+k;faces.append((a,a+1,a+8,a+7) if side==1 else (a+7,a+8,a+1,a))
    tile=mesh(name+'_wave_tile',verts,faces,random.choice([blue,blue,blue,blue2,blue3]))
    for p in tile.data.polygons:p.use_smooth=True
  beam(name+'_eave_gutter',(cx-width/2,cy+side*depth/2,height-.09),(cx+width/2,cy+side*depth/2,height-.09),.047,steel)
 for i in range(cols):
  beam(name+'_ridge_cap',(cx-width/2+i*.25,cy,height+.79),(cx-width/2+(i+1)*.25+.02,cy,height+.79),.09,blue,architecture,n=10)
roof_building('Near tiled roof',-.4,5.5,13.5,4.10,1.35)
roof_building('Left higher tiled roof',-6.1,9.55,5.7,5.1,3.4)

# Mountains are layered, irregular 3D terrains. A seeded tree population adds depth.
for band,(cy,amplitude,basez) in enumerate([(15,3.8,.5),(22,5.5,1.8),(31,7.0,3.0)]):
 nx=48;ny=12;verts=[];faces=[]
 for j in range(ny+1):
  for i in range(nx+1):
   x=-29+i*58/nx;y=cy-3+j*.95
   z=basez+amplitude*(.57+.27*math.sin(x*.20+band)+.18*math.sin(x*.51+1.3))*(.25+.75*math.sin(j/ny*math.pi*.78))
   z+=random.uniform(-.3,.3)
   verts.append((x,y,z))
 for j in range(ny):
  for i in range(nx):
   a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
 mount=mesh('MountainLayer_%d'%band,verts,faces,terrainm[band],forest)
 for p in mount.data.polygons:p.use_smooth=True
 for i in range(260):
  x=random.uniform(-25,25);y=random.uniform(cy-.7,cy+7.8)
  zz=basez+amplitude*(.57+.27*math.sin(x*.20+band)+.18*math.sin(x*.51+1.3))*(.25+.75*math.sin((y-cy+3)/11.4*math.pi*.78))
  height=random.uniform(.7,1.6);r=random.uniform(.31,.57)
  # Broadleaf crowns are irregular solid forms, with occasional conifer silhouettes.
  if i%5==0:
   ico('Distant evergreen',(x,y,zz+height*.45),r,random.choice(leaves),forest,scale=(.80,.80,height/r*.80),sub=1)
  else:ico('Distant forest crown',(x,y,zz+height*.35),r,random.choice(leaves),forest,scale=(1,1,height/r*.7),sub=1)
forestCombined=join_group(forest,'LayeredMountainForest');forestCombined['effect']='ambient-landscape';forestCombined['background']=True

# Blossom tree: real trunk/branches and clustered five-petal flowers, spatially separated.
blossoms=[];treepos=(2.0,8.0,.9)
beam('Sakura main trunk',(2.0,8.0,.75),(1.92,8.04,3.46),.17,bark)
for arm in range(8):
 ang=arm*math.tau/8+.2;end=(2+math.cos(ang)*random.uniform(1.1,2.1),8+math.sin(ang)*random.uniform(.8,1.6),random.uniform(2.9,3.85))
 stem=(1.92,8.04,2.7+random.uniform(-.2,.35))
 beam('Sakura major branch',stem,end,.045,bark)
 for twig in range(5):
  tip=(end[0]+random.uniform(-.9,.9),end[1]+random.uniform(-.75,.75),end[2]+random.uniform(-.3,.7))
  beam('Sakura fine twig',end,tip,.013,bark)
  # Irregular cloud of explicit low-poly petals, avoiding a flat sprite canopy.
  for j in range(40):
   p=(tip[0]+random.gauss(0,.26),tip[1]+random.gauss(0,.23),tip[2]+random.gauss(0,.21))
   ico('Sakura flower cluster',p,random.uniform(.08,.16),random.choice(petals),blossoms,scale=(1.1,.8,.72),sub=1)
canopy=join_group(blossoms,'BlossomCanopy');canopy['effect']='wind'
for v in canopy.data.vertices:v.co-=Vector((2.0,8.0,3.85))
canopy.location=(2.0,8.0,3.85);live.append(canopy)
# A smaller distant blossom crown offsets the main tree.
small=[]
beam('Distant cherry trunk',(-4.0,12.6,.6),(-4.2,12.6,3.2),.09,bark)
for i in range(135):ico('Distant cherry cluster',(-4.2+random.gauss(0,1.4),12.6+random.gauss(0,.8),3.35+random.gauss(0,.52)),random.uniform(.07,.17),random.choice(petals),small,sub=1)
smallCombined=join_group(small,'DistantBlossom');live.append(smallCombined)

# The train is a real separate carriage and can pass the set without entering at load.
train=[]
root=bpy.data.objects.new('AnimatedTrain',None);bpy.context.collection.objects.link(root);root.location=(-23,-3.72,.0);root['effect']='train';root['track_axis']='x';root['initial_hidden']=True
cube('Train carriage body',(0,0,1.12),(5.80,1.80,1.80),trainGreen,.14,train)
cube('Train carriage roof',(0,0,2.08),(5.87,1.86,.16),metal,.085,train)
cube('Train cream belt',(0,-.914,1.14),(5.61,.028,.38),trainCream,.01,train)
for y in [-.928,.928]:
 for x in [-2.23,-1.22,-.2,.82,1.88]:
  cube('Train window bezel',(x,y,1.58),(.77,.033,.66),trainCream,.042,train)
  cube('Train window glass',(x,y+(-.021 if y<0 else .021),1.59),(.68,.017,.57),trainGlass,.035,train)
for x in [-2.7,2.7]:
 for y in [-.95,.95]:cube('Train end door frame',(x,y,1.16),(.26,.028,1.6),trainCream,.014,train)
 for y in [-.54,.54]:ico('Train small end lamp',(x+(-.20 if x<0 else .20),y,.86),.08,red,train,scale=(.3,1,1))
for x in [-1.83,1.83]:
 for y in [-.65,.65]:beam('Train wheel',(x,y-.11,.34),(x,y+.11,.34),.24,black,train,n=16)
 cube('Train bogie',(x,0,.38),(.97,1.32,.29),metal,.025,train)
trainmesh=join_group(train,'TrainCarriage');trainmesh.parent=root;live.append(trainmesh)

anchors={'platform':(0,-.30,1.65),'seats':(-1.0,.35,.90),'board':(-3.11,1.44,2.07),'sign':(1.10,.98,3.12),'blossom':(2.0,8.0,3.85),'roof':(0,.35,3.81)}
for key,p in anchors.items():
 o=bpy.data.objects.new('Anchor_'+key,None);bpy.context.collection.objects.link(o);o.location=p;o['category']=key

# CPU render/bake lighting, independent of Three.js runtime lighting.
def area(name,pos,target,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Low afternoon sun',(-7,-5,9),(0,1,1),1900,4,(1,.83,.61))
area('Mountain sky fill',(5,2,9),(0,2,1),1600,10,(.61,.79,.91))
area('Under canopy bounce',(0,-3,4.1),(0,1,1.0),400,6,(.82,.87,.77))
world=bpy.data.worlds.new('Hasedera clear mountain sky');world.use_nodes=True;bpy.context.scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.31,.47,.51,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.cycles.max_bounces=3
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1500;scene.render.resolution_y=850;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
d=bpy.data.cameras.new('StationCamera');cam=bpy.data.objects.new('StationCamera',d);bpy.context.collection.objects.link(cam)
cam.location=(.25,-12.7,3.15);cam.rotation_euler=(Vector((0,2.30,2.25))-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=39;scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hasedera-station.blend'))
print('MODEL_READY architecture',len(architecture),'live',len(live),flush=True)
# One daylight atlas, architecture only. Forest, blossoms, glass and chairs relight live.
combined=join_group(architecture,'Station_Baked_Static')
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.003);bpy.ops.object.mode_set(mode='OBJECT')
combined.data.uv_layers.active.name='BakedUV'
img=bpy.data.images.new('station-day-baked',width=2048,height=2048,alpha=False)
for m in combined.data.materials:
 if m:
  n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;n.select=True;m.node_tree.nodes.active=n
bpy.context.view_layer.objects.active=combined;combined.select_set(True)
scene.render.bake.use_clear=True;scene.render.bake.margin=5
bpy.ops.object.bake(type='COMBINED')
img.filepath_raw=str(ASSETS/'station-day-baked.jpg');img.file_format='JPEG';img.save()
baked=mat('Station_Cycles_Baked_Atlas',(1,1,1),1)
n=baked.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;baked.node_tree.links.new(n.outputs['Color'],baked.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
combined.data.materials.clear();combined.data.materials.append(baked)
for p in combined.data.polygons:p.material_index=0
bpy.context.view_layer.objects.active=combined
mod=combined.modifiers.new('Web delivery reduction','DECIMATE');mod.ratio=.50
bpy.ops.object.modifier_apply(modifier=mod.name)
print('BAKED station-day-baked',flush=True)
scene.render.filepath=str(OUT/'hasedera-station-day.png');bpy.ops.render.render(write_still=True)
for o in list(bpy.data.objects):
 if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'hasedera-station.glb'),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False,export_materials='EXPORT',export_apply=True)
meshobjects=[o for o in bpy.data.objects if o.type=='MESH']
stats={'blender':bpy.app.version_string,'architecture_parts':len(architecture),'meshes':len(meshobjects),'vertices':sum(len(o.data.vertices) for o in meshobjects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshobjects),'glb_bytes':(ASSETS/'hasedera-station.glb').stat().st_size,'atlas_size':2048,'anchors_blender_z_up':anchors,'anchors_gltf_y_up':{k:[p[0],p[2],-p[1]] for k,p in anchors.items()},'home_gltf':{'position':[.25,3.15,12.7],'target':[0,2.25,-2.3],'fov':42},'focus_gltf':{'seats':{'position':[-1.1,1.7,4.4],'target':[-1.1,.92,-.35]},'board':{'position':[-3.11,2.2,2.6],'target':[-3.11,2.07,-1.44]},'sign':{'position':[1.1,3.1,3.1],'target':[1.1,3.12,-.98]},'blossom':{'position':[2,2.9,-3.8],'target':[2,3.85,-8]},'roof':{'position':[-.4,2.8,2.2],'target':[0,3.81,-.35]}},'nodes':{'static':'Station_Baked_Static','forest':'LayeredMountainForest','seats':['Seat_%02d'%(i+1) for i in range(7)],'blossoms':['BlossomCanopy','DistantBlossom'],'notice_glass':'NoticeBoardGlass','station_sign':'StationSign','train_root':'AnimatedTrain'},'atlas':'station-day-baked.jpg','note':'All scene volumes modeled in Blender. Only authentic sign/notice lettering uses local surface crops.'}
(SITE.parent/'model/station-notes.json').write_text(json.dumps(stats,indent=2))
(ASSETS/'station-model-info.json').write_text(json.dumps(stats,indent=2))
shutil.copy2(ASSETS/'hasedera-station.glb',OUT/'hasedera-station.glb')
for target in [SITE/'scripts/build_station.py',OUT/'build_station.py']:
 if Path(__file__).resolve()!=target.resolve():shutil.copy2(__file__,target)
print('EXPORT_READY',json.dumps(stats),flush=True)
