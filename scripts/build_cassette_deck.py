"""A physical cassette player and paper still-life for the film's opening.

All controls, the hinged lid, cassette, reels and earphone plug remain independent
nodes for the site to animate. No reference photograph is used as scene geometry.
Blender --background --factory-startup --python build_cassette_deck.py -- SITE OUT
"""
import bpy, bmesh, math, random, json, sys, struct
from pathlib import Path
from mathutils import Vector, Quaternion

random.seed(7527)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
SITE=Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
OUT=Path(args[1]).resolve() if len(args)>1 else SITE.parent.parent/'outputs'
ASSETS=SITE/'dist/assets'; ASSETS.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
ROOT=bpy.data.objects.new('CassetteOpening',None); bpy.context.collection.objects.link(ROOT)
ROOT['asset_role']='cassette-film-navigation'; ROOT['reference']='Original geometry inspired by paper, found objects and red wired earphones.'
groups={}; all_meshes=[]

def material(name,c,rough=.6,metal=0,alpha=1,transmission=0,noise=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*c,alpha); m.use_nodes=True
 n=m.node_tree.nodes; p=n.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,alpha)
 p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
 p.inputs['Alpha'].default_value=alpha; p.inputs['Transmission Weight'].default_value=transmission
 if alpha<1:
  try:m.surface_render_method='DITHERED'
  except:pass
 if noise:
  t=n.new('ShaderNodeTexNoise'); t.inputs['Scale'].default_value=140; t.inputs['Detail'].default_value=2
  b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=noise; b.inputs['Distance'].default_value=.006
  m.node_tree.links.new(t.outputs['Fac'],b.inputs['Height']); m.node_tree.links.new(b.outputs['Normal'],p.inputs['Normal'])
 return m

ivory=material('Player — warm ivory enamel',(.70,.69,.62),.34)
ivoryedge=material('Player — softly worn ivory edges',(.86,.84,.74),.43)
navy=material('Player — deep midnight blue',(.028,.058,.093),.31)
navysoft=material('Paper label — indigo ink',(.035,.070,.116),.88)
silver=material('Player — brushed aluminium',(.49,.51,.50),.30,.82)
chrome=material('Jack — nickel plated metal',(.64,.66,.64),.18,.88)
black=material('Mechanism — soft black rubber',(.013,.016,.016),.72)
tape=material('Magnetic tape — brown oxide',(.068,.037,.018),.35)
smoky=material('Cassette — smoky transparent resin',(.43,.56,.60),.17,.03,.18)
clearglass=material('Door — transparent pale glass',(.56,.70,.75),.12,.04,.14)
reelivory=material('Cassette — ivory nylon reels',(.77,.77,.68),.45)
red=material('Earphones — deep red flexible vinyl',(.48,.009,.016),.31)
redbright=material('Earphones — red polished shell',(.62,.015,.022),.24)
earfoam=material('Earphones — black speaker grille',(.018,.012,.011),.83)
paper=material('Paper — uncoated warm white',(.81,.79,.73),.96,noise=.18)
paperwhite=material('Paper — ivory label strip',(.89,.88,.80),.96,noise=.10)
craft=material('Paper — brown envelope',(.48,.35,.19),.93,noise=.19)
greycard=material('Paper — stone gray backing',(.56,.57,.55),.98,noise=.18)
mask=material('Paper — translucent masking tape',(.79,.67,.39),.97)
ink=material('Paper — graphite printing',(.058,.064,.067),.95)
fiber=material('Paper — tiny cream edge fibres',(.81,.77,.65),.98)
thread=material('Paper — twisted natural cotton thread',(.53,.43,.28),.91)
deskmat=material('Table — pale warm gray linoleum',(.55,.56,.54),.82,noise=.12)
whiteink=material('Label — off-white printing',(.84,.84,.77),.94)

def empty(name,pos=(0,0,0),parent=ROOT):
 o=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(o); o.location=pos; o.parent=parent; return o
DESK=empty('DeskStillLife'); PLAYER=empty('Player',(1.10,.35,0)); BAY=empty('CassetteBay',(0,0,0),PLAYER)
CASSETTE=empty('Cassette',(-1.68,-.58,.205)); CASSETTE.rotation_euler.z=math.radians(-11)
COVER=empty('DoorPivot',(0,1.32,1.077),PLAYER)
COVER.rotation_euler.x=math.radians(-67)
EARPHONES=empty('Earphones'); JACK=empty('JackPlug',(-.64,-1.95,.145)); JACK.rotation_euler.z=math.radians(-13)

