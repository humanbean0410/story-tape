"""Four-coach passenger train: editable Blender mesh + optimized Y-up GLB.
Run Blender --background --factory-startup --python build_train.py -- SITE OUTPUTS
X is longitudinal, Blender Y is across track, Z is height. GLB is Y-up.
No reference photos, brands, or third party models are embedded.
"""
import bpy,bmesh,math,random,json,sys,shutil,struct
from pathlib import Path
from mathutils import Vector
random.seed(731)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
SITE=Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
OUT=Path(args[1]).resolve() if len(args)>1 else SITE.parent.parent/'outputs'
ASSETS=SITE/'dist/assets';TEX=ASSETS/'train-textures'
ASSETS.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True);TEX.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
static=[];door_sets=[];all_parts=[]
root=bpy.data.objects.new('PassengerTrain',None);bpy.context.collection.objects.link(root)
root['description']='Four detailed 12 m passenger coaches, genuine modeled interior and running gear'
root['coach_count']=4;root['track_z']=3.72;root['travel_axis']='X'

# Portable microvariation maps: modest patina that survives GLB export.
def paint_image(name,color,n=128):
 im=bpy.data.images.new(name,width=n,height=n,alpha=False);pix=[]
 for y in range(n):
  for x in range(n):
   v=(random.random()-.5)*.045+math.sin(x*.26+y*.034)*.007
   wear=.94 if y<3 or y>n-4 else 1
   pix.extend([max(.002,min(1,c*wear*(1+v))) for c in color]+[1])
 im.pixels=pix;im.filepath_raw=str(TEX/(name+'.png'));im.file_format='PNG';im.save();im.pack()
 return im

def mat(name,col,rough=.5,metal=0,tex=False,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if tex:
  im=paint_image(name.replace(' ','-').lower(),col);t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
 if emission:
  p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emission
 return m
G=mat('Train forest enamel',(.052,.17,.123),.28,.24,True)
C=mat('Train warm cream enamel',(.73,.70,.55),.32,.12,True)
R=mat('Train weathered roof',(.32,.365,.35),.5,.45,True)
M=mat('Train brushed metal',(.43,.47,.45),.26,.78)
D=mat('Train iron chassis',(.065,.079,.078),.62,.52)
B=mat('Train rubber and gasket',(.018,.025,.024),.77,.03)
S=mat('Train upholstery',(.21,.29,.235),.77)
F=mat('Train interior timber',(.215,.125,.076),.65)
I=mat('Train interior ivory',(.64,.63,.52),.68)
W=mat('Train glazing',(.155,.27,.27),.12,.10)
p=W.node_tree.nodes.get('Principled BSDF');p.inputs['Alpha'].default_value=.22
try:W.surface_render_method='DITHERED'
except:pass
W.diffuse_color=(.155,.27,.27,.22)
H=mat('Train headlamp',(.92,.81,.57),.2,.1,3.0)
T=mat('Train tail lamp',(.68,.04,.017),.2,.1,1.6)
L=mat('Train interior lamp',(.86,.78,.56),.3,0,1.0)

# Explicit rounded topology and real window openings.
def reg(o,m,group):
 if m:o.data.materials.append(m)
 o.parent=root;group.append(o);all_parts.append(o);return o

def uv_box(o):
 uv=o.data.uv_layers.new(name='UVMap')
 for p in o.data.polygons:
  a=max(range(3),key=lambda i:abs(p.normal[i]));dims=[i for i in range(3) if i!=a]
  for li in p.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co
   uv.data[li].uv=(v[dims[0]]*.31+.5,v[dims[1]]*.31+.5)

def mesh(name,vs,fs,m,group,smooth=False,uvs=None):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
 if uvs:
  uv=d.uv_layers.new(name='UVMap')
  for p in d.polygons:
   for li in p.loop_indices:uv.data[li].uv=uvs[d.loops[li].vertex_index]
 else:uv_box(o)
 for p in d.polygons:p.use_smooth=smooth
 return reg(o,m,group)

def box(name,pos,size,m,group,bevel=.014,segments=1):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=segments,affect='EDGES',clamp_overlap=True)
 d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;uv_box(o)
 return reg(o,m,group)

