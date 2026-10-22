"""Editable vintage diner built in Blender from IMG_1820.JPG.
All architecture, props and generic adult performers are geometric models.
No photographic background or borrowed art. Blender --background --python ... -- SITE OUTPUTS
"""
import bpy,bmesh,math,random,json,sys,shutil,struct
from pathlib import Path
from mathutils import Vector
random.seed(1820)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
SITE=Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
OUT=Path(args[1]).resolve() if len(args)>1 else SITE.parent.parent/'outputs'
ASSETS=SITE/'dist/assets'
ASSETS.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
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
  mesh(name+' pointed collar',vs,[(0,1,2,3)],shirt,body)
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
  elbows=[(-.27,.06,1.46),(.28,.03,1.48)];wrists=[(-.15,-.29,1.44),(.09,-.33,1.45)]
 else:
  elbows=[(-.28,.05,1.48),(.26,.03,1.48)];wrists=[(-.13,-.31,1.45),(.11,-.30,1.44)]
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
 h=join(head,name+'Head');h.location=(0,.39,1.98);h.rotation_euler.z=0;h.parent=root
 # Actor body includes multiple retained materials but one efficient draw hierarchy.
 b=join(body,name+'Body');b.parent=root
 return root

# Physical surfaces: the original procedural meshes remain in the editable source.
sage=mat('Diner sage lime plaster',(.225,.345,.208),.87,noise=.14,scale=105)
dados=mat('Deep sage painted wainscot',(.080,.154,.120),.54,noise=.08,scale=80)
wood=mat('Rubbed walnut trim',(.125,.055,.028),.35,noise=.20,scale=10)
red=mat('Polished oxblood red laminate',(.41,.025,.012),.19,noise=.10,scale=115)
chrome=mat('Brushed chrome metal',(.51,.57,.56),.20,.92)
chrome_dark=mat('Recessed black nickel',(.070,.079,.073),.29,.80)
cream=mat('Warm milk white ceramic',(.76,.70,.55),.22)
black=mat('Dark charcoal recess',(.018,.025,.022),.50)
tileA=mat('Cream terrazzo tile',(.51,.47,.34),.57,noise=.20,scale=155)
tileB=mat('Muted green floor tile',(.117,.201,.157),.51,noise=.16,scale=180)
vinyl=mat('Bottle green booth upholstery',(.032,.096,.058),.40,noise=.06,scale=200)
vinyl_piping=mat('Booth leather piping',(.100,.142,.084),.40)
marble=mat('Cream speckled counter stone',(.57,.52,.40),.51,noise=.24,scale=165)
glow=mat('DinerPracticalGlow',(.94,.77,.42),.38)
p=glow.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.67,.26,1);p.inputs['Emission Strength'].default_value=2.1
frost=mat('Frosted ribbed glass warm white',(.85,.68,.37),.44)
glass=mat('Condiment soft smoky glass',(.35,.29,.12),.18,.06)
coffee=mat('Black coffee liquid',(.026,.012,.004),.18)
paper=mat('Folded recycled paper napkin',(.62,.52,.31),.98)
ketchup=mat('Vintage red condiment bottle',(.30,.025,.005),.34)
mustard=mat('Vintage amber condiment bottle',(.59,.35,.013),.34)
navy=mat('Performer navy knitted sweater',(.024,.034,.056),.95,noise=.12,scale=210)
whitecloth=mat('Performer warm stone chinos',(.47,.43,.34),.92,noise=.10,scale=165)
shirt=mat('Performer pale blue shirt',(.18,.37,.44),.90)
slate=mat('Performer brown houndstooth jacket',(.22,.13,.059),.94)
skirt=mat('Performer brown wool skirt',(.22,.13,.059),.94,noise=.14,scale=180)
boots=mat('Performer dark polished leather',(.022,.018,.012),.37)
shoe=mat('Performer soft leather shoes',(.048,.032,.019),.44)
sole=mat('Performer tan rubber sole',(.29,.23,.15),.84)
skin=mat('Warm natural skin',(.58,.36,.23),.79)
p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.09
hair=mat('Dark chocolate hair',(.027,.016,.011),.69)
hairlight=mat('Hair soft ridge',(.050,.030,.018),.70)
eye=mat('Eyes warm dark brown',(.019,.010,.005),.37)
eyewhite=mat('Subtle eye sclera',(.52,.47,.38),.72)
lip=mat('Muted terracotta lips',(.27,.093,.065),.86)
olive=shirt;brass=chrome;creamwall=whitecloth
# A tiny original woven plaid bitmap for jacket UVs, rather than unexportable nodes.
img=bpy.data.images.new('Original brown wool plaid',width=128,height=128,alpha=False)
pixels=[]
for j in range(128):
 for i in range(128):
  v=.72 if (i%16<3 or j%16<3) else 1.10
  if (i//8+j//8)%2==0:v*=.92
  pixels.extend((.22*v,.13*v,.059*v,1))
img.pixels=pixels;img.filepath_raw=str(ASSETS/'diner-jacket-weave.png');img.file_format='PNG';img.save();img.pack()
n=slate.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;slate.node_tree.links.new(n.outputs['Color'],slate.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

# Joined rounded rectangular tabletops, rims and upholstered benches.
def rounded_slab(name,cx,cy,z,w,d,h,r,m,group=static,n=12):
 pts=[]
 for x,y,a in [(cx+w/2-r,cy+d/2-r,0),(cx-w/2+r,cy+d/2-r,90),(cx-w/2+r,cy-d/2+r,180),(cx+w/2-r,cy-d/2+r,270)]:
  for i in range(n+1):
   t=math.radians(a+90*i/n);pts.append((x+r*math.cos(t),y+r*math.sin(t)))
 N=len(pts);vs=[(x,y,z+dz) for dz in [-h/2,h/2] for x,y in pts];fs=[]
 fs.append(tuple(range(N-1,-1,-1)));fs.append(tuple(N+i for i in range(N)))
 for i in range(N):j=(i+1)%N;fs.append((i,j,N+j,N+i))
 return mesh(name,vs,fs,m,group)
def ring(name,center,r,minor,m,axis='Z',group=static,N=48,M=8):
 vs=[];fs=[]
 for j in range(N):
  t=math.tau*j/N
  for k in range(M):
   a=math.tau*k/M;p=((r+minor*math.cos(a))*math.cos(t),(r+minor*math.cos(a))*math.sin(t),minor*math.sin(a))
   if axis=='X':p=(p[2],p[0],p[1])
   elif axis=='Y':p=(p[0],p[2],p[1])
   vs.append(tuple(center[i]+p[i] for i in range(3)))
 for j in range(N):
  for k in range(M):a=j*M+k;b=j*M+(k+1)%M;c=((j+1)%N)*M+(k+1)%M;d=((j+1)%N)*M+k;fs.append((a,b,c,d))
 o=mesh(name,vs,fs,m,group)
 for p in o.data.polygons:p.use_smooth=True
 return o
def lathe(name,center,profile,m,group=static,N=48):
 vs=[];fs=[]
 for r,z in profile:
  for i in range(N):t=math.tau*i/N;vs.append((center[0]+r*math.cos(t),center[1]+r*math.sin(t),center[2]+z))
 for j in range(len(profile)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 o=mesh(name,vs,fs,m,group)
 for p in o.data.polygons:p.use_smooth=True
 return o

cube('Diner raised studio foundation',(0,-.1,-.16),(8.5,6,.30),wood,.045)
for j in range(12):
 for i in range(17):
  cube('Diner beveled terrazzo tile',(-4+i*.5,-2.78+j*.5,.015),(.487,.487,.035),tileB if (i+j)%4==0 else tileA,.007)
# Sage wall and short return wings, open camera side, real moulding bands.
cube('Diner rear lime plaster wall',(0,2.62,2.03),(8.4,.16,4.05),sage,.025)
for s in [-1,1]:cube('Diner return side wall',(s*4.22,1.2,1.95),(.15,2.98,3.9),sage,.018)
cube('Diner rear wainscot',(0,2.50,.43),(8.3,.04,.84),dados,.004)
for x in [-3.6,-2.7,-1.8,-.9,0,.9,1.8,2.7,3.6]:
 cube('Diner dado panel',(x,2.465,.43),(.79,.045,.67),dados,.012)
 for dx in [-.39,.39]:cube('Diner dado panel edge',(x+dx,2.425,.43),(.025,.015,.69),wood,.004)
for z in [.045,.87,3.92]:cube('Diner continuous architectural moulding',(0,2.43,z),(8.4,.17,.095),wood,.014)
for s in [-1,1]:
 cube('Diner side wainscot',(s*4.13,1.14,.43),(.025,2.9,.86),dados,.004)
 cube('Diner cut wall moulding',(s*4.10,1.18,.88),(.10,2.96,.06),wood,.008)
# Booths arranged opposite one another. Seat heights agree with retained performers.
for s in [-1,1]:
 x=s*1.95
 rounded_slab('Booth plinth',x,.20,.39,1.35,2.3,.55,.16,wood)
 rounded_slab('Booth padded seat',x,.20,.775,1.45,2.30,.24,.19,vinyl)
 for off in [-.95,-.45,.05,.55,1.05]:
  cube('Booth soft padded back',(s*2.57,off,1.18),(.21,.49,1.35),vinyl,.045)
  ellipsoid('Booth tuft button',(s*2.455,off,1.24),(.012,.029,.029),chrome_dark,static,12,8)
 for yy in [-.97,1.37]:
  tube('Booth rolled arm rest',[(s*2.50,yy,1.36),(s*2.0,yy,1.21),(s*1.35,yy,1.18)],[.10,.085,.065],vinyl,static,20)
 beam('Booth chrome back piping',(s*2.44,-.91,1.81),(s*2.44,1.31,1.81),.018,chrome)
# Chrome double pedestal, genuine rounded red/chrome tabletop.
for y in [-.45,.55]:
 lathe('Table bell foot',(0,y,.02),[(.0,0),(.31,0),(.35,.05),(.24,.11),(.08,.17),(.045,.20)],chrome)
 beam('Table chrome pedestal',(0,y,.16),(0,y,.98),.047,chrome,static,24)
 beam('Table support cross bar',(-.74,y,.96),(.74,y,.96),.025,chrome_dark)
rounded_slab('Table chrome rolled edge',0,.12,1.015,2.20,1.70,.095,.22,chrome)
rounded_slab('Red lacquer laminate table top',0,.12,1.067,2.15,1.65,.026,.20,red)
rounded_slab('Table lower dark inset',0,.12,.958,2.14,1.64,.032,.19,chrome_dark)
# Retro wall jukebox, detailed front, folded buttons and ribbed speaker grille.
JY=2.40
cube('Jukebox walnut wall case',(0,JY,1.91),(.84,.36,1.16),wood,.052)
cube('Jukebox chrome rolled surround',(0,JY-.205,1.91),(.89,.055,1.23),chrome,.055)
cube('Jukebox black recessed face',(0,JY-.245,1.91),(.77,.022,1.10),black,.032)
for row in range(7):
 z=2.29-row*.095
 for col in [-1,1]:
  x=col*.195
  cube('Jukebox ivory song selection label',(x,JY-.263,z),(.305,.019,.060),cream,.006)
  for k in range(3):beam('Jukebox engraved label line',(x-.12,JY-.275,z+.015-k*.012),(x+.09-k*.019,JY-.275,z+.015-k*.012),.0016,chrome_dark,static,4)
  cube('Jukebox brushed button',(x+col*.150,JY-.298,z),(.029,.048,.046),chrome,.006)
# Lower selector numbers represented as raised geometric indicators, coin slot and knob.
for row in range(2):
 for i in range(10):
  cube('Jukebox numbered selector key',(-.318+i*.070,JY-.280,1.62-row*.063),(.045,.042,.036),chrome,.005)
  cube('Jukebox selector black inlay',(-.318+i*.070,JY-.304,1.62-row*.063),(.018,.002,.007),black,.001)
cube('Jukebox coin slot plate',(.258,JY-.278,1.44),(.13,.027,.072),chrome,.012)
cube('Jukebox coin slot',(.258,JY-.294,1.448),(.051,.008,.012),black,.002)
for i in range(16):cube('Jukebox lower vertical speaker rib',(-.34+i*.045,JY-.278,1.41),(.008,.018,.115),chrome,.003)
beam('Jukebox glass title rail',(-.36,JY-.279,2.37),(.36,JY-.279,2.37),.010,chrome)
# Tall frosted jukebox lamps, actual round fluted tubes and metal cap fittings.
for s in [-1,1]:
 x=s*.75
 cube('DinerPractical'+('Left' if s<0 else 'Right'),(x,2.35,1.97),(.21,.11,1.30),glow,.043,live)
 for dx in [-.067,-.033,0,.033,.067]:beam('Lamp fine fluted glass rib',(x+dx,2.282,1.36),(x+dx,2.282,2.56),.0045,frost)
 for z in [1.33,1.39,2.55,2.61]:cube('Diner lamp chromium band',(x,2.335,z),(.24,.13,.034),chrome,.007)
 for z in [1.36,2.58]:beam('Lamp mounting center strap',(x,2.254,z-.058),(x,2.254,z+.058),.009,chrome)
# Original framed archival car relief art, with layers inside a deep picture frame.
framey=2.495
cube('Framed archival sage mat',(0,framey,3.20),(2.14,.035,.81),dados,.008)
for x in [-1.17,1.17]:cube('Framed car photograph wood edge',(x,framey-.041,3.20),(.077,.095,.98),wood,.018)
for z in [2.75,3.65]:cube('Framed car photograph wood edge',(0,framey-.041,z),(2.39,.095,.067),wood,.014)
artgray=mat('Original archival relief gray',(.12,.145,.138),.94)
artcream=mat('Original archival relief gray highlight',(.44,.43,.37),.88)
cube('Original car art neutral backdrop',(0,framey-.029,3.18),(1.84,.025,.65),artgray,.002)
for j in range(6):cube('Original car art old urban skyline',(-.72+j*.28,framey-.046,3.33),(.21,.025,random.uniform(.18,.41)),wood,.002)
rounded_slab('Original artwork vintage car body',0,framey-.075,3.08,1.38,.052,.17,.035,artcream)
cube('Original artwork car cabin',(-.10,framey-.09,3.21),(.62,.028,.22),artgray,.031)
for x in [-.48,.47]:
 ring('Original artwork chrome wheel',(x,framey-.099,3.015),.089,.023,black,'Y',static,24,8)
 ring('Original artwork wheel hub',(x,framey-.112,3.015),.037,.014,chrome,'Y',static,20,6)
# Vintage outlet and modest entrance door details.
cube('Wall ivory outlet plate',(-1.38,2.49,1.91),(.17,.037,.23),cream,.019)
for z in [1.96,1.86]:
 ellipsoid('Outlet round recess',(-1.38,2.464,z),(.040,.003,.037),paper,static,16,10)
 for dx in [-.014,.014]:cube('Outlet pin slot',(-1.38+dx,2.457,z+.003),(.006,.003,.017),chrome_dark,.001)
cube('Diner service door frame',(3.14,2.44,1.53),(1.51,.22,3.04),wood,.015)
cube('Diner service door',(3.14,2.30,1.53),(1.33,.07,2.91),dados,.008)
for z in [.51,1.41,2.31]:cube('Diner door raised panel',(3.14,2.249,z),(1.06,.03,.75),sage,.013)
ellipsoid('Diner brass door knob',(2.72,2.192,1.42),(.037,.039,.037),chrome,static,18,12)
# A low service cabinet and condiment caddy at the rear.
cube('Diner sideboard cabinet',(-2.95,2.12,.59),(1.72,.62,1.16),wood,.02)
cube('Diner sideboard stone top',(-2.95,2.05,1.20),(1.83,.79,.07),marble,.027)
for x in [-3.39,-2.52]:
 cube('Diner cabinet drawer',(x,1.783,.95),(.72,.038,.28),dados,.013)
 beam('Diner cabinet handle',(x-.08,1.750,.95),(x+.08,1.750,.95),.012,chrome)
 cube('Diner cabinet lower door',(x,1.777,.44),(.72,.043,.64),dados,.014)
# tabletop cups, open bowls and individual spoons.
for x,y in [(-.61,-.01),(.63,.26)]:
 lathe('Coffee mug hollow ceramic',(x,y,1.08),[(0,0),(.077,0),(.083,.014),(.088,.157),(.083,.173),(.073,.173),(.073,.035),(0,.035)],cream)
 ring('Mug thick glazed rim',(x,y,1.249),.079,.005,cream)
 lathe('Dark coffee meniscus',(x,y,1.214),[(0,0),(.072,0),(.072,.004),(0,.004)],coffee)
 ring('Mug curved loop handle',(x+(.11 if x>0 else -.11),y,1.165),.052,.012,cream,'Y',static,32,10)
 cube('Paper folded under cup',(x,y,1.079),(.24,.23,.004),paper,.003)
for x,y in [(.28,-.16),(-.19,.52)]:
 lathe('Small open diner bowl',(x,y,1.081),[(0,0),(.075,0),(.110,.018),(.132,.062),(.140,.082),(.135,.087),(.128,.080),(.110,.040),(.072,.023),(0,.023)],cream)
 ellipsoid('Spoon concave silver bowl',(x+.012,y+.015,1.181),(.024,.040,.006),chrome,static,24,12)
 beam('Spoon slender rounded handle',(x+.014,y+.049,1.184),(x+.028,y+.196,1.222),.0045,chrome,static,10)
# Wire condiment holder: real rods, individual glass shakers and folded napkins.
cx=.10;cy=.78
for z in [1.094,1.255]:
 for y in [cy-.12,cy+.12]:beam('Condiment rack horizontal rail',(cx-.26,y,z),(cx+.26,y,z),.006,chrome)
 for x in [cx-.26,cx+.26]:beam('Condiment rack end rail',(x,cy-.12,z),(x,cy+.12,z),.006,chrome)
for x in [-.26,-.13,0,.13,.26]:
 for y in [cy-.12,cy+.12]:beam('Condiment rack upright',(cx+x,y,1.09),(cx+x,y,1.25),.004,chrome)
for x,m in [(cx-.14,ketchup),(cx+.14,mustard)]:
 lathe('Retro condiment bottle',(x,cy,1.08),[(0,0),(.047,0),(.051,.04),(.042,.17),(.020,.205),(.016,.255),(.0,.259)],m,static,32)
 lathe('Condiment bottle small cap',(x,cy,1.325),[(.014,0),(.016,0),(.016,.028),(.011,.039),(.0,.042)],cream,static,24)
for x in [-.25,.27]:
 lathe('Glass salt shaker',(x,.67,1.08),[(0,0),(.035,0),(.040,.020),(.031,.13),(.025,.145),(0,.145)],glass,static,28)
 lathe('Salt shaker perforated chrome cap',(x,.67,1.221),[(.028,0),(.030,.004),(.028,.025),(.023,.031),(0,.031)],chrome,static,24)
 for j in range(6):
  t=math.tau*j/6;ellipsoid('Salt shaker lid tiny hole',(x+.014*math.cos(t),.67+.014*math.sin(t),1.254),(.002,.002,.001),black,static,8,4)
# Closed period flip phone, keys and softly crumpled shopping bag.
rounded_slab('Closed retro silver telephone',.62,-.55,1.10,.21,.14,.037,.022,chrome)
rounded_slab('Telephone inset cover',.62,-.55,1.122,.174,.105,.011,.018,chrome_dark)
for x in [-.25,-.12]:
 ring('Small brass key ring',(x,-.46,1.083),.025,.0035,chrome,'Z',static,24,6)
 beam('House key shaft',(x,-.484,1.083),(x+.06,-.58,1.083),.004,chrome)
 cube('House key tooth',(x+.06,-.565,1.084),(.022,.030,.006),chrome,.001)
cube('Folded wallet',(-.56,-.57,1.090),(.18,.13,.018),wood,.014)
# Performer geometry is deliberately omitted; the two place settings tell the scene.
# Physical plant beside cabinet: stems and leaves with bent profiles.
plantmat=mat('Potted diner plant leaf',(.035,.14,.040),.68)
clay=mat('Diner plant ochre pot',(.22,.14,.056),.59)
lathe('Diner plant pot',(-3.52,2.02,1.245),[(0,0),(.105,0),(.105,.04),(.14,.28),(.155,.30),(.133,.30),(.125,.26),(0,.26)],clay)
for j in range(14):
 a=math.tau*j/14;r=random.uniform(.08,.28);z=random.uniform(1.67,1.96);p=(-3.52+r*math.cos(a),2.02+r*math.sin(a),z)
 beam('Diner plant slender stem',(-3.52,2.02,1.47),p,.006,plantmat,static,8)
 ellipsoid('Diner plant broad leaf',p,(.080,.033,.14),plantmat,static,16,10)
# Anchors identify real bodies, props and angles; glTF converts Z-up to Y-up.
anchors={'master':(0,.32,1.35),'two-shot':(0,.34,1.42),'man':(-1.54,.20,1.57),'woman':(1.54,.20,1.57),'detail':(.03,.02,1.15),'jukebox':(0,2.10,1.91),'phone':(.62,-.55,1.11)}
for k,p in anchors.items():o=empty('Anchor_'+k,p);o['category']=k
# Main soft key and warm actual practicals, plus cool camera-side bounce.
def area(name,pos,target,power,size,c):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=c;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Diner large warm camera key',(-2.2,-2.4,3.35),(0,.22,1.17),650,3.2,(1,.79,.50))
area('Diner cool return fill',(3.3,-1.2,3.0),(0,.3,1.1),190,3,(.60,.74,.70))
area('Diner table specular ceiling key',(0,.5,3.8),(0,.2,1),240,2.0,(1,.83,.65))
practical=[(-.75,2.22,1.97),(.75,2.22,1.97)]
for i,p in enumerate(practical):
 d=bpy.data.lights.new('DinerPracticalLight%02d'%i,'POINT');d.energy=55;d.shadow_soft_size=.18;d.color=(1,.67,.28);o=bpy.data.objects.new(d.name,d);bpy.context.collection.objects.link(o);o.location=p
world=bpy.data.worlds.new('Diner soft dark ambient');world.use_nodes=True;bpy.context.scene.world=world;world.node_tree.nodes['Background'].inputs[0].default_value=(.065,.070,.045,1);world.node_tree.nodes['Background'].inputs[1].default_value=.25
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=3
scene.render.threads_mode='FIXED';scene.render.threads=6;scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
d=bpy.data.cameras.new('Diner camera');cam=bpy.data.objects.new('Diner camera',d);bpy.context.collection.objects.link(cam);cam.location=(.0,-7.25,2.62);cam.rotation_euler=(Vector((0,.5,1.63))-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=42;scene.camera=cam
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'vintage-diner.blend'))
print('DINER_MODEL_READY',len(static),flush=True)
# Static 3D details share a 4K shadow atlas; performers, glowing practicals stay live.
combined=join(static,'Diner_Baked_Static');bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(67),island_margin=.003);bpy.ops.object.mode_set(mode='OBJECT');combined.data.uv_layers.active.name='BakedUV'
img=bpy.data.images.new('diner-warm-baked',width=4096,height=4096,alpha=False)
for m in combined.data.materials:
 if m:n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;n.select=True;m.node_tree.nodes.active=n
bpy.context.view_layer.objects.active=combined;combined.select_set(True);scene.render.bake.use_clear=True;scene.render.bake.margin=5
bpy.ops.object.bake(type='COMBINED');img.filepath_raw=str(ASSETS/'diner-warm-baked.jpg');img.file_format='JPEG';img.save()
baked=mat('Diner_Cycles_Baked_Atlas',(1,1,1),1);n=baked.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;baked.node_tree.links.new(n.outputs['Color'],baked.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);combined.data.materials.clear();combined.data.materials.append(baked)
for p in combined.data.polygons:p.material_index=0
print('DINER_BAKED',flush=True)
p=baked.node_tree.nodes.get('Principled BSDF');base_link=next(l for l in baked.node_tree.links if l.to_socket==p.inputs['Base Color']);baked.node_tree.links.remove(base_link);p.inputs['Base Color'].default_value=(0,0,0,1);baked.node_tree.links.new(n.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=1
scene.render.filepath=str(OUT/'vintage-diner-preview.png');bpy.ops.render.render(write_still=True)
for l in list(baked.node_tree.links):
 if l.to_socket==p.inputs['Emission Color']:baked.node_tree.links.remove(l)
p.inputs['Emission Strength'].default_value=0;baked.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
for o in list(bpy.data.objects):
 if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(ASSETS/'vintage-diner.glb'),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False,export_materials='EXPORT',export_apply=True)
export_file=ASSETS/'vintage-diner.glb';glb=export_file.read_bytes();json_size=struct.unpack_from('<I',glb,12)[0];gltf=json.loads(glb[20:20+json_size])
for material in gltf.get('materials',[]):
 runtime=material.setdefault('pbrMetallicRoughness',{});source=bpy.data.materials.get(material.get('name',''))
 if source and 'baseColorTexture' not in runtime and 'baseColorFactor' not in runtime:runtime['baseColorFactor']=list(source.diffuse_color)
json_chunk=json.dumps(gltf,separators=(',',':')).encode();json_chunk+=b' '*((-len(json_chunk))%4);bin_chunk=glb[20+json_size:];export_file.write_bytes(struct.pack('<III',0x46546c67,2,20+len(json_chunk)+len(bin_chunk))+struct.pack('<II',len(json_chunk),0x4e4f534a)+json_chunk+bin_chunk)
conv=lambda p:[p[0],p[2],-p[1]]
info={'blender':bpy.app.version_string,'source_reference':'IMG_1820.JPG','static_parts':len(static),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'glb_bytes':export_file.stat().st_size,'atlas':'diner-warm-baked.jpg','atlas_size':4096,'nodes':{'static':'Diner_Baked_Static','actors':[],'practicals':['DinerPracticalLeft','DinerPracticalRight']},'anchors_gltf_y_up':{k:conv(p) for k,p in anchors.items()},'frames_gltf_y_up':{'master':{'position':[0,2.40,8.8],'target':[0,1.48,-.75],'lens':35},'two-shot':{'position':[0,1.75,5.5],'target':[0,1.40,-.35],'lens':50},'man':{'position':[1.35,1.77,3.15],'target':[-1.54,1.56,-.20],'lens':85},'woman':{'position':[-1.35,1.77,3.15],'target':[1.54,1.56,-.20],'lens':85},'detail':{'position':[.2,2.04,2.25],'target':[0,1.12,-.02],'lens':85},'jukebox':{'position':[.10,2.0,1.45],'target':[0,1.95,-2.25],'lens':50}},'practical_lights_gltf':[{'position':conv(p),'color':'#ffbd69','intensity':11} for p in practical],'note':'Real modeled vintage diner: sage walls, chrome jukebox with forty selector buttons, frosted fluted lamps, booth upholstery, red laminate table, mugs, coffee, spoons, condiment caddy, closed telephone and keys. No actor or proxy humanoid geometry. Editable .blend preserves objects and procedural materials.'}
(ASSETS/'vintage-diner-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));shutil.copy2(export_file,OUT/'vintage-diner.glb');shutil.copy2(__file__,OUT/'build_vintage_diner.py');print('DINER_EXPORT_READY',json.dumps(info),flush=True)