def reg(o,m,parent,group):
 if m:o.data.materials.append(m)
 o.parent=parent; all_meshes.append(o)
 if group:groups.setdefault((parent.name,group),[]).append(o)
 return o
def mesh(name,vs,fs,m,parent=ROOT,group=None):
 d=bpy.data.meshes.new(name); d.from_pydata(vs,[],fs); d.update()
 o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); return reg(o,m,parent,group)
def cube(name,pos,size,m,parent=ROOT,bevel=.01,group=None):
 bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=4,affect='EDGES',clamp_overlap=True)
 d=bpy.data.meshes.new(name); bm.to_mesh(d);bm.free();d.update()
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos
 return reg(o,m,parent,group)
def cyl(name,pos,r,depth,m,parent=ROOT,vertices=40,group=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=pos)
 o=bpy.context.object;o.name=name
 for f in o.data.polygons:f.use_smooth=True
 return reg(o,m,parent,group)
def ellipsoid(name,pos,size,m,parent=ROOT,group=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=1,location=pos)
 o=bpy.context.object;o.name=name;o.scale=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for f in o.data.polygons:f.use_smooth=True
 return reg(o,m,parent,group)
def ring(name,pos,radius,minor,m,parent=ROOT,group=None,major=60,minor_seg=10):
 bpy.ops.mesh.primitive_torus_add(major_segments=major,minor_segments=minor_seg,location=pos,major_radius=radius,minor_radius=minor)
 o=bpy.context.object;o.name=name
 for f in o.data.polygons:f.use_smooth=True
 return reg(o,m,parent,group)
def tube(name,points,r,m,parent=ROOT,group=None,seg=10):
 vs=[]; fs=[]
 for j,point in enumerate(points):
  p=Vector(point);d=Vector(points[min(len(points)-1,j+1)])-Vector(points[max(0,j-1)])
  d.normalize();u=d.cross(Vector((0,0,1)))
  if u.length<.01:u=d.cross(Vector((0,1,0)))
  u.normalize();v=d.cross(u)
  for k in range(seg):a=math.tau*k/seg;vs.append(tuple(p+r*(math.cos(a)*u+math.sin(a)*v)))
 for j in range(len(points)-1):
  for k in range(seg):a=j*seg+k;b=j*seg+(k+1)%seg;fs.append((a,b,b+seg,a+seg))
 fs.extend([tuple(range(seg-1,-1,-1)),tuple((len(points)-1)*seg+k for k in range(seg))])
 o=mesh(name,vs,fs,m,parent,group)
 for f in o.data.polygons:f.use_smooth=True
 return o
def beam(name,a,b,r,m,parent=ROOT,group=None):return tube(name,[a,b],r,m,parent,group,12)
def lettering(name,text,pos,size,m,parent=ROOT,group=None,font='latin',align='LEFT'):
 d=bpy.data.curves.new(name,'FONT');d.body=text;d.size=size;d.extrude=.0008;d.bevel_depth=.00035;d.bevel_resolution=1;d.align_x=align;d.space_character=1.08
 if font=='cjk':d.font=CJK
 else:d.font=LATIN
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;o.parent=parent;d.materials.append(m)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 o=bpy.context.object;all_meshes.append(o)
 if group:groups.setdefault((parent.name,group),[]).append(o)
 return o

CJK=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
LATIN=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Andale Mono.ttf')

# Off-white paper objects sit above a softly rounded desk, with real folded edges.
cube('Desk slab',(0,0,-.18),(8.25,6.35,.30),deskmat,DESK,.12,'Desk_static')
card=empty('OpeningPaper',(-.20,-.06,.015),DESK);card.rotation_euler.z=math.radians(-3)
cube('Thick uncoated main sheet',(0,0,0),(6.08,4.77,.045),paper,card,.015,'Paper_main')
for i in range(36):
 x=random.uniform(-2.92,2.93);y=random.choice([-2.38,2.38]);z=random.uniform(.013,.027)
 beam('Deckle paper edge',(x,y,z),(x+random.uniform(.015,.052),y+random.uniform(-.012,.012),z),.0018,fiber,card,'Paper_main')