def tube(name,a,b,r,m,group,n=10):
 a=Vector(a);b=Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
 if u.length<.01:u=axis.cross(Vector((0,1,0)))
 u.normalize();v=axis.cross(u)
 vs=[tuple(p+r*(math.cos(i*2*math.pi/n)*u+math.sin(i*2*math.pi/n)*v)) for p in [a,b] for i in range(n)]
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return mesh(name,vs,fs,m,group,True)

def wheel(name,x,y,z,group):
 # Radial profiles revolve around axle Y, including rim and flange.
 prof=[(-.11,.13),(-.11,.27),(-.075,.315),(.075,.315),(.075,.345),(.12,.345),(.13,.27),(.13,.13)]
 n=24;vs=[]
 for dy,r in prof:
  vs += [(x+r*math.cos(i*2*math.pi/n),y+dy,z+r*math.sin(i*2*math.pi/n)) for i in range(n)]
 fs=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(prof)-1) for i in range(n)]
 fs += [tuple(range(n-1,-1,-1)),tuple((len(prof)-1)*n+i for i in range(n))]
 mesh(name,vs,fs,M,group,True)
 tube('Wheel hub',(x,y-.135,z),(x,y+.145,z),.095,D,group,12)
 for dy in [-.145,.155]:
  for i in range(6):
   ang=i*math.pi/3;tube('Hub securing bolt',(x+.064*math.cos(ang),y+dy-.014,z+.064*math.sin(ang)),(x+.064*math.cos(ang),y+dy+.014,z+.064*math.sin(ang)),.014,M,group,6)

def spring(name,x,y,z,group):
 # Actual helical spring, not a stack of plates.
 vs=[];fs=[];turns=5;steps=60;n=5
 for i in range(steps+1):
  t=i/steps;ang=turns*math.tau*t;cx=x+.058*math.cos(ang);cy=y+.058*math.sin(ang);cz=z+.21*t
  for j in range(n):
   q=j*math.tau/n;vs.append((cx+.011*math.cos(q)*math.cos(ang),cy+.011*math.cos(q)*math.sin(ang),cz+.011*math.sin(q)))
 for i in range(steps):
  for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
 mesh(name,vs,fs,M,group,True)

def roof(name,cx,length,group):
 n=20;vs=[]
 for x in [cx-length/2,cx+length/2]:
  for i in range(n+1):
   t=-math.pi/2+i*math.pi/n;vs.append((x,1.15*math.sin(t),2.66+.41*math.cos(t)))
 fs=[(i,i+1,n+2+i,n+1+i) for i in range(n)]
 fs += [tuple(range(n,-1,-1)),tuple(range(n+1,(n+1)*2))]
 mesh(name,vs,fs,R,group,True)
 # Fine roof gutter extends along the upper belt.
 for side in [-1,1]:
  tube('Rain gutter',(cx-length/2,side*1.159,2.66),(cx+length/2,side*1.159,2.66),.022,M,group,8)
 for dx in [-3.75,-2.2,-.75,.75,2.2,3.75]:
  box('Roof ventilator',(cx+dx,0,3.12),(.6,.34,.145),R,group,.045)
  for k in range(4):box('Ventilation slit',(cx+dx-.19+k*.125,-.176,3.125),(.061,.008,.06),B,group,.002,1)

# Rounded perimeter reveals: gasket behind thin satin metal frame.
def window(name,x,y,z,w,h,group,m=W):
 # Geometry around a glass opening; no solid wall behind it.
 for gm,yy,thick,bar in [(B,y,.039,.037),(M,y+math.copysign(.008,y),.036,.018)]:
  box(name+' bottom',(x,yy,z-h/2),(w+.065,thick,bar),gm,group,.008)
  box(name+' top',(x,yy,z+h/2),(w+.065,thick,bar),gm,group,.008)
  for xx in [x-w/2,x+w/2]:box(name+' upright',(xx,yy,z),(bar,thick,h),gm,group,.008)
 box(name+' pane',(x,y,z),(w-.025,.012,h-.025),m,group,.006)
 box(name+' sliding crossbar',(x,y+math.copysign(.017,y),z-.085),(w,.035,.025),M,group,.006)
 # Fine latch catches readable in closeup.
 box(name+' latch',(x+w*.25,y+math.copysign(.034,y),z-.08),(.055,.032,.055),D,group,.008)

