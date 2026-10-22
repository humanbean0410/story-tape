"""Editable vintage lounge set, reconstructed from IMG_1837.JPG.
Geometry, procedural surface materials and generic adult performers; no photo plane.
Blender --background --factory-startup --python build_interior.py -- SITE OUTPUTS
"""
import bpy,bmesh,math,random,json,sys,shutil,struct
from pathlib import Path
from mathutils import Vector
random.seed(1837)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
SITE=Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
OUT=Path(args[1]).resolve() if len(args)>1 else SITE.parent.parent/'outputs'
ASSETS=SITE/'dist/assets';NOTES=SITE.parent/'model'
ASSETS.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True);NOTES.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
static=[];live=[];foliage=[]

def mat(name,c,rough=.6,metal=0,noise=0,scale=40):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if noise:
  t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=scale;t.inputs['Detail'].default_value=3
  r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(*[v*(1-noise) for v in c],1);r.color_ramp.elements[1].color=(*[min(1,v*(1+noise)) for v in c],1)
  l.new(t.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])
  b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.14;b.inputs['Distance'].default_value=.008;l.new(t.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
 return m
mahogany=mat('Rubbed dark red mahogany',(.125,.036,.022),.28,noise=.3,scale=8)
woodedge=mat('Mahogany polished edges',(.21,.065,.03),.25,noise=.25,scale=9)
woodblack=mat('Slatted bench dark recess',(.045,.022,.009),.5)
parquet=[mat('Oak parquet %02d'%i,(.22+.018*i,.115+.008*i,.045+.005*i),.43,noise=.32,scale=16) for i in range(8)]
ochre=mat('Faded ochre wallpaper',(.49,.31,.105),.88,noise=.1,scale=130)
creamwall=mat('Pale stripe aged wallpaper',(.62,.48,.27),.94,noise=.14,scale=70)
plaster=mat('Lime plaster warm cream',(.53,.43,.29),.85,noise=.12,scale=160)
cream=mat('Old ivory shutter paint',(.65,.57,.39),.48,noise=.07)
brass=mat('Tarnished antique brass',(.34,.20,.062),.37,.65,noise=.18)
gold=mat('Worn gilded wallpaper motif',(.50,.32,.125),.86,noise=.10)
bronze=mat('Sconce rubbed bronze',(.10,.075,.038),.35,.6)
pipe=mat('Ceiling cream painted pipe',(.19,.18,.13),.67,noise=.12)
linen=mat('Linen lampshade',(.80,.64,.38),.87,noise=.09,scale=180)
upholstery=mat('Ivory floral woven upholstery',(.54,.44,.29),.98,noise=.14,scale=210)
floral=mat('Cushion burgundy embroidered flowers',(.23,.13,.082),.98)
olive=mat('Deep olive velvet pillow',(.12,.15,.055),.96,noise=.11,scale=150)
teal=mat('Faded teal velvet pillow',(.10,.145,.115),.92,noise=.16,scale=170)
black=mat('Dark metal shadow',(.017,.018,.012),.4,.2)
leafm=[mat('Banana leaf %02d'%i,(.048+.009*i,.105+.019*i,.036+.007*i),.71) for i in range(6)]
leafvein=mat('Leaf raised vein',(.18,.22,.075),.79)
soil=mat('Plant pot soil',(.048,.023,.012),.97)
clay=mat('Aged green ceramic pot',(.13,.17,.097),.31,noise=.18)
windowwood=mat('Window center pale frame',(.29,.25,.14),.48)
glass=mat('Window glass low reflection',(.31,.43,.29),.10,.15)
p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Alpha'].default_value=.16
try:glass.surface_render_method='DITHERED'
except:pass
bulbmat=mat('InteriorPracticalGlow',(.94,.70,.32),.28)
p=bulbmat.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.69,.29,1);p.inputs['Emission Strength'].default_value=2.0
navy=mat('Performer navy knitted sweater',(.025,.035,.054),.96,noise=.10,scale=200)
whitecloth=mat('Performer ivory cotton trousers',(.72,.68,.57),.91,noise=.07,scale=170)
shirt=mat('Performer clean shirt collar',(.83,.81,.71),.91)
slate=mat('Performer gray wool jacket',(.245,.255,.22),.92,noise=.11,scale=180)
skirt=mat('Performer brown tweed skirt',(.255,.165,.084),.94,noise=.16,scale=220)
boots=mat('Performer black leather boots',(.025,.023,.018),.34)
shoe=mat('Performer canvas sneakers',(.51,.49,.42),.93)
sole=mat('Performer rubber soles',(.75,.69,.57),.82)
skin=mat('Warm natural skin',(.59,.36,.225),.76)
p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.09
hair=mat('Dark chocolate hair',(.035,.020,.012),.69)
hairlight=mat('Hair soft ridge',(.068,.039,.024),.65)
eye=mat('Eyes warm dark brown',(.027,.013,.006),.33)
eyewhite=mat('Subtle eye sclera',(.58,.53,.45),.68)
lip=mat('Muted terracotta lips',(.34,.125,.093),.84)


def reg(o,m,group=static):
 if m:o.data.materials.append(m)
 group.append(o);return o

def mesh(name,vs,fs,m,group=static,uv=None):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
 if uv:
  u=d.uv_layers.new(name='UVMap')
  for f in d.polygons:
   for li in f.loop_indices:u.data[li].uv=uv[d.loops[li].vertex_index]
 return reg(o,m,group)