cube('Gray mounting card',(-1.57,.99,.066),(2.61,2.43,.060),greycard,card,.025,'Paper_main')
env=empty('Envelope',(-1.59,1.22,.107),card);env.rotation_euler.z=math.radians(5)
cube('Kraft envelope body',(0,0,0),(2.05,1.97,.055),craft,env,.015,'Envelope_static')
# A triangular flap has a visible paper fold and shadow.
mesh('Envelope folded flap',[(-1.01,.95,.038),(1.01,.95,.038),(.08,-.10,.065)],[ (0,1,2) ],craft,env,'Envelope_static')
beam('Envelope center crease',(-1,.93,.045),(1,.93,.045),.0038,fiber,env,'Envelope_static')
cube('Ivory correspondence strip',(0,.55,.068),(1.79,.41,.018),paperwhite,env,.004,'Envelope_static')
lettering('Film title on envelope','老派约会之必要',(-.81,.46,.080),.157,ink,env,'Envelope_static','cjk')
cube('Envelope blue track strip',(-.42,-.08,.061),(.97,.23,.020),navysoft,env,.002,'Envelope_static')
lettering('Envelope mixtape side','SIDE A',(-.84,-.125,.078),.10,whiteink,env,'Envelope_static')
lettering('Envelope date marker','A FILM IN SIX TRACKS',(-.89,-.72,.052),.086,ink,env,'Envelope_static')
# Torn tape strips, stitch and a bow are separate physical volumes.
for x,y,ang in [(-2.69,1.05,-7),(-.47,1.78,14)]:
 o=cube('Envelope masking tape',(x,y,.146),(.63,.15,.027),mask,card,.004,'Paper_main');o.rotation_euler.z=math.radians(ang)
bow=[(-2.20,1.85,.19),(-2.30,2.04,.19),(-2.60,2.03,.19),(-2.71,1.86,.19),(-2.47,1.73,.19),(-2.20,1.85,.20),(-2.03,2.10,.20),(-1.75,2.12,.20),(-1.72,1.94,.20),(-1.96,1.78,.20),(-2.20,1.85,.20),(-2.54,1.46,.17),(-2.48,1.28,.16)]
tube('Cotton bow and trailing thread',bow,.015,thread,card,'Paper_main',12)
ring('Cotton knot',(-2.20,1.85,.197),.053,.018,thread,card,'Paper_main',28,8)
# Original, quiet track notes; no copied song lyrics or opening-credit collage.
note=empty('TrackReceipt',(.60,-1.69,.073),card);note.rotation_euler.z=math.radians(6)
cube('Receipt backing',(0,0,0),(2.28,.91,.025),paperwhite,note,.004,'Receipt_static')
cube('Receipt indigo title',(0,.25,.018),(2.06,.18,.012),navysoft,note,.002,'Receipt_static')
lettering('Mixtape title','SIX TRACKS / TWO DATES',(-.93,.211,.029),.074,whiteink,note,'Receipt_static')
for i,txt in enumerate(['01  ARRIVE    02  MEET','03  TALK      04  STAY','05 WALK HOME  06 RETURN']):lettering('Printed track index '+str(i),txt,(-.93,.06-i*.17,.017),.076,ink,note,'Receipt_static')
for x in [-1.115,1.115]:
 for y in [-.31,-.14,.03,.20,.37]:
  cyl('Receipt torn binder hole',(x,y,.017),.020,.031,deskmat,note,12,'Receipt_static')
o=cube('Receipt masking tape',(.21,-.40,.038),(.57,.12,.025),mask,note,.005,'Receipt_static');o.rotation_euler.z=.08

# The portable player is a full enclosure with visible seams, screws and controls.
cube('Player lower enclosure',(0,0,.345),(3.48,2.93,.67),ivory,PLAYER,.105,'Player_static')
cube('Player bottom shadow seam',(0,0,.145),(3.491,2.942,.018),navy,PLAYER,.065,'Player_static')
cube('Player upper metal rim',(0,0,.666),(3.465,2.915,.087),silver,PLAYER,.062,'Player_static')
cube('Player indigo upper fascia',(0,0,.714),(3.335,2.775,.047),navy,PLAYER,.052,'Player_static')
cube('Player lower front metal accent',(0,-1.443,.40),(2.64,.036,.15),silver,PLAYER,.015,'Player_static')
for x in [-1.42,1.42]:
 for y in [-1.23,1.23]:
  cyl('Case recessed screw',(x,y,.743),.047,.014,chrome,PLAYER,24,'Player_static')
  cube('Screw cross slot horizontal',(x,y,.754),(.052,.008,.005),black,PLAYER,.001,'Player_static')
  cube('Screw cross slot vertical',(x,y,.754),(.008,.052,.005),black,PLAYER,.001,'Player_static')