LENGTH=11.75;GAP=.78;PITCH=LENGTH+GAP;centers=[(i-1.5)*PITCH for i in range(4)]
for ci,cx in enumerate(centers):
 group=[];static.append(group)
 prefix='Coach_%02d'%(ci+1)
 box(prefix+' floor',(cx,0,.75),(LENGTH,2.15,.16),F,group,.025)
 box(prefix+' underframe',(cx,0,.625),(LENGTH-.24,1.84,.14),D,group,.04)
 for y in [-1.05,1.05]:
  box('Sill metal rail',(cx,y,.76),(LENGTH,.13,.16),M,group,.019)
  for lo,hi in [(-LENGTH/2,-4.37),(-3.11,3.11),(4.37,LENGTH/2)]:
   mid=(lo+hi)/2;wid=hi-lo
   box('Green lower side',(cx+mid,y,1.15),(wid,.12,.66),G,group,.024)
   box('Cream window sill',(cx+mid,y,1.515),(wid,.11,.12),C,group,.012)
   box('Waist polished stripe',(cx+mid,y+math.copysign(.064,y),1.442),(wid,.026,.027),M,group,.007)
  box('Header cream band',(cx,y,2.56),(LENGTH,.115,.22),C,group,.025)
  box('Header green edging',(cx,y,2.685),(LENGTH,.11,.047),G,group,.008)
  # Seven passenger windows, separated by proper solid piers. Two entrances interrupt window rhythm.
  wins=[(-5.18,.68),(-2.66,1.12),(-1.35,1.1),(0,1.18),(1.35,1.1),(2.66,1.12),(5.18,.68)]
  for dx,w in wins:window('Passenger window',cx+dx,y+math.copysign(.066,y),2.04,w,.87,group)
  spans=[(-5.77,.19),(-4.69,.15),(-4.38,.20),(-3.05,.16),(-2.02,.16),(-.675,.16),(.675,.16),(2.02,.16),(3.05,.16),(4.38,.20),(4.69,.15),(5.77,.19)]
  for dx,w in spans:box('Window cream pillar',(cx+dx,y,2.035),(w,.12,.93),C,group,.012)
  for dx in [-3.74,3.74]:
   # Recessed vestibule openings + independent double leaves. At open state exterior green panels slide aside.
   box('Door recessed lintel',(cx+dx,y,2.58),(1.22,.18,.16),D,group,.015)
   box('Door threshold',(cx+dx,y,.815),(1.20,.23,.045),M,group,.012)
   for sx in [-.63,.63]:box('Door jamb',(cx+dx+sx,y,1.655),(.069,.18,1.73),M,group,.009)
   for leaf in [-1,1]:
    dg=[];name=prefix+('_Near' if y<0 else '_Far')+('_DoorLeft_' if leaf<0 else '_DoorRight_')+str(0 if dx<0 else 1)
    # Geometry grouped with pivot at door centre during optimization.
    px=cx+dx+leaf*.293;dy=y+math.copysign(.072,y)
    box(name+' lower',(px,dy,1.15),(.565,.09,.62),G,dg,.018)
    box(name+' upper',(px,dy,2.455),(.565,.09,.17),C,dg,.012)
    box(name+' waist',(px,dy,1.516),(.565,.09,.12),C,dg,.012)
    for ox in [-.269,.269]:box('Door window side',(px+ox,dy,1.954),(.043,.09,.85),C,dg,.008)
    window('Door glazed pane',px,dy+math.copysign(.05,dy),1.963,.465,.76,dg)
    box('Door metal split seam',(px+leaf*.282,dy+math.copysign(.06,dy),1.667),(.018,.018,1.64),M,dg,.004)
    tube('Door grab handle',(px-leaf*.175,dy+math.copysign(.096,dy),1.432),(px-leaf*.175,dy+math.copysign(.096,dy),1.765),.013,M,dg,8)
    door_sets.append((dg,name,Vector((px,dy,1.667)),leaf))
   box('Retracted step footboard',(cx+dx,y+math.copysign(.18,y),.565),(1.22,.31,.06),D,group,.012)
   for k in range(7):box('Step tread grooves',(cx+dx-.48+k*.16,y+math.copysign(.18,y),.599),(.036,.26,.01),M,group,.002,1)
  # interior sofa benches are interrupted at entrances, remain visible through true glass.
  for mid,wid in [(-5.15,1.15),(-1.22,3.72),(1.94,1.14),(5.15,1.15)]:
   box('Passenger bench cushion',(cx+mid,y*.73,1.07),(wid,.43,.17),S,group,.055)
   box('Passenger bench back',(cx+mid,y*.91,1.39),(wid,.12,.50),S,group,.045)
   for k in range(max(1,int(wid/.48))):box('Upholstery stitched join',(cx+mid-wid/2+.29+k*.48,y*.969,1.40),(.007,.006,.34),D,group,.002,1)
   box('Seat storage plinth',(cx+mid,y*.73,.91),(wid-.08,.38,.21),I,group,.02)
  # overhead luggage racks and hanging grab rings.
  tube('Rack front rail',(cx-5.35,y*.73,2.35),(cx+5.35,y*.73,2.35),.018,M,group,8)
  for x in [-4.9,-2.55,-1.35,0,1.35,2.55,4.9]:
   tube('Rack crossmember',(cx+x,y*.73,2.35),(cx+x,y*.96,2.35),.011,M,group,6)
   tube('Hand strap',(cx+x,y*.48,2.40),(cx+x,y*.48,2.18),.01,B,group,6)
   # articulated molded ring (20 perimeter segments)
   for q in range(14):
    a=math.tau*q/14;b=math.tau*(q+1)/14
    tube('Grab ring',(cx+x+.047*math.cos(a),y*.48,2.13+.047*math.sin(a)),(cx+x+.047*math.cos(b),y*.48,2.13+.047*math.sin(b)),.006,I,group,5)
 for y in [-.55,.55]:box('Warm interior ceiling light',(cx,y,2.565),(9.1,.085,.025),L,group,.007)
 for x in [-2.28,2.28]:
  box('Underfloor electrical cabinet',(cx+x,0,.42),(1.14,.95,.28),D,group,.035)
  for k in range(7):box('Cabinet cooling groove',(cx+x-.43+k*.14,-.49,.42),(.067,.019,.15),B,group,.004)
 for x in [-1.15,1.15]:tube('Underslung air reservoir',(cx+x,-.66,.39),(cx+x+.70,-.66,.39),.10,D,group,12)
 for bx in [cx-3.86,cx+3.86]:
  box('Bogie bolster',(bx,0,.53),(2.03,1.59,.17),D,group,.03)
  for y in [-.83,.83]:
   box('Bogie side frame',(bx,y,.44),(2.11,.135,.155),D,group,.035)
   for dx in [-.72,.72]:
    wheel('Steel flanged wheel',bx+dx,y,.345,group)
    box('Axle journal bearing',(bx+dx,y*1.13,.355),(.23,.19,.22),D,group,.03)
    spring('Bogie suspension spring',bx+dx,y*.82,.48,group)
    tube('Spring damper',(bx+dx+.19,y,.37),(bx+dx+.32,y,.66),.025,M,group,8)
   box('Bogie center bearing',(bx,y,.59),(.42,.12,.16),M,group,.027)
   tube('Brake link',(bx-.85,y,.30),(bx+.85,y,.30),.018,M,group,8)
  for dx in [-.72,.72]:tube('Full axle',(bx+dx,-.93,.345),(bx+dx,.93,.345),.052,D,group,12)
 roof('Arched continuous roof',cx,LENGTH,group)
 # end walls and end windows: internal ends have central gangway, outside ends form rounded cabs.
 for sign in [-1,1]:
  ex=cx+sign*LENGTH/2
  outside=(ci==0 and sign<0) or (ci==3 and sign>0)
  if not outside:
   box('End wall lower',(ex,0,1.15),(.11,2.07,.67),G,group,.023)
   for y in [-.82,.82]:box('End wall shoulder',(ex,y,2.025),(.12,.42,1.28),C,group,.02)
   box('Gangway lintel',(ex,0,2.59),(.13,1.30,.17),C,group,.017)
   box('Gangway portal darkness',(ex,0,1.83),(.035,.82,1.88),B,group,.035)
   for y in [-.44,.44]:tube('Gangway metal rail',(ex+sign*.062,y,.84),(ex+sign*.062,y,2.63),.029,M,group,8)
  else:
   # Rounded cab corners, framed panoramic windshield, inset destination box.
   box('Cab nose rounded',(ex+sign*.105,0,1.21),(.31,2.12,.84),G,group,.11,4)
   box('Cab windscreen header',(ex+.06*sign,0,2.56),(.20,2.12,.18),C,group,.06,3)
   for y in [-.97,.97]:box('Cab upright outer',(ex+.05*sign,y,2.00),(.23,.14,1.07),C,group,.045,3)
   box('Cab centre mullion',(ex+.109*sign,0,2.055),(.10,.065,.96),M,group,.018)
   for y in [-.47,.47]:
    box('Cab windscreen gasket',(ex+.112*sign,y,2.08),(.042,.86,.845),B,group,.045,3)
    box('Cab windscreen',(ex+.147*sign,y,2.09),(.027,.78,.755),W,group,.043,3)
    tube('Cab windshield wiper',(ex+.171*sign,y-.28,1.81),(ex+.171*sign,y+.05,2.245),.013,D,group,6)
    tube('Wiper metal hinge',(ex+.174*sign,y-.30,1.79),(ex+.174*sign,y-.28,1.96),.009,M,group,6)
   box('Cab destination box',(ex+.16*sign,0,2.566),(.031,.44,.104),B,group,.014)
   # no brand lettering, tiny luminous slat identifiers.
   for k in range(5):box('Route indicator segment',(ex+.18*sign,-.13+k*.063,2.566),(.008,.039,.046),I,group,.002)
   for y in [-.68,.68]:
    tube('Headlamp metal bezel',(ex+.22*sign,y,1.32),(ex+.30*sign,y,1.32),.119,M,group,20)
    tube('Headlamp illuminated lens',(ex+.31*sign,y,1.32),(ex+.324*sign,y,1.32),.090,H if sign>0 else T,group,20)
    tube('Tail marker bezel',(ex+.22*sign,y,1.62),(ex+.285*sign,y,1.62),.042,M,group,12)
    tube('Tail marker glass',(ex+.29*sign,y,1.62),(ex+.30*sign,y,1.62),.029,T if sign>0 else H,group,12)
   box('Cab bumper anti-climber',(ex+sign*.30,0,.88),(.22,1.33,.14),D,group,.035)
   for k in range(8):box('Anti-climber ribs',(ex+sign*.42,-.55+k*.157,.88),(.015,.055,.11),M,group,.004,1)
   box('Driver desk',(ex-sign*.45,0,1.48),(.46,1.71,.20),D,group,.04)
   for y in [-.37,.37]:box('Driver instrument panel',(ex-sign*.38,y,1.66),(.21,.38,.035),B,group,.015)
  # centre coupling at each coach end, including rods and air hoses
  tube('Coupling shaft',(ex,0,.56),(ex+sign*.49,0,.56),.062,D,group,10)
  box('Knuckle coupler',(ex+sign*.46,0,.56),(.23,.23,.17),D,group,.045)
  for y in [-.42,.42]:tube('Buffer piston',(ex,y,.77),(ex+sign*.38,y,.77),.045,M,group,8)
  for y in [-.42,.42]:box('Buffer disc',(ex+sign*.40,y,.77),(.047,.24,.15),D,group,.035)
  for k in range(5):
   a=Vector((ex+sign*(.14+k*.043),.28,.64-k*.051));b=Vector((ex+sign*(.14+(k+1)*.043),.28,.64-(k+1)*.051));tube('Flexible air hose',a,b,.021,B,group,8)
 if ci in [1,2]:
  # compact diamond pantograph with four sprung links and contact strip
  px=cx+.25;box('Pantograph insulator base',(px,0,3.13),(.65,.65,.08),D,group,.023)
  for y in [-.27,.27]:
   tube('Pantograph lower arm',(px-.40,y,3.16),(px+.02,y,3.56),.022,D,group,8)
   tube('Pantograph upper arm',(px+.02,y,3.56),(px-.22,y,3.88),.017,M,group,8)
   tube('Pantograph bracing',(px+.35,y,3.16),(px-.02,y,3.56),.019,D,group,8)
  box('Pantograph carbon contact',(px-.22,0,3.895),(.14,.92,.047),D,group,.015)
  tube('Roof power conduit',(cx-4.9,.51,2.99),(cx+4.9,.51,2.99),.012,M,group,8)