def cube(name,pos,size,m,bevel=.014,group=static):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=3,affect='EDGES',clamp_overlap=True)
 d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;d.update();return reg(o,m,group)

def ellipsoid(name,pos,radii,m,group=static,seg=24,rings=16):
 vs=[];fs=[]
 for j in range(rings+1):
  t=math.pi*j/rings
  for i in range(seg):
   a=2*math.pi*i/seg;vs.append((pos[0]+radii[0]*math.sin(t)*math.cos(a),pos[1]+radii[1]*math.sin(t)*math.sin(a),pos[2]+radii[2]*math.cos(t)))
 for j in range(rings):
  for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,a+seg,b+seg,b))
 o=mesh(name,vs,fs,m,group)
 for f in o.data.polygons:f.use_smooth=True
 return o

def tube(name,points,radii,m,group=static,seg=12):
 vs=[];fs=[]
 for j,p in enumerate(points):
  p=Vector(p);v=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
  v.normalize();u=v.cross(Vector((0,0,1)))
  if u.length<.01:u=v.cross(Vector((0,1,0)))
  u.normalize();w=v.cross(u);r=radii[j] if isinstance(radii,(tuple,list)) else radii
  if isinstance(r,(tuple,list)):rx,ry=r
  else:rx=ry=r
  for i in range(seg):a=2*math.pi*i/seg;vs.append(tuple(p+rx*math.cos(a)*u+ry*math.sin(a)*w))
 for j in range(len(points)-1):
  for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
 fs.extend([tuple(range(seg-1,-1,-1)),tuple((len(points)-1)*seg+i for i in range(seg))]);o=mesh(name,vs,fs,m,group)
 for f in o.data.polygons:f.use_smooth=True
 return o