for x in [-1.2,-.72,-.24,.24,.72,1.2]:
 cube('Front recessed speaker slit',(x,-1.466,.342),(.255,.008,.025),black,PLAYER,.008,'Player_static')
cube('Front carry-strap lug',(-1.783,-.87,.43),(.15,.29,.115),silver,PLAYER,.019,'Player_static')
cube('Strap lug aperture',(-1.868,-.87,.43),(.02,.17,.05),black,PLAYER,.004,'Player_static')
for y in [-1.04,-.88,-.72,-.56,-.40,-.24,-.08,.08]:
 cube('Right side cooling seam',(1.748,y,.345),(.012,.075,.025),black,PLAYER,.004,'Player_static')
# The cavity has a raised mechanical floor and a real tape head; cassette fits here.
cube('Bay mechanism well',(0,.01,.742),(2.94,2.39,.031),black,BAY,.023,'Bay_mechanism')
cube('Bay inner metal plate',(0,.08,.763),(2.73,2.13,.010),silver,BAY,.021,'Bay_mechanism')
for x in [-1.46,1.46]:cube('Bay elevated side casing',(x,.05,.899),(.095,2.40,.295),ivoryedge,BAY,.018,'Bay_mechanism')
for y in [-1.10,1.21]:cube('Bay elevated end casing',(0,y,.898),(2.90,.095,.295),ivoryedge,BAY,.018,'Bay_mechanism')
for x in [-.62,.62]:
 cyl('Bay drive spindle',(x,-.03,.827),.105,.10,black,BAY,32,'Bay_mechanism')
 cyl('Bay spindle pin',(x,-.03,.893),.031,.063,chrome,BAY,24,'Bay_mechanism')
 for a in range(6):
  angle=a*math.tau/6;o=cube('Bay spindle tooth',(x+.112*math.cos(angle),-.03+.112*math.sin(angle),.846),(.052,.028,.045),black,BAY,.004,'Bay_mechanism');o.rotation_euler.z=angle
cube('Tape read head',(0,-.954,.828),(.31,.115,.111),chrome,BAY,.018,'Bay_mechanism')
cube('Tape read head magnetic contact',(0,-1.019,.853),(.23,.009,.040),black,BAY,.004,'Bay_mechanism')
for x in [-1.03,1.03]:
 cyl('Bay pinch roller',(x,-.81,.805),.091,.076,black,BAY,32,'Bay_mechanism')
 cyl('Bay guide roller',(x,-.61,.829),.034,.09,chrome,BAY,24,'Bay_mechanism')
# Hinged front cover. Window is transparent, not an image of the tape.
cube('Door top border',(0,-.10,.018),(3.13,.18,.078),ivoryedge,COVER,.023,'Cover_parts')
cube('Door front border',(0,-2.47,.018),(3.13,.18,.078),ivoryedge,COVER,.023,'Cover_parts')
for x in [-1.48,1.48]:cube('Door side border',(x,-1.285,.018),(.17,2.45,.078),ivoryedge,COVER,.023,'Cover_parts')
cube('Door clear protective window',(0,-1.285,.025),(2.88,2.21,.023),clearglass,COVER,.023,'Cover_parts')
for x in [-1.02,1.02]:
 hinge=cyl('Door stainless hinge',(x,0,.003),.078,.32,silver,COVER,32,'Cover_parts');hinge.rotation_euler.y=math.pi/2
cube('Door tiny handle',(0,-2.538,.027),(.64,.10,.095),silver,COVER,.025,'Cover_parts')
lettering('Player cover legend','PORTABLE MEMORY',(0,-2.472,.064),.095,navy,COVER,'Cover_parts',align='CENTER')
lettering('Player cover model','STEREO  /  TYPE I',(0,-.09,.064),.069,navy,COVER,'Cover_parts',align='CENTER')
# Physically separate buttons have top symbols and tactile grooves.
buttons={}
for i,(node,label) in enumerate([('ButtonRewind','<<'),('ButtonPlay','>'),('ButtonStop','[]'),('ButtonForward','>>')]):
 x=-1.08+i*.72;b=empty(node,(x,-1.273,.761),PLAYER);buttons[node]=b
 cube(node+' cap',(0,0,0),(.59,.245,.086),silver if node!='ButtonPlay' else ivoryedge,b,.018,node+'_parts')
 for yy in [-.083,.083]:cube(node+' edge grip',(0,yy,.046),(.40,.009,.006),navy,b,.002,node+'_parts')
 lettering(node+' symbol',label,(0,-.035,.048),.102,navy,b,node+'_parts',align='CENTER')
 cube(node+' seam',(0,0,-.049),(.64,.27,.018),black,b,.008,node+'_parts')