# Genuine accordion bellows bridges between the coaches.
bridges=[]
for i in range(3):
 g=[];bridges.append(g);x=(centers[i]+centers[i+1])/2
 for k in range(10):
  bx=x-GAP/2+.05+k*(GAP-.1)/9
  for y in [-.46,.46]:box('Accordion gangway vertical fold',(bx,y,1.76),(.045,.10,1.71),B,g,.025)
  box('Accordion gangway top fold',(bx,0,2.61),(.045,.94,.085),B,g,.023)
  box('Accordion gangway lower fold',(bx,0,.915),(.045,.94,.065),B,g,.02)
 box('Gangway tread bridge',(x,0,.84),(GAP,.76,.038),D,g,.015)

# Editable file before optimization. All external paint images are packed.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24
scene.world.color=(.20,.20,.20)
for im in bpy.data.images:
 if im.name!='Render Result' and im.pixels:im.pack()
# Presentation: full continuous long train three-quarter viewpoint + close detailed coach view.
def point(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;point(o,(0,0,1));return o
area('Key softbox',(5,-13,15),6500,18,(1,.88,.70));area('Backlight',(-10,8,12),8000,22,(.70,.82,1));area('Cab fill',(30,-5,7),4000,12,(.96,.98,1))
camd=bpy.data.cameras.new('Train presentation camera');cam=bpy.data.objects.new('Train presentation camera',camd);bpy.context.collection.objects.link(cam);scene.camera=cam
cam.location=(37,-48,21);point(cam,(0,0,1.6));camd.type='ORTHO';camd.ortho_scale=60
scene.render.resolution_x=1800;scene.render.resolution_y=760;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
# Ground is preview-only, excluded from GLB.
preview=[];floor=box('Preview-only ground',(0,0,-.085),(130,100,.13),mat('Preview ground',(.065,.082,.086),.9),preview,.02);floor.parent=None
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'passenger-train.blend'))
scene.render.filepath=str(OUT/'passenger-train-preview.png');bpy.ops.render.render(write_still=True)
cam.location=(28,-18,8.5);point(cam,(16,0,1.55));camd.ortho_scale=16.5;scene.render.resolution_x=1500;scene.render.resolution_y=1000
scene.render.filepath=str(OUT/'passenger-train-detail.png');bpy.ops.render.render(write_still=True)
# Join only static coach parts. Door leaf geometry stays independently animated.
def join(objs,name,pivot=None):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;o.parent=root
 if pivot is not None:
  # origin geometry remains world-space; moves only the transform origin to slide anchor.
  old=bpy.context.scene.cursor.location.copy();bpy.context.scene.cursor.location=pivot;bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.context.scene.cursor.location=old
 return o