def beam(name,a,b,r,m,group=static,n=12):return tube(name,[a,b],r,m,group,n)
def join(objs,name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;return o

def empty(name,pos=(0,0,0)):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=pos;return o

def leaf(name,a,b,width,m,group=foliage,banana=False):
 a=Vector(a);b=Vector(b);direction=b-a;side=direction.cross(Vector((0,0,1))).normalized();verts=[];faces=[];N=18
 for j in range(N+1):
  t=j/N;center=a+direction*t+Vector((0,0,.24*math.sin(math.pi*t)));half=width*(math.sin(math.pi*t)**.68)
  for k in range(5):
   f=(k-2)/2;pos=center+side*half*f;pos.z+=.085*(1-abs(f))*math.sin(math.pi*t)-.055*abs(f)*math.sin(j*.7)
   verts.append(tuple(pos))
 for j in range(N):
  for k in range(4):q=j*5+k;faces.append((q,q+1,q+6,q+5))
 o=mesh(name,verts,faces,m,group)
 for p in o.data.polygons:p.use_smooth=True
 beam(name+' central vein',tuple(a),tuple(b),.009,leafvein,group,8)
 if banana:
  for j in range(2,N,2):
   t=j/N;c=a+direction*t+Vector((0,0,.24*math.sin(math.pi*t)));w=width*math.sin(math.pi*t)**.68
   for s in [-1,1]:beam('Banana fine leaf rib',tuple(c),tuple(c+side*w*s+direction*.06),.0035,leafvein,group,6)
 return o

# A physical three-wall set, open at the camera side.
cube('Room foundation',(0,0,-.15),(9.8,5.9,.25),woodblack,.03)
for j in range(22):
 for i in range(16):
  # Staggered real parquet boards with visible bevel joints.
  x=-4.72+i*.61+(j%2)*.305;y=-2.80+j*.265
  if x>4.7:continue
  cube('Parquet plank',(x,y,.011),(.595,.25,.052),random.choice(parquet),.009)
# Back aperture is genuinely open to the geometric garden.
# Build wall left/right as panels with a large central physical window aperture.
for x,w in [(-3.77,2.25),(3.77,2.25)]:
 cube('Wall paper backing',(x,2.56,2.18),(w,.12,3.93),ochre,.006)
 for dx in [x-.72,x,x+.72]:cube('Cream wallpaper stripe',(dx,2.485,2.18),(.265,.012,3.93),creamwall,.002)
# Window top lintel and bottom wall.
cube('Wallpaper above window',(0,2.52,3.77),(5.4,.15,.72),ochre,.008)
cube('Wallpaper below window',(0,2.52,.52),(5.4,.15,1.05),ochre,.008)
for x in [-4.90,4.90]:
 cube('Side cut wall',(x,.03,2.04),(.14,5.23,4.08),ochre,.012)
 cube('Side dark dado',(x-.08*(1 if x>0 else -1),.03,.55),(.035,5.23,1.06),mahogany,.005)
# True panelled dark wainscot across wall and sides.
for x in [-4.15,-3.42,-2.69,-1.96,-1.23,-.50,.23,.96,1.69,2.42,3.15,3.88,4.61]:
 cube('Dado raised panel',(x,2.425,.52),(.665,.085,.84),mahogany,.017)
 for dx in [-.29,.29]:cube('Dado panel stile',(x+dx,2.356,.52),(.055,.025,.79),woodedge,.005)
 for z in [.16,.88]:cube('Dado panel rail',(x,2.35,z),(.625,.028,.045),woodedge,.005)
for z in [.04,1.02]:cube('Dado continuous moulding',(0,2.34,z),(9.8,.15,.10),woodedge,.015)
# Wallpaper vine motifs deliberately made as relief geometry.
for cx in [-4.45,-3.02,3.00,4.42]:
 for cz in [1.57,2.62,3.60]:
  for s in [-1,1]:
   points=[(cx,2.471,cz-.28),(cx+s*.05,2.468,cz-.12),(cx+s*.11,2.465,cz+.05),(cx+s*.08,2.468,cz+.21)]
   tube('Faded gilded vine',points,.006,gold,static,6)
   for dz in [-.10,.04,.17]:ellipsoid('Wallpaper acanthus leaf',(cx+s*(.07+dz*.2),2.461,cz+dz),(.029,.002,.052),gold,static,12,8)
  for ang in range(5):
   t=ang*2*math.pi/5;ellipsoid('Wallpaper rosette petal',(cx+.045*math.cos(t),2.454,cz+.26+.045*math.sin(t)),(.018,.002,.029),gold,static,10,6)
# Mahogany architectural surrounds with layers of moulding.
for x in [-2.65,2.65]:
 cube('Window heavy jamb',(x,2.26,2.32),(.18,.26,2.82),mahogany,.025)
 cube('Window jamb raised bead',(x,2.095,2.32),(.075,.065,2.90),woodedge,.012)
for z in [.92,3.71]:
 cube('Window heavy cross rail',(0,2.255,z),(5.55,.25,.19),mahogany,.027)
 cube('Window cross rail bead',(0,2.095,z),(5.63,.075,.065),woodedge,.014)
cube('Window broad shelf',(0,2.1,.99),(5.55,.48,.10),woodedge,.018)
# Cream louver shutters each made of actual angled slats.
for cx in [-1.82,1.82]:
 for dx in [-.63,.63]:cube('Shutter outer stile',(cx+dx,2.05,2.30),(.11,.085,2.48),cream,.009)
 for z in [1.09,2.3,3.51]:cube('Shutter cross rail',(cx,2.044,z),(1.34,.10,.11),cream,.008)
 cube('Shutter inner mullion',(cx,2.017,2.30),(.075,.12,2.44),cream,.007)
 for half in [-1,1]:
  for j in range(32):
   z=1.155+j*.072
   if abs(z-2.3)<.08:continue
   o=cube('Individually angled louver',(cx+half*.315,2.018,z),(.525,.075,.035),cream,.006)
   o.rotation_euler.x=math.radians(-25)
 for z in [1.40,3.1]:
  cube('Shutter brass hinge',(cx-.70,2.0,z),(.045,.05,.09),brass,.006)
 cube('Shutter latch',(cx+.61,1.971,2.08),(.09,.025,.035),brass,.005)
# Central open window divided into green garden panes.
for x in [-1.13,0,1.13]:cube('Window slender stile',(x,2.1,2.31),(.045,.085,2.38),windowwood,.006)
for z in [1.11,2.31,3.51]:cube('Window center crossbar',(0,2.1,z),(2.28,.085,.05),windowwood,.008)
for x in [-.56,.56]:
 for z in [1.72,2.91]:cube('WindowGlass',(x,2.16,z),(1.06,.017,1.13),glass,.006,live)
# Rich ceiling cornice and exposed painted pipe work.
for z,y,size in [(3.92,2.27,.12),(4.04,2.32,.12),(4.15,2.41,.10)]:cube('Back cornice layered bead',(0,y,z),(9.83,.22,size),woodedge,.015)
for x in [-4.67,4.67]:cube('Side ceiling cornice',(x,.0,4.04),(.18,5.3,.15),mahogany,.022)
cube('Ceiling rear set slice',(0,2.30,4.23),(9.85,1.0,.16),plaster,.012)
tube('Exposed curved pipe',[(-4.45,2.0,3.8),(-4.40,.70,3.84),(-4.32,-.20,3.99),(-4.0,-.5,4.04),(-3.30,-.5,4.04)],.095,pipe,static,16)
for y in [1.68,.80,-.20]:tube('Pipe collar',[(-4.43,y-.05,3.84),(-4.43,y+.05,3.84)],.114,pipe,static,16)
# Large long bench, open wooden slatted base and upholstered botanical cushion.
cube('Bench upper seat rim',(0,1.48,.68),(7.38,1.15,.18),mahogany,.025)
cube('Bench inner seat',(0,1.43,.74),(7.12,.91,.06),woodblack,.005)
for x in [-3.56,-2.0,0,2.0,3.56]:
 cube('Bench front turned leg',(x,.96,.34),(.11,.12,.62),woodedge,.025)
 cube('Bench rear leg',(x,1.95,.35),(.10,.11,.65),mahogany,.018)
 ellipsoid('Bench carved foot',(x,.96,.052),(.094,.10,.05),woodedge,static,20,10)
for z in [.16,.57]:cube('Bench base horizontal rail',(0,1.07,z),(7.30,.10,.072),woodedge,.010)
for x in [-3.4+i*.19 for i in range(37)]:cube('Bench base open fret slat',(x,1.04,.37),(.043,.06,.35),mahogany,.008)
for x in [-3.65,3.65]:
 cube('Bench end arm pedestal',(x,1.45,.89),(.10,1.07,.46),mahogany,.023)
 cube('Bench end rounded arm',(x,1.45,1.10),(.17,1.13,.12),woodedge,.043)
for z in [.78,1.32]:cube('Bench back horizontal rail',(0,1.96,z),(7.22,.115,.13),woodedge,.015)
for x in [-3.45+i*.23 for i in range(31)]:cube('Bench back lattice upright',(x,1.97,1.05),(.052,.07,.43),mahogany,.012)
# Cloth cushion gently bulges and creases rather than looking like a box.
def cushion(name,pos,w,d,h,m,group=static,tilt=0):
 verts=[];faces=[];nx=28;ny=12
 for side in [0,1]:
  for j in range(ny+1):
   yy=-d/2+d*j/ny
   for i in range(nx+1):
    xx=-w/2+w*i/nx;edge=(math.sin(math.pi*i/nx)*math.sin(math.pi*j/ny))**.42
    zz=(h*.15+h*.55*edge if side==0 else -h*.45)+.006*math.sin(xx*53)*math.sin(yy*31)*edge
    verts.append((pos[0]+xx,pos[1]+yy*math.cos(tilt)-zz*math.sin(tilt),pos[2]+yy*math.sin(tilt)+zz*math.cos(tilt)))
 stride=nx+1;off=stride*(ny+1)
 for j in range(ny):
  for i in range(nx):
   a=j*stride+i;faces.append((a,a+1,a+1+stride,a+stride));faces.append((a+off,a+off+stride,a+off+stride+1,a+off+1))
 edges=[list(range(nx+1)),[j*stride+nx for j in range(ny+1)],list(range(ny*stride,ny*stride+nx+1)),[j*stride for j in range(ny+1)]]
 for e in edges:
  for i in range(len(e)-1):a,b=e[i:i+2];faces.append((a,b,b+off,a+off))
 o=mesh(name,verts,faces,m,group)
 for p in o.data.polygons:p.use_smooth=True
 return o
cushion('Long floral seat cushion',(0,1.39,.835),7.08,.91,.16,upholstery)
# Piping and stitch lines on both long seat edges.
for y in [.94,1.84]:beam('Upholstery rolled piping',(-3.53,y,.839),(3.53,y,.839),.012,floral)
# Small repeated embroidered botanical geometry along the visible upholstery front edge.
for x in [-3.3+i*.30 for i in range(23)]:
 tube('Seat embroidered curling stem',[(x,.936,.81),(x+.03,.933,.85),(x+.08,.933,.875)],.003,floral,static,6)
 for dx,z in [(-.02,.835),(.04,.858),(.085,.874)]:ellipsoid('Seat embroidered leaf',(x+dx,.933,z),(.025,.002,.013),floral,static,10,6)
for cx,cy,cz,w,h,m,tilt in [(-2.67,1.73,1.15,.88,.80,olive,1.03),(2.28,1.73,1.13,.85,.82,teal,1.12),(2.88,1.65,1.03,.70,.64,olive,.70),(-2.08,1.75,1.10,.66,.69,teal,1.10)]:
 cushion('Soft velvet bench pillow',(cx,cy,cz),w,h,.19,m,static,tilt)
 # Button and creased corner detail.
 ellipsoid('Velvet tuft button',(cx,cy-.10,cz+.07),(.017,.012,.017),m,static,12,8)
# Left wall vintage framed botanical print rendered from geometry.
cube('Picture dark timber frame',(-3.87,2.335,2.43),(.83,.18,1.45),mahogany,.020)
cube('Picture gold inner frame',(-3.87,2.228,2.43),(.70,.035,1.30),brass,.006)
cube('Picture aged paper',(-3.87,2.20,2.43),(.59,.012,1.19),creamwall,.003)
for s in [-1,1]:
 tube('Framed botanical drawing',[(-3.87,2.186,1.93),(-3.87+s*.04,2.186,2.17),(-3.87+s*.07,2.186,2.40),(-3.87+s*.11,2.186,2.75)],.007,gold,static,6)
 for z in [2.1,2.30,2.50,2.68]:ellipsoid('Framed botanical leaf',(-3.87+s*.08,2.18,z),(.055,.006,.092),gold,static,12,8)
# Decorative wall sconces: molded rose backplates and swooping arms.
practical=[]
for cx in [-3.00,3.37]:
 ellipsoid('Sconce bronze backplate',(cx,2.31,3.28),(.073,.04,.13),bronze,static,20,12)
 for dz in [-.17,.17]:ellipsoid('Sconce gilded finial',(cx,2.32,3.28+dz),(.027,.014,.05),brass,static,14,8)
 tube('Sconce graceful scroll',[(cx,2.31,3.28),(cx+.07,2.19,3.17),(cx+.18,2.12,3.17),(cx+.22,2.10,3.27),(cx+.16,2.08,3.34)],.022,bronze,static,12)
 beam('Sconce lamp socket',(cx+.16,2.08,3.30),(cx+.16,2.08,3.40),.041,brass)
 ellipsoid('InteriorSconceBulb',(cx+.16,2.08,3.47),(.068,.068,.107),bulbmat,live,20,12)
 practical.append((cx+.16,2.01,3.45))
# Right floor lamp with real pleated fabric and open translucent-like linen shade.
beam('FloorLamp tall brass stem',(3.23,.24,.10),(3.23,.24,2.84),.035,bronze,n=18)
ellipsoid('FloorLamp round weighted foot',(3.23,.24,.055),(.28,.28,.056),bronze,static,28,12)
beam('FloorLamp upper turned collar',(3.23,.24,2.51),(3.23,.24,2.69),.078,brass,n=20)
verts=[];faces=[];N=64
for z,r in [(2.49,.48),(2.95,.29)]:
 for i in range(N):a=2*math.pi*i/N;rr=r+(.01 if i%2 else -.01);verts.append((3.23+rr*math.cos(a),.24+rr*math.sin(a),z))
for i in range(N):faces.append((i,(i+1)%N,(i+1)%N+N,i+N))
shade=mesh('InteriorFloorLampShade',verts,faces,linen,live)
for z,r in [(2.49,.48),(2.95,.29)]:
 pts=[(3.23+r*math.cos(i*2*math.pi/N),.24+r*math.sin(i*2*math.pi/N),z) for i in range(N+1)]
 tube('Lampshade bound trim',pts,.012,brass,static,8)
ellipsoid('InteriorFloorLampBulb',(3.23,.24,2.68),(.07,.07,.13),bulbmat,live,20,12);practical.append((3.23,.24,2.69))
# Tall banana/monstera plant with true curled leaves, soil and ceramic pot.
ellipsoid('Plant rounded pot',(4.11,.67,.33),(.37,.37,.40),clay,static,32,16)
ellipsoid('Plant visible soil',(4.11,.67,.65),(.30,.30,.03),soil,static,20,8)
for i in range(9):
 ang=i*2.1;end=(4.11+math.cos(ang)*(.7+.06*i),.67+math.sin(ang)*(.40+.05*i),1.22+.18*i)
 stem=(4.11,.67,.61);mid=(4.11+math.cos(ang)*.15,.67+math.sin(ang)*.14,end[2]-.28)
 tube('Banana petiole',[stem,mid,end],[.026,.020,.014],leafm[2],foliage,10)
 tip=(end[0]+math.cos(ang)*.54,end[1]+math.sin(ang)*.36,end[2]+.44)
 leaf('Large curled banana leaf',end,tip,.31+.015*i,leafm[i%6],foliage,True)
plant=join(foliage,'InteriorPlant');live.append(plant);plant['effect']='soft-wind'
# Layered garden visible through the window, made entirely of foliage geometry.
garden=[]
for i in range(17):
 x=random.uniform(-2.8,2.8);y=random.uniform(3.1,5.4);z=random.uniform(1.0,3.9)
 beam('Garden twig',(x,y,z-.5),(x+.16,y,z+.45),.016,leafm[0],garden)
 for j in range(8):
  ang=random.uniform(0,math.tau);a=(x,y,z+random.uniform(-.4,.35));b=(a[0]+math.cos(ang)*random.uniform(.25,.55),a[1]+math.sin(ang)*random.uniform(.20,.55),a[2]+random.uniform(-.12,.25))
  leaf('Garden laurel leaf',a,b,random.uniform(.07,.12),leafm[random.randrange(6)],garden)
gard=join(garden,'InteriorGarden');gard['background']=True;live.append(gard)

# Generic seated adults, carefully shaped organic mesh and clothing, no portrait texture.
def performer(name,cx,woman=False):
 body=[];head=[];root=empty(name,(cx,1.08,0));root['performer']='generic adult';root['breathing_pivot']=True
 cloth=slate if woman else navy
 # Soft tapered torso with proper shoulders and garment overlap.
 ellipsoid(name+' torso',(0,.43,1.46),(.23 if woman else .255,.17,.36),cloth,body,28,20)
 ellipsoid(name+' waist',(0,.40,1.12),(.215,.19,.16),cloth,body,24,14)
 ellipsoid(name+' shoulder line',(0,.44,1.66),(.26 if woman else .285,.15,.15),cloth,body,28,16)
 # Shirt throat and a pair of geometric folded collars.
 tube(name+' neck',[(0,.40,1.72),(0,.40,1.88)],[.075,.071],skin,body,18)
 for s in [-1,1]:
  vs=[(s*.015,.242,1.77),(s*.13,.285,1.73),(s*.095,.218,1.63),(s*.04,.211,1.69)]
  mesh(name+' pointed collar',vs,[(0,1,2,3)],shirt if not woman else slate,body)
 if woman:
  # Open jacket lapels, dark inner blouse, three real buttons and sleeve cuffs.
  ellipsoid('Woman dark inner blouse',(0,.236,1.43),(.087,.035,.235),olive,body,20,14)
  for s in [-1,1]:mesh('Gray jacket folded lapel',[(s*.10,.217,1.76),(s*.21,.216,1.62),(s*.095,.194,1.42),(s*.065,.191,1.65)],[(0,1,2,3)],slate,body)
  for z in [1.23,1.34,1.45]:ellipsoid('Jacket small horn button',(.045,.201,z),(.012,.006,.012),brass,body,12,8)
 else:
  # Ribbed sweater waist band and subtle vertical knit seam folds.
  for x in [-.20+i*.019 for i in range(22)]:beam('Sweater ribbing waist',(x,.239,1.075),(x,.225,1.16),.0024,navy,body,6)
 # Arms in conversational lap pose, organic tapered sleeves.
 if woman:
  elbows=[(-.27,.19,1.32),(.28,.18,1.28)];wrists=[(-.03,-.03,1.14),(.10,-.08,1.13)]
 else:
  elbows=[(-.28,.10,1.37),(.26,.09,1.36)];wrists=[(-.04,-.04,1.40),(.075,-.09,1.39)]
 for s,e,w in zip([-1,1],elbows,wrists):
  shoulder=(s*(.21 if woman else .24),.42,1.68)
  tube(name+' sleeve upper',[shoulder,(s*.28,.31,1.55),e],[.091,.080,.075],cloth,body,20)
  tube(name+' sleeve forearm',[e,((e[0]+w[0])*.5,(e[1]+w[1])*.5,(e[2]+w[2])*.5),w],[.074,.068,.058],cloth,body,20)
  ellipsoid(name+' cuff seam',w,(.060,.058,.041),cloth,body,18,10)
  palm=(w[0]+s*.027,w[1]-.075,w[2]-.016)
  ellipsoid(name+' shaped palm',palm,(.060,.076,.025),skin,body,20,12)
  # Four separate bent fingers and opposed thumb.
  for f in range(4):
   dx=-.040+f*.025;start=(palm[0]+dx,palm[1]-.035,palm[2]);end=(palm[0]+dx+s*.005,palm[1]-.100,palm[2]-.012)
   tube(name+' finger',[start,((start[0]+end[0])/2,start[1]-.038,start[2]-.004),end],[.011,.010,.007],skin,body,10)
  tube(name+' thumb',[(palm[0]+s*.04,palm[1]+.005,palm[2]),(palm[0]+s*.072,palm[1]-.032,palm[2]+.003),(palm[0]+s*.063,palm[1]-.065,palm[2]-.005)],[.017,.013,.009],skin,body,10)
 # Seated hips/thighs then knees and long lowered calves, floor feet.
 if woman:
  # Skirt hangs softly over closed knees with a fluted curved hem.
  verts=[];faces=[];rings=[(.40,1.00,.235),(.13,.91,.25),(-.15,.74,.245),(-.25,.62,.25)];N=40
  for j,(y,z,r) in enumerate(rings):
   for i in range(N):a=math.tau*i/N;rr=r+.009*math.sin(i*1.7);verts.append((rr*math.cos(a),y+.14*math.sin(a),z+.05*math.sin(a)))
  for j in range(len(rings)-1):
   for i in range(N):a=j*N+i;b=j*N+(i+1)%N;faces.append((a,b,b+N,a+N))
  faces.append(tuple(range(N-1,-1,-1)));o=mesh('Woman tailored tweed skirt',verts,faces,skirt,body)
  for p in o.data.polygons:p.use_smooth=True
  for x in [-.105,.105]:
   tube('Woman knee to calf',[(x,-.25,.60),(x,-.32,.45),(x,-.35,.25)],[.070,.061,.053],skin,body,20)
   tube('Woman leather boot shaft',[(x,-.35,.10),(x,-.35,.38)],[.065,.061],boots,body,20)
   ellipsoid('Woman leather boot foot',(x,-.45,.091),(.088,.17,.09),boots,body,24,14)
   cube('Woman boot sole',(x,-.46,.030),(.174,.33,.035),black,.014,body)
   for z in [.18,.24,.30]:beam('Woman boot lace',(x-.031,-.414,z),(x+.031,-.414,z+.018),.003,boots,body,6)
 else:
  ellipsoid('Man trouser hips',(0,.40,.96),(.25,.23,.13),whitecloth,body,24,14)
  for x in [-.14,.14]:
   tube('Man trouser thigh',[(x,.40,.95),(x,.05,.91),(x,-.27,.77)],[(.134,.15),(.136,.132),(.115,.10)],whitecloth,body,24)
   tube('Man trouser calf',[(x,-.27,.77),(x,-.33,.43),(x,-.42,.15)],[(.110,.103),(.086,.09),(.075,.065)],whitecloth,body,24)
   # Cloth seam and compressed knee folds.
   for z in [.70,.75,.80]:beam('Trouser knee crease',(x-.09,-.362,z),(x+.09,-.364,z-.018),.0025,creamwall,body,6)
   ellipsoid('Man canvas sneaker',(x,-.51,.081),(.100,.19,.076),shoe,body,28,14)
   cube('Man sneaker rubber sole',(x,-.52,.033),(.207,.375,.037),sole,.022,body)
   ellipsoid('Man sneaker toe cap',(x,-.639,.077),(.10,.055,.054),sole,body,20,12)
   for z,y in [(.115,-.54),(.13,-.51),(.14,-.48)]:beam('Sneaker cotton lace',(x-.060,y,z),(x+.060,y,z+.005),.005,shirt,body,8)
 # Head built in its own coordinate space, with subtle sculpted facial anatomy.
 ellipsoid(name+' shaped head',(0,0,0),(.112,.106,.152),skin,head,32,24)
 ellipsoid(name+' jaw',(0,-.018,-.070),(.095,.080,.070),skin,head,28,18)
 for s in [-1,1]:
  ellipsoid(name+' ear',(s*.109,.006,-.006),(.017,.018,.034),skin,head,18,12)
  ellipsoid(name+' ear inner',(s*.115,-.004,-.006),(.008,.008,.017),lip,head,14,8)
  # Narrow adult eyes under the brow, never oversized toy eyes.
  ellipsoid(name+' eye socket',(s*.047,-.098,.021),(.029,.008,.015),skin,head,20,12)
  ellipsoid(name+' eye white',(s*.047,-.105,.021),(.022,.004,.0075),eyewhite,head,18,10)
  ellipsoid(name+' eye iris',(s*.047,-.109,.021),(.006,.0025,.007),eye,head,16,10)
  tube(name+' upper lid',[(s*.068,-.108,.023),(s*.049,-.110,.029),(s*.026,-.104,.024)],.0035,hair,head,8)
  tube(name+' eyebrow',[(s*.076,-.093,.055),(s*.050,-.102,.062),(s*.024,-.096,.057)],.007,hair,head,10)
 # Slender nose bridge and actual nostrils.
 ellipsoid(name+' nose bridge',(0,-.103,-.001),(.014,.018,.038),skin,head,20,14)
 ellipsoid(name+' nose tip',(0,-.126,-.020),(.022,.023,.017),skin,head,20,12)
 for s in [-1,1]:ellipsoid(name+' nostril',(s*.012,-.141,-.026),(.006,.003,.003),lip,head,12,8)
 tube(name+' upper lip',[(-.029,-.104,-.058),(-.011,-.115,-.056),(0,-.118,-.059),(.010,-.115,-.056),(.029,-.104,-.058)],.0034,lip,head,10)
 tube(name+' lower lip',[(-.027,-.104,-.062),(0,-.113,-.066),(.027,-.104,-.062)],.0040,lip,head,10)
 # Smooth cropped/bob hair cap, with organic boundary and a visible part.
 vs=[];fs=[];N=40;R=10
 for j in range(R+1):
  t=j/R
  for i in range(N):
   a=math.tau*i/N
   # Front hairline stops above eyebrow; sides and back fall behind the ears.
   front=max(0,-math.sin(a));limit=(1.60 if not woman else 1.93)-.47*front+.05*math.sin(a*3)
   phi=.03+t*limit;vs.append((.118*math.sin(phi)*math.cos(a),.112*math.sin(phi)*math.sin(a)+.012,.159*math.cos(phi)+.010))
 for j in range(R):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 o=mesh(name+' hairstyle cap',vs,fs,hair,head)
 for p in o.data.polygons:p.use_smooth=True
 if woman:
  # Long bob curtain with volume behind and on either side of the face.
  ellipsoid('Woman bob back',(0,.092,-.048),(.123,.07,.21),hair,head,28,22)
  for s in [-1,1]:ellipsoid('Woman side bob',(s*.105,.02,-.095),(.042,.061,.171),hair,head,24,20)
  for s in [-1,1]:
   for j in range(6):
    x=s*(.098+j*.006)
    tube('Woman hair fine strand',[(x,-.012,.099),(x+s*.014,-.028,-.003),(x+s*.005,-.015,-.16)],[.0025,.003,.002],hairlight,head,8)
 else:
  for j in range(13):
   x=-.086+j*.012
   tube('Man swept hair ridge',[(x,-.071,.103),(x+.015,-.038,.152),(x+.037,.020,.153),(x+.055,.073,.112)],[.003,.0035,.003,.002],hairlight,head,8)
 h=join(head,name+'Head');h.location=(0,.39,1.98);h.rotation_euler.z=math.radians(28 if not woman else -32);h.parent=root
 # Actor body includes multiple retained materials but one efficient draw hierarchy.
 b=join(body,name+'Body');b.parent=root
 return root
# Performer geometry is deliberately omitted. The dusk window is told through its empty seats and props.

anchors={'master':(0,1.13,1.60),'two-shot':(0,1.02,1.61),'man':(-.83,1.36,1.80),'woman':(.73,1.37,1.80),'detail':(.0,.90,1.37),'window':(.0,2.12,2.28),'lamp':(3.23,.24,2.70)}
for k,p in anchors.items():o=empty('Anchor_'+k,p);o['category']=k
# A soft practical key and garden bounce; built-in lamps remain editable in .blend.
def area(name,pos,target,power,size,c):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=c;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Warm cinematic key',(-2.3,-2.8,3.4),(0,1.2,1.45),470,4.0,(1,.77,.46))
area('Garden window fill',(0,2.28,2.5),(0,1,1.3),330,2.5,(.64,.80,.58))
area('Subtle soft camera fill',(2.0,-2.5,2.8),(0,1.4,1.4),90,3,(1,.86,.70))
for i,p in enumerate(practical):
 d=bpy.data.lights.new('Interior practical %d'%i,'POINT');d.energy=55 if i<2 else 85;d.shadow_soft_size=.18;d.color=(1,.70,.37);o=bpy.data.objects.new(d.name,d);bpy.context.collection.objects.link(o);o.location=p
world=bpy.data.worlds.new('Warm lounge ambient');world.use_nodes=True;bpy.context.scene.world=world;world.node_tree.nodes['Background'].inputs[0].default_value=(.085,.068,.039,1);world.node_tree.nodes['Background'].inputs[1].default_value=.22
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=3
scene.render.threads_mode='FIXED';scene.render.threads=8;scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
d=bpy.data.cameras.new('InteriorCamera');cam=bpy.data.objects.new('InteriorCamera',d);bpy.context.collection.objects.link(cam);cam.location=(.12,-7.7,2.12);cam.rotation_euler=(Vector((0,1.4,1.94))-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=42;scene.camera=cam
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'interior-room.blend'))
print('INTERIOR_MODEL_READY',len(static),len(live),flush=True)
# Bake architecture warm shadows/grain into one atlas; performers and practicals relight live.
combined=join(static,'Interior_Baked_Static');bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(67),island_margin=.003);bpy.ops.object.mode_set(mode='OBJECT');combined.data.uv_layers.active.name='BakedUV'
img=bpy.data.images.new('interior-warm-baked',width=4096,height=4096,alpha=False)
for m in combined.data.materials:
 if m:n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;n.select=True;m.node_tree.nodes.active=n