# Left edge volume thumb-wheel and graduated marks.
knob=empty('VolumeWheel',(-1.75,.63,.419),PLAYER)
v=cyl('Volume wheel rubber hub',(0,0,0),.211,.096,black,knob,64,'Volume_parts');v.rotation_euler.y=math.pi/2
for i in range(35):
 a=i*math.tau/35;o=cube('Volume wheel serration',(-.006,.211*math.sin(a),.211*math.cos(a)),(.109,.018,.028),navy,knob,.003,'Volume_parts');o.rotation_euler.x=-a
lettering('Volume engraving','VOL',(-1.55,.605,.741),.072,whiteink,PLAYER,'Player_static')
# The headphones jack is a radial socket in the right side of the machine.
port=cyl('HeadphoneSocket',(1.759,.82,.474),.123,.027,chrome,PLAYER,48,'Player_static');port.rotation_euler.y=math.pi/2
hole=cyl('HeadphoneSocketCenter',(1.781,.82,.474),.072,.030,black,PLAYER,40,'Player_static');hole.rotation_euler.y=math.pi/2
lettering('Jack top legend','PHONES',(1.22,.737,.741),.074,whiteink,PLAYER,'Player_static')

# A detailed compact cassette, smoky shell with nylon hubs and magnetic tape.
cube('Cassette bottom resin panel',(0,0,-.056),(2.55,1.615,.041),smoky,CASSETTE,.036,'Cassette_shell')
for y in [-.764,.764]:cube('Cassette moulded long rim',(0,y,.039),(2.55,.09,.214),smoky,CASSETTE,.025,'Cassette_shell')
for x in [-1.23,1.23]:cube('Cassette moulded end rim',(x,0,.039),(.09,1.49,.214),smoky,CASSETTE,.022,'Cassette_shell')
# Top cover divided into window frames so the reel openings remain genuinely open.
for y,h in [(.625,.22),(-.634,.23)]:cube('Cassette label perimeter',(0,y,.126),(2.34,h,.026),smoky,CASSETTE,.018,'Cassette_shell')
for x in [-1.06,0,1.06]:cube('Cassette window mullion',(x,0,.119),(.10,1.09,.027),smoky,CASSETTE,.008,'Cassette_shell')
for x in [-.62,.62]:
 ring('Cassette reel aperture rim',(x,-.03,.138),.282,.018,smoky,CASSETTE,'Cassette_shell',64,12)
for x in [-1.12,1.12]:
 for y in [-.62,.62]:
  cyl('Cassette silver screw',(x,y,.156),.048,.017,chrome,CASSETTE,28,'Cassette_shell')
  cube('Cassette screw slot',(x,y,.167),(.055,.009,.005),black,CASSETTE,.001,'Cassette_shell')