exports=[]
for i,g in enumerate(static):
 o=join(g,'Coach_%02d_Static'%(i+1),Vector((centers[i],0,0)));o['coach_index']=i;exports.append(o)
for i,g in enumerate(bridges):exports.append(join(g,'Gangway_%02d'%(i+1)))
door_notes=[]
for g,name,pivot,sign in door_sets:
 o=join(g,name,pivot);o['slide_axis']='X';o['slide_sign']=sign;o['slide_distance']=.575;exports.append(o)
 door_notes.append({'name':name,'slide':[sign*.575,0,0],'coach_index':int(name[6:8])-1})
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in exports:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'passenger-train.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
# GLTFLoader natively supports KHR_mesh_quantization. Compact normals use signed
# normalized bytes (four-byte vertex stride); positions stay full precision.
# This saves 2+ MB without requiring a Draco or meshopt decoder on the website.
pth=ASSETS/'passenger-train.glb';raw=pth.read_bytes();jlen=struct.unpack_from('<I',raw,12)[0]
j=json.loads(raw[20:20+jlen]);binstart=20+jlen+8;binlen=struct.unpack_from('<I',raw,20+jlen)[0];oldbin=raw[binstart:binstart+binlen]
normalids={p['attributes']['NORMAL'] for m in j['meshes'] for p in m['primitives'] if 'NORMAL' in p['attributes']};replacement={}
for ai in sorted(normalids):
 ac=j['accessors'][ai];vi=ac['bufferView'];bv=j['bufferViews'][vi]
 assert ac['componentType']==5126 and ac['type']=='VEC3'
 assert all(a.get('bufferView')!=vi or a is ac for a in j['accessors'])
 start=bv.get('byteOffset',0)+ac.get('byteOffset',0);stride=bv.get('byteStride',12);comp=bytearray()
 for i in range(ac['count']):
  vals=struct.unpack_from('<3f',oldbin,start+i*stride)
  comp.extend(struct.pack('<4b',*[max(-127,min(127,round(v*127))) for v in vals],0))
 replacement[vi]=bytes(comp);bv['byteStride']=4;ac['componentType']=5120;ac['normalized']=True;ac['byteOffset']=0;ac.pop('min',None);ac.pop('max',None)