bpy.context.view_layer.objects.active=combined;combined.select_set(True);scene.render.bake.use_clear=True;scene.render.bake.margin=5
bpy.ops.object.bake(type='COMBINED');img.filepath_raw=str(ASSETS/'interior-warm-baked.jpg');img.file_format='JPEG';img.save()
baked=mat('Interior_Cycles_Baked_Atlas',(1,1,1),1);n=baked.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;baked.node_tree.links.new(n.outputs['Color'],baked.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);combined.data.materials.clear();combined.data.materials.append(baked)
for p in combined.data.polygons:p.material_index=0
print('INTERIOR_BAKED',flush=True)
# Preview uses the already lit atlas as emission, avoiding a second shading pass.
p=baked.node_tree.nodes.get('Principled BSDF');base_link=next(l for l in baked.node_tree.links if l.to_socket==p.inputs['Base Color']);baked.node_tree.links.remove(base_link);p.inputs['Base Color'].default_value=(0,0,0,1);baked.node_tree.links.new(n.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=1
scene.render.filepath=str(OUT/'interior-preview.png');bpy.ops.render.render(write_still=True)
for l in list(baked.node_tree.links):
 if l.to_socket==p.inputs['Emission Color']:baked.node_tree.links.remove(l)
p.inputs['Emission Strength'].default_value=0;baked.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
for o in list(bpy.data.objects):
 if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(ASSETS/'interior-room.glb'),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False,export_materials='EXPORT',export_apply=True)