cube('Cassette top paper label',(0,.568,.147),(1.93,.325,.024),paperwhite,CASSETTE,.006,'Cassette_shell')
lettering('Cassette original title','老派约会之必要',(-.865,.550,.163),.130,navysoft,CASSETTE,'Cassette_shell','cjk')
cube('Cassette lower ink label',(0,-.590,.147),(1.89,.236,.019),navysoft,CASSETTE,.003,'Cassette_shell')
lettering('Cassette side / track count','A   /   01—05',(0,-.627,.162),.089,whiteink,CASSETTE,'Cassette_shell',align='CENTER')
lettering('Cassette upper fine print','NORMAL POSITION  /  STEREO',(-.92,.660,.163),.046,navysoft,CASSETTE,'Cassette_shell')
# Ribbon crosses beneath two independent rotating reels, wrapping the guides.
tube('Exposed magnetic ribbon',[(-.97,-.71,.043),(-1.02,-.49,.043),(-.75,-.36,.043),(0,-.36,.043),(.77,-.37,.043),(1.03,-.48,.043),(.98,-.71,.043)],.017,tape,CASSETTE,'Cassette_shell',8)
for x in [-.96,.96]:cyl('Cassette guide pin',(x,-.63,.05),.035,.133,chrome,CASSETTE,24,'Cassette_shell')
for name,x,rad in [('ReelLeft',-.62,.46),('ReelRight',.62,.40)]:
 r=empty(name,(x,-.03,.011),CASSETTE);r['rotation_axis']='glTF local Y';r['role']='magnetic-tape-reel'
 cyl(name+' magnetic winding',(0,0,.026),rad,.063,tape,r,80,name+'_parts')
 for radius in [rad-.015,rad-.035,rad-.055,rad-.075]:ring(name+' winding line',(0,0,.061),radius,.0025,black,r,name+'_parts',80,6)
 ring(name+' outer nylon ring',(0,0,.079),.238,.024,reelivory,r,name+'_parts',64,12)
 ring(name+' inner nylon ring',(0,0,.083),.101,.018,reelivory,r,name+'_parts',48,10)
 for k in range(6):
  a=k*math.tau/6;v=cube(name+' radial spoke',(.163*math.cos(a),.163*math.sin(a),.082),(.132,.048,.035),reelivory,r,.005,name+'_parts');v.rotation_euler.z=a
  v=cube(name+' drive tooth',(.104*math.cos(a),.104*math.sin(a),.086),(.060,.027,.045),reelivory,r,.003,name+'_parts');v.rotation_euler.z=a
 cyl(name+' center dark bore',(0,0,.064),.084,.028,black,r,32,name+'_parts')
 ring(name+' hub raised lip',(0,0,.105),.109,.010,reelivory,r,name+'_parts',48,10)

# Red wired earphones draw an irregular, physical looping line across the paper.
# Dense sampling follows cubic Bezier segments: the cable has no angular corners.
def bezier(points,count=32):
 out=[]
 for p0,p1,p2,p3 in points:
  for j in range(count):
   t=j/count;s=1-t;p=(Vector(p0)*s**3+Vector(p1)*3*s*s*t+Vector(p2)*3*s*t*t+Vector(p3)*t**3);out.append(tuple(p))
 out.append(tuple(points[-1][-1]));return out
z=.091
segments=[
 ((-.84,-1.95,z),(-1.50,-2.14,z),(-3.25,-1.96,z),(-3.27,-.91,z)),
 ((-3.27,-.91,z),(-3.34,.10,z),(-2.61,.37,z),(-2.01,.13,z)),
 ((-2.01,.13,z),(-1.20,-.29,z),(-1.15,-1.26,z),(-2.13,-1.43,z)),
 ((-2.13,-1.43,z),(-3.01,-1.46,z),(-3.05,-.48,z+.02),(-2.47,-.22,z+.02)),
 ((-2.47,-.22,z+.02),(-1.65,.20,z+.03),(-.65,-.19,z+.02),(-.68,-.91,z+.02)),
 ((-.68,-.91,z+.02),(-.76,-1.70,z+.03),(-1.61,-1.96,z+.03),(-1.72,-1.27,z+.03)),
 ((-1.72,-1.27,z+.03),(-1.86,-.62,z+.05),(-2.09,-.52,z+.05),(-2.04,-.07,z+.05)),
]
tube('EarphoneCable',bezier(segments),.018,red,EARPHONES,'Earphones_static',12)
split=(-2.04,-.07,.15)
for budname,dest,control in [('EarbudLeft',(-2.70,.34,.172),(-2.84,-.12,.11)),('EarbudRight',(-.71,-.06,.169),(-1.56,-.37,.11))]:
 pts=bezier([(split,control,(dest[0],dest[1]-.26,.14),dest)])
 tube(budname+' cord',pts,.013,red,EARPHONES,'Earphones_static',10)
 b=empty(budname,dest,EARPHONES);b.rotation_euler.z=math.radians(17 if 'Left' in budname else -23)
 ellipsoid(budname+' glossy shell',(0,0,.035),(.113,.147,.087),redbright,b,budname+'_parts')
 ellipsoid(budname+' eartip',(.031,.025,.089),(.074,.083,.048),red,b,budname+'_parts')
 g=cyl(budname+' speaker grille',(.032,.026,.133),.063,.008,earfoam,b,40,budname+'_parts')
 for i in range(16):
  a=i*math.tau/16;x=.032+.043*math.cos(a);y=.026+.043*math.sin(a)
  cyl(budname+' grille perforation',(x,y,.138),.0045,.004,chrome,b,8,budname+'_parts')
 cube(budname+' stem',(0,-.11,.014),(.059,.139,.061),redbright,b,.017,budname+'_parts')
 lettering(budname+' channel','L' if 'Left' in budname else 'R',(-.019,-.080,.050),.040,paperwhite,b,budname+'_parts')