newbin=bytearray()
for vi,bv in enumerate(j['bufferViews']):
 while len(newbin)%4:newbin.append(0)
 data=replacement.get(vi,oldbin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']])
 bv['byteOffset']=len(newbin);bv['byteLength']=len(data);newbin.extend(data)
while len(newbin)%4:newbin.append(0)
j['buffers'][0]['byteLength']=len(newbin)
for k in ['extensionsUsed','extensionsRequired']:
 j.setdefault(k,[])
 if 'KHR_mesh_quantization' not in j[k]:j[k].append('KHR_mesh_quantization')
js=json.dumps(j,separators=(',',':')).encode();js+=b' ' *((-len(js))%4)
result=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(newbin))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(newbin),0x004e4942)+newbin
pth.write_bytes(result)
tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in exports)
pts=[o.matrix_world @ Vector(c) for o in exports for c in o.bound_box]
bounds_bl=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
bounds=[[bounds_bl[0][0],bounds_bl[0][2],-bounds_bl[1][1]],[bounds_bl[1][0],bounds_bl[1][2],-bounds_bl[0][1]]]
info={'root':'PassengerTrain','coach_count':4,'coach_length_m':LENGTH,'coach_spacing_m':PITCH,'total_length_m':bounds[1][0]-bounds[0][0],'bounds_y_up':bounds,'track_z':3.72,'mesh_count':len(exports),'triangles':tri,'glb_bytes':pth.stat().st_size,'normal_encoding':'KHR_mesh_quantization signed normalized bytes; built-in GLTFLoader support','door_nodes':door_notes,'notes':'True passenger window openings and translucent glazing; 8 independently detailed bogies, interior bench seats and hand straps; roof vents and two pantographs. Source .blend preserves individual geometry and packed textures. Preview-only ground, cameras, lights excluded from GLB.'}
(ASSETS/'train-detail-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
shutil.copy2(__file__,OUT/'build_train.py')
print('TRAIN_COMPLETE',json.dumps({k:v for k,v in info.items() if k!='door_nodes'}))