# glTF cannot translate procedural noise; keep the original linear base colors.
export_file=ASSETS/'interior-room.glb'
glb=export_file.read_bytes();json_size=struct.unpack_from('<I',glb,12)[0]
gltf=json.loads(glb[20:20+json_size])
for material in gltf.get('materials',[]):
 runtime=material.setdefault('pbrMetallicRoughness',{})
 source=bpy.data.materials.get(material.get('name',''))
 if source and 'baseColorTexture' not in runtime and 'baseColorFactor' not in runtime:runtime['baseColorFactor']=list(source.diffuse_color)
json_chunk=json.dumps(gltf,separators=(',',':')).encode();json_chunk+=b' '*((-len(json_chunk))%4)
bin_chunk=glb[20+json_size:]
export_file.write_bytes(struct.pack('<III',0x46546c67,2,20+len(json_chunk)+len(bin_chunk))+struct.pack('<II',len(json_chunk),0x4e4f534a)+json_chunk+bin_chunk)
objs=[o for o in bpy.data.objects if o.type=='MESH'];conv=lambda p:[p[0],p[2],-p[1]]
frames={
'master':{'position':[0,2.0,8.4],'target':[0,1.85,-1.4],'fov':40,'angle':'平视','scale':'全景'},
'two-shot':{'position':[0,1.80,4.3],'target':[0,1.65,-1.15],'fov':40,'angle':'平视','scale':'双人中景'},
'man':{'position':[.15,1.92,2.65],'target':[-.83,1.96,-1.47],'fov':30,'angle':'斜侧','scale':'单人近景'},
'woman':{'position':[-.25,1.92,2.65],'target':[.73,1.96,-1.47],'fov':30,'angle':'斜侧','scale':'单人近景'},
'detail':{'position':[.08,1.55,1.15],'target':[0,1.37,-1.0],'fov':30,'angle':'俯视','scale':'手部特写'},
'window':{'position':[-.45,2.2,2.6],'target':[0,2.3,-2.15],'fov':32,'angle':'平视','scale':'窗景'},
'lamp':{'position':[1.8,2.4,2.0],'target':[3.23,2.68,-.24],'fov':34,'angle':'斜侧','scale':'细节近景'}
}
info={'blender':bpy.app.version_string,'source_reference':'IMG_1837.JPG','static_parts':len(static),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objs),'glb_bytes':(ASSETS/'interior-room.glb').stat().st_size,'meshes':len(objs),'atlas':'interior-warm-baked.jpg','atlas_size':4096,'nodes':{'static':'Interior_Baked_Static','actors':[],'garden':'InteriorGarden','plant':'InteriorPlant','sconce':'InteriorSconceBulb','shade':'InteriorFloorLampShade','floor_bulb':'InteriorFloorLampBulb','glass':'WindowGlass'},'anchors_gltf_y_up':{k:conv(p) for k,p in anchors.items()},'frames_gltf_y_up':frames,'practical_lights_gltf':[{ 'position':conv(p),'color':'#ffca80','intensity':i} for p,i in zip(practical,[13,13,18])],'note':'Physical modeled architecture, shutters, slatted bench, upholstery, wallpaper relief, plants, lamps, and two quiet places set at the dusk window. No image plane background. Editable .blend preserves individual meshes and original procedural materials.'}
(ASSETS/'interior-model-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));(NOTES/'interior-notes.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));shutil.copy2(ASSETS/'interior-room.glb',OUT/'interior-room.glb');shutil.copy2(__file__,OUT/'build_interior.py');print('INTERIOR_EXPORT_READY',json.dumps(info),flush=True)