ellipsoid('Earphones cable Y split',split,(.035,.063,.027),redbright,EARPHONES,'Earphones_static')
# Small cylindrical inline volume remote.
remote=empty('EarphoneRemote',(-3.15,-.37,.113),EARPHONES);remote.rotation_euler.z=math.radians(-10)
cube('Earphone inline controller',(0,0,0),(.106,.41,.10),redbright,remote,.034,'Remote_parts')
cube('Earphone inline slider',(0,0,.054),(.050,.17,.012),red,remote,.006,'Remote_parts')
cube('Earphone inline slider finger',(0,.01,.066),(.053,.055,.018),silver,remote,.005,'Remote_parts')
# Jack tip lies outside the player initially, ready to swing into its socket.
body=cyl('Jack red rubber barrel',(-.073,0,0),.080,.244,redbright,JACK,40,'Jack_parts');body.rotation_euler.y=math.pi/2
beam('Jack red strain relief',(-.31,0,0),(-.185,0,0),.052,red,JACK,'Jack_parts')
for x in [-.27,-.235,-.20]:
 t=ring('Jack strain relief groove',(x,0,0),.052,.007,redbright,JACK,'Jack_parts',32,8);t.rotation_euler.y=math.pi/2
pin=cyl('Jack 3.5mm metal pin',(.155,0,0),.043,.31,chrome,JACK,32,'Jack_parts');pin.rotation_euler.y=math.pi/2
for x in [.12,.22]:
 band=cyl('Jack insulating ring',(x,0,0),.044,.022,black,JACK,32,'Jack_parts');band.rotation_euler.y=math.pi/2
ellipsoid('Jack round nickel tip',(.309,0,0),(.037,.043,.043),chrome,JACK,'Jack_parts')
cube('Jack small red stop collar',(.005,0,0),(.034,.181,.181),red,JACK,.043,'Jack_parts')

# Keep an editable source before reducing meshes for the runtime package.
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.world.color=(.45,.45,.45)
world=scene.world;world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.58,.61,.62,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.45
def area(name,pos,power,size,color):
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;d.energy=power;d.shape='DISK';d.size=size;d.color=color;o.rotation_euler=(Vector((0,0,.3))-o.location).to_track_quat('-Z','Y').to_euler()
area('Broad soft daylight',(-4,-3,8),700,5.5,(1,.91,.75))
area('Cool reflected sky',(4,2,6),480,4.0,(.78,.87,1))
area('Soft highlight for aluminium',(-1,5,4),280,3.0,(1,.95,.85))
camd=bpy.data.cameras.new('Cassette opening camera');camera=bpy.data.objects.new('Cassette opening camera',camd);bpy.context.collection.objects.link(camera)
camera.location=(0,-7.3,8.4);camera.rotation_euler=(Vector((-.10,.12,.37))-camera.location).to_track_quat('-Z','Y').to_euler();camd.type='PERSP';camd.lens=46;scene.camera=camera
scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.20
for f in bpy.data.fonts:
 if f.filepath:
  try:f.pack()
  except:pass
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'cassette-deck.blend'))
scene.render.filepath=str(OUT/'cassette-deck-preview.png');bpy.ops.render.render(write_still=True)

# Batch static objects within each animated node. Each player control keeps a root.
for (parent_name,name),objects in groups.items():
 if not objects:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name=name
for o in bpy.data.objects:
 if o.type=='MESH':
  o.data.update()
  # Tiny bevels have face normals; auto-smooth faceting is kept at actual hard edges.
  for p in o.data.polygons:
   if len(p.vertices)>4:p.use_smooth=False

bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type in {'MESH','EMPTY'}:o.select_set(True)
glb_path=ASSETS/'cassette-deck.glb'
bpy.ops.export_scene.gltf(filepath=str(glb_path),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_yup=True,export_cameras=False,export_lights=False,export_animations=False)

# Runtime material base colours remain explicit even when Blender has paper bumps.
data=glb_path.read_bytes(); jsonlen=struct.unpack_from('<I',data,12)[0]; doc=json.loads(data[20:20+jsonlen])
for m in doc.get('materials',[]):
 pbr=m.setdefault('pbrMetallicRoughness',{})
 if 'baseColorFactor' not in pbr and 'baseColorTexture' not in pbr:
  original=bpy.data.materials.get(m.get('name',''))
  if original:pbr['baseColorFactor']=list(original.diffuse_color)
chunks=[];cursor=12
while cursor<len(data):
 length,kind=struct.unpack_from('<II',data,cursor);payload=data[cursor+8:cursor+8+length]
 if kind==0x4e4f534a:
  payload=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();payload+=b' '*((-len(payload))%4)
 chunks.append(struct.pack('<II',len(payload),kind)+payload);cursor+=8+length
packed=b''.join(chunks);glb_path.write_bytes(struct.pack('<III',0x46546c67,2,len(packed)+12)+packed)

def gltf_point(p):return [round(p[0],5),round(p[2],5),round(-p[1],5)]
def gltf_quat(q):
 # Blender-to-glTF coordinate basis, not the exporter's per-node Euler values.
 basis=Quaternion((1,0,0),-math.pi/2);r=basis@q@basis.inverted();return [round(r.x,6),round(r.y,6),round(r.z,6),round(r.w,6)]
info={
 'title':'老派约会之必要 — portable memory player',
 'coordinate_system':'glTF / Three.js Y-up. Coordinates below are in asset root space.',
 'genuine_geometry':True,'photograph_planes':False,
 'bounds':{'min':[-4.2,-.34,-3.2],'max':[4.2,3.42,3.2]},
 'root_name':'CassetteOpening',
 'node_parents':{'Cassette':'CassetteOpening','JackPlug':'CassetteOpening','DoorPivot':'Player','ReelLeft':'Cassette','ReelRight':'Cassette','Player':'CassetteOpening','Earphones':'CassetteOpening'},
 'camera':{'pos':[0,8.4,7.3],'position':[0,8.4,7.3],'target':[-.10,.37,-.12],'fov':33,'wide_fov':43},
 'mobile_camera':{'position':[0,10.8,9.4],'target':[-.10,.37,-.12],'fov':50},
 'cassette':{'node':'Cassette','start':{'position':gltf_point(CASSETTE.location),'quaternion':gltf_quat(CASSETTE.rotation_euler.to_quaternion())},'insertPosition':gltf_point((1.10,.35,.862)),'insertRotation':[0,0,0],'inserted':{'position':gltf_point((1.10,.35,.862)),'quaternion':[0,0,0,1]},'approach':gltf_point((1.10,.35,2.10)),'local_size':[2.55,.243,1.615],'reel_nodes':['ReelLeft','ReelRight'],'reel_axis':[0,1,0],'reel_spin_rad_per_second':2.7},
 'door':{'node':'DoorPivot','local_hinge_position':gltf_point(COVER.location),'axis':'x','axisVector':[1,0,0],'open':math.radians(-67),'closed':0,'open_angle':math.radians(-67),'closed_angle':0},
 'jack':{'node':'JackPlug','start':{'position':gltf_point(JACK.location),'quaternion':gltf_quat(JACK.rotation_euler.to_quaternion())},'insertPosition':gltf_point((3.18,1.17,.474)),'insertRotation':[0,-math.pi,0],'inserted':{'position':gltf_point((3.18,1.17,.474)),'quaternion':gltf_quat(Quaternion((0,0,1),math.pi))},'socket_position':gltf_point((2.88,1.17,.474)),'tip_axis':[1,0,0]},
 'earphones':{'root':'Earphones','buds':['EarbudLeft','EarbudRight'],'cable_node':'Earphones_static','headphone_lift_offset':[0,1.5,.6]},
 'controls':{name:{'node':name,'depression_axis':[0,-1,0],'depression_distance':.037,'root_position':gltf_point(Vector((1.10,.35,0))+b.location)} for name,b in buttons.items()},
 'volume':{'node':'VolumeWheel','axis':[1,0,0]},
 'track_count':5,'suggested_sequence':['Lift cassette','Move above bay','Lower cassette','Close hinged door','Insert red headphones jack','Press play','Spin both tape reels','Travel into track 01'],
 'static_meshes':len([o for o in bpy.data.objects if o.type=='MESH']),
 'triangles':sum(len(p.vertices)-2 for o in bpy.data.objects if o.type=='MESH' for p in o.data.polygons),
 'materials':len(doc.get('materials',[])),'file_size_bytes':glb_path.stat().st_size,
}
(ASSETS/'cassette-deck-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
(OUT/'cassette-deck-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
print(json.dumps(info,ensure_ascii=False,indent=2))
