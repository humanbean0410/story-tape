"""Detailed, performer-free Blender masters for the dusk window and vintage diner.
Opens the original editable sets, removes actors before rebaking and preserves runtime anchors.
Blender --background --python refine_dusk_diner.py -- SITE OUTPUTS [interior|diner|both]
"""
import bpy,bmesh,math,random,json,sys,struct,shutil
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
SITE=Path(args[0]).resolve();OUT=Path(args[1]).resolve();ASSETS=SITE/'dist/assets'
MODE=args[2] if len(args)>2 else 'both'
random.seed(1812)
added=[]

def material(name,c,rough=.6,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if p is None:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m

def reg(o,m):
 o.data.materials.append(m);added.append(o);return o

def mesh(name,vs,fs,m):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);reg(o,m);return o

def cube(name,pos,size,m,bevel=.01):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:
  v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=3,affect='EDGES',clamp_overlap=True)
 d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;d.update();reg(o,m);return o

def tube(name,points,r,m,N=8):
 vs=[];fs=[]
 for j,p in enumerate(points):
  p=Vector(p);v=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)])).normalized();u=v.cross(Vector((0,0,1)))
  if u.length<.001:u=v.cross(Vector((0,1,0)))
  u.normalize();w=v.cross(u)
  for i in range(N):a=math.tau*i/N;vs.append(tuple(p+r*(math.cos(a)*u+math.sin(a)*w)))
 for j in range(len(points)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 fs.extend([tuple(range(N-1,-1,-1)),tuple((len(points)-1)*N+i for i in range(N))]);o=mesh(name,vs,fs,m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def ring(name,pos,r,minor,m,axis='Z',N=48,M=8):
 vs=[];fs=[]
 for j in range(N):
  a=math.tau*j/N
  for k in range(M):
   b=math.tau*k/M;p=((r+minor*math.cos(b))*math.cos(a),(r+minor*math.cos(b))*math.sin(a),minor*math.sin(b))
   if axis=='Y':p=(p[0],p[2],p[1])
   elif axis=='X':p=(p[2],p[0],p[1])
   vs.append(tuple(pos[i]+p[i] for i in range(3)))
 for j in range(N):
  for k in range(M):a=j*M+k;b=j*M+(k+1)%M;c=((j+1)%N)*M+(k+1)%M;d=((j+1)%N)*M+k;fs.append((a,b,c,d))
 o=mesh(name,vs,fs,m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def lathe(name,pos,profile,m,N=56):
 vs=[];fs=[]
 for r,z in profile:
  for i in range(N):a=math.tau*i/N;vs.append((pos[0]+r*math.cos(a),pos[1]+r*math.sin(a),pos[2]+z))
 for j in range(len(profile)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 o=mesh(name,vs,fs,m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def join(objs,name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;return o

def setbase(name,c,rough=None):
 m=bpy.data.materials.get(name)
 if not m:return
 m.diffuse_color=(*c,1);p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 for l in list(m.node_tree.links):
  if l.to_socket==p.inputs['Base Color']:m.node_tree.links.remove(l)
 p.inputs['Base Color'].default_value=(*c,1)
 if rough is not None:p.inputs['Roughness'].default_value=rough

def surface_grain(m,scale=(4,70,5),strength=.08):
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None);n=m.node_tree.nodes;l=m.node_tree.links
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3;tex.inputs['Detail'].default_value=2
 mapping=n.new('ShaderNodeMapping');mapping.inputs['Scale'].default_value=scale
 coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],mapping.inputs['Vector']);l.new(mapping.outputs['Vector'],tex.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');c=m.diffuse_color[:3]
 ramp.color_ramp.elements[0].color=(*[v*.84 for v in c],1);ramp.color_ramp.elements[1].color=(*[min(1,v*1.08) for v in c],1)
 l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=.0014;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])

def screw(name,pos,r,m,axis='Y'):
 ring(name+' bezel',pos,r,.0018,m,axis,N=16,M=6)
 if axis=='Y':tube(name+' slot',[(pos[0]-r*.45,pos[1]-.002,pos[2]),(pos[0]+r*.45,pos[1]-.002,pos[2])],.0011,dark,N=6)
 else:tube(name+' slot',[(pos[0]-r*.45,pos[1],pos[2]+.002),(pos[0]+r*.45,pos[1],pos[2]+.002)],.0011,dark,N=6)

def cup(name,x,y,z,glaze,tea,accent):
 lathe(name+' footed saucer',(x,y,z),[(0,0),(.065,0),(.070,.006),(.137,.012),(.155,.022),(.158,.027),(.154,.032),(.120,.025),(.064,.014),(0,.014)],glaze)
 lathe(name+' fine porcelain hollow cup',(x,y,z+.019),[(0,0),(.043,0),(.056,.012),(.070,.110),(.076,.137),(.073,.143),(.067,.137),(.060,.035),(.030,.021),(0,.021)],glaze)
 ring(name+' gilded lip',(x,y,z+.160),.071,.0019,accent)
 ring(name+' thin handle',(x+.098,y,z+.105),.042,.008,glaze,'Y',N=40,M=8)
 lathe(name+' dark amber tea',(x,y,z+.138),[(0,0),(.068,0),(.068,.001),(0,.001)],tea)
 for j in range(8):
  a=math.tau*j/8;xx=x+.146*math.cos(a);yy=y+.146*math.sin(a)
  cube(name+' tiny saucer blue mark',(xx,yy,z+.03),(.009,.004,.0013),blue,.0005).rotation_euler.z=a

def leaf(name,a,b,w,m):
 a=Vector(a);b=Vector(b);v=b-a;side=v.cross(Vector((0,0,1))).normalized();vs=[];fs=[]
 for j in range(13):
  t=j/12;cen=a+v*t+Vector((0,0,.05*math.sin(math.pi*t)));half=w*math.sin(math.pi*t)**.72
  for k in [-1,0,1]:vs.append(tuple(cen+side*half*k+Vector((0,0,.013*(1-abs(k))*math.sin(math.pi*t)))))
 for j in range(12):
  for k in range(2):p=j*3+k;fs.append((p,p+1,p+4,p+3))
 o=mesh(name,vs,fs,m)
 for p in o.data.polygons:p.use_smooth=True
 tube(name+' fine vein',[tuple(a),tuple(a+v*.5+Vector((0,0,.065))),tuple(b)],.0015,leafvein,N=6)
 return o

def book(name,cx,cy,z,w=.36,d=.26,openbook=True):
 cover=material(name+' faded cloth cover',(.075,.135,.14),.83);page=material(name+' ivory paper',(.67,.58,.39),.96);ink=material(name+' muted letterpress ink',(.18,.14,.085),.92)
 cube(name+' cloth spine',(cx,cy,z+.011),(.023,d+.018,.023),cover,.005)
 for s in [-1,1]:
  cube(name+' hardcover',(cx+s*w*.25,cy,z),(w*.48,d+.014,.01),cover,.004)
  for j in range(18):
   o=cube(name+' individual page',(cx+s*w*.245,cy,z+.012+j*.0008),(w*.465,d-.005,.0007),page,.0002);o.rotation_euler.y=s*.04
  # Open pages arch near the gutter and flatten away.
  vs=[];fs=[]
  for j in range(17):
   x=w*.48*j/16;zz=.019+.012*math.sin(math.pi*j/16)+.012*(1-j/16)**2
   vs.extend([(cx+s*x,cy-d*.48,z+zz),(cx+s*x,cy+d*.48,z+zz)])
  for j in range(16):fs.append((j*2,j*2+1,j*2+3,j*2+2))
  mesh(name+' lifted open page',vs,fs,page)
  for j in range(11):
   yy=cy-d*.35+j*d*.064;xx=cx+s*w*.25
   tube(name+' fine printed line',[(xx-s*w*.16,yy,z+.028),(xx+s*w*.16,yy,z+.024)],.0007,ink,N=4)
 ribbon=material(name+' burgundy bookmark',(.19,.027,.021),.8)
 cube(name+' satin ribbon bookmark',(cx+.011,cy-d*.25,z+.038),(.008,d*.92,.0015),ribbon,.0005)

def refine_interior():
 global dark,blue,leafvein
 brass=material('Dusk brushed antique brass',(.32,.18,.051),.35,.58);dark=material('Dusk dark hardware recess',(.025,.019,.011),.58);blue=material('Dusk handpainted porcelain blue',(.04,.13,.20),.38)
 porcelain=material('Dusk glazed ivory porcelain',(.68,.62,.47),.2);tea=material('Dusk amber tea surface',(.12,.045,.008),.22)
 cotton=material('Dusk fine linen blanket',(.29,.32,.24),.88);thread=material('Dusk linen fine seam',(.51,.48,.32),.88);leafvein=material('Dusk fine leaf veins',(.13,.18,.039),.76)
 surface_grain(cotton,(120,4,110),.10)
 for name,c in [('Rubbed dark red mahogany',(.13,.029,.014)),('Mahogany polished edges',(.19,.052,.025))]:
  setbase(name,c,.29);surface_grain(bpy.data.materials.get(name),(1,35,5),.10)
 setbase('Faded gilded wallpaper motif',(.33,.22,.068),.86)
 setbase('Linen lampshade',(.64,.47,.24),.92)
 setbase('Ivory floral woven upholstery',(.48,.40,.28),.96)
 # Two cups waiting on the broad sill; no human stand-ins.
 cup('Left window tea',-.63,1.995,1.042,porcelain,tea,brass)
 cup('Right window tea',.68,1.995,1.042,porcelain,tea,brass)
 book('Window bench poetry',-.12,1.27,.959,.43,.28)
 # Soft throw laid across the right half of the seat and over its front, modeled as cloth.
 vs=[];fs=[];nx=28;ny=28
 for j in range(ny+1):
  t=j/ny;yy=1.76-1.05*t
  for i in range(nx+1):
   u=i/nx;xx=.85+1.20*u+.018*math.sin(t*7+u*8)
   zz=.963+.025*math.sin(u*math.tau*2+t*2)+.007*math.sin(u*60)
   if yy<.96:zz-=min(.45,(.96-yy)*2.1)
   vs.append((xx,yy,zz))
 for j in range(ny):
  for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
 cloth=mesh('Dusk naturally draped linen throw',vs,fs,cotton)
 solid=cloth.modifiers.new('Cloth fine thickness','SOLIDIFY');solid.thickness=.003
 for p in cloth.data.polygons:p.use_smooth=True
 for i in range(nx+1):
  u=i/nx;xx=.85+1.20*u+.018*math.sin(7+u*8);zz=.963+.025*math.sin(u*math.tau*2+2)+.007*math.sin(u*60)-.45
  tube('Dusk throw short tasseled fringe',[(xx,.71,zz),(xx+.003*math.sin(i),.69,zz-.065)],.0018,thread,N=6)
 # Close-camera stitching along the seat's front and pillow perimeters.
 for i in range(160):
  x=-3.46+i*.043;tube('Dusk individual upholstery stitch',[(x,.930,.848),(x+.016,.930,.847)],.0014,thread,N=6)
 for cx,cy,cz,w,h,tilt in [(-2.67,1.73,1.15,.88,.80,1.03),(2.28,1.73,1.13,.85,.82,1.12)]:
  pts=[]
  for side in range(4):
   for j in range(17):
    t=j/16
    if side==0:x=-w/2+w*t;y=-h/2
    elif side==1:x=w/2;y=-h/2+h*t
    elif side==2:x=w/2-w*t;y=h/2
    else:x=-w/2;y=h/2-h*t
    zz=.01;pts.append((cx+x,cy+y*math.cos(tilt)-zz*math.sin(tilt),cz+y*math.sin(tilt)+zz*math.cos(tilt)))
  tube('Dusk velvet pillow tailored piping',pts,.006,thread,N=8)
 # Window and shutter joinery: real hinge barrels, leaf plates, slots and stay handles.
 for s in [-1,1]:
  for z in [1.32,2.30,3.24]:
   x=s*2.54;cube('Dusk shutter hinge leaf',(x,1.985,z),(.11,.019,.073),brass,.004)
   tube('Dusk shutter hinge pin',[(x+s*.045,1.968,z-.05),(x+s*.045,1.968,z+.05)],.012,brass,N=12)
   for dx in [-.03,.02]:screw('Dusk hinge slotted screw',(x+dx,1.972,z),.008,brass)
  x=s*.08;cube('Dusk window latch escutcheon',(x,2.03,2.29),(.05,.032,.145),brass,.007)
  tube('Dusk window curved latch',[(x,1.998,2.31),(x+s*.045,1.96,2.32),(x+s*.09,1.96,2.29)],.013,brass,N=12)
 for x in [-2.63,2.63]:
  for z in [1.00,3.65]:screw('Dusk frame countersunk screw',(x,2.087,z),.008,brass)
 # Socket, pull-chain and pleat stitches give the lamp a plausible close view.
 for cx in [-2.84,3.53]:
  for z in [3.31,3.33,3.35,3.37]:ring('Dusk bulb socket thread',(cx,2.08,z),.043,.002,brass,N=28,M=6)
  screw('Dusk sconce backplate fastening',(cx-.16,2.27,3.30),.008,brass)
 for z in [2.52,2.59,2.65]:ring('Dusk floor lamp turned collar',(3.23,.24,z),.071,.007,brass,N=32,M=8)
 for j in range(14):ring('Dusk lamp pull-chain bead',(3.31,.24,2.60-j*.016),.004,.002,brass,axis='Y',N=10,M=6)
 # Lighter, thin garden leaf silhouettes replace the murky proxy garden tone.
 garden=bpy.data.objects.get('InteriorGarden')
 if garden:
  for m in garden.data.materials:
   if m:m.diffuse_color=(.07,.20,.054,1);p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None);p.inputs['Base Color'].default_value=(.07,.20,.054,1);p.inputs['Roughness'].default_value=.72
 # Glass barely tinted and genuinely transparent rather than a foggy green plane.
 glass=bpy.data.materials.get('Window glass low reflection')
 if glass:
  p=next((n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None);p.inputs['Base Color'].default_value=(.42,.48,.34,1);p.inputs['Alpha'].default_value=.065;p.inputs['Roughness'].default_value=.08
 # Warm, low dusk light comes from the actual window toward the empty bench.
 light=bpy.data.objects.get('Garden window fill')
 if light:light.data.energy=460;light.data.color=(1,.59,.29);light.location=(-1.1,2.86,3.4);light.rotation_euler=(Vector((.6,.7,.7))-light.location).to_track_quat('-Z','Y').to_euler()
 key=bpy.data.objects.get('Warm cinematic key')
 if key:key.data.energy=280;key.data.color=(1,.72,.43)
 fill=bpy.data.objects.get('Subtle soft camera fill')
 if fill:fill.data.energy=60;fill.data.color=(.64,.71,.66)
 return ['Two fine porcelain teas on the sill','Open poetry book with individual pages and ribbon','Draped linen throw and tassels','160 cushion stitches and tailored pillow piping','Slotted window hardware and shutter hinge pins','Turned lamp hardware and pull chain','Fresh performer-free dusk atlas']

def refine_diner():
 global dark,blue,leafvein
 chrome=material('Diner detail satin chrome',(.46,.50,.47),.23,.72);dark=material('Diner detail graphite recess',(.018,.022,.018),.46);blue=material('Diner painted porcelain stripe',(.015,.11,.14),.35)
 cream=material('Diner detail warm ceramic',(.70,.66,.52),.23);paper=material('Diner embossed linen napkin',(.63,.56,.40),.98);thread=material('Diner warm vinyl stitching',(.24,.29,.15),.69);leafvein=material('Diner leaf fine vein',(.17,.27,.065),.73)
 surface_grain(paper,(120,90,4),.14)
 setbase('Diner sage lime plaster',(.21,.32,.19),.85)
 setbase('Polished oxblood red laminate',(.39,.010,.006),.17)
 # Fine double chrome bead follows the actual rounded tabletop rather than a square outline.
 pts=[];w=2.20;d=1.70;r=.22
 for cx,cy,a in [(w/2-r,.12+d/2-r,0),(-w/2+r,.12+d/2-r,90),(-w/2+r,.12-d/2+r,180),(w/2-r,.12-d/2+r,270)]:
  for i in range(17):t=math.radians(a+90*i/16);pts.append((cx+r*math.cos(t),cy+r*math.sin(t),1.041))
 pts.append(pts[0]);tube('Diner tabletop upper chrome rolled bead',pts,.006,chrome,N=10)
 tube('Diner tabletop lower chrome rolled bead',[(x,y,z-.044) for x,y,z in pts],.005,chrome,N=10)
 # Authentic bench upholstery: continuous edge welting plus individual saddle stitches.
 for s in [-1,1]:
  x=s*1.95;w=1.45;d=2.30;r=.19;pts=[]
  for cx,cy,a in [(x+w/2-r,.20+d/2-r,0),(x-w/2+r,.20+d/2-r,90),(x-w/2+r,.20-d/2+r,180),(x+w/2-r,.20-d/2+r,270)]:
   for i in range(12):t=math.radians(a+90*i/11);pts.append((cx+r*math.cos(t),cy+r*math.sin(t),.793))
  pts.append(pts[0]);tube('Diner tailored seat welt',pts,.008,thread,N=8)
  for j in range(55):
   yy=-.90+j*.041;tube('Diner individual saddle seat stitch',[(s*1.245,yy,.815),(s*1.245,yy+.012,.815)],.0015,thread,N=6)
  for yy in [-.95,-.45,.05,.55,1.05]:
   for j in range(25):z=.58+j*.043;tube('Diner back panel double stitch',[(s*2.459,yy-.226,z),(s*2.459,yy-.226,z+.014)],.0014,thread,N=6)
 # Empty place settings convey two people's presence without mannequin replacements.
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.name.startswith(('Coffee mug hollow ceramic','Mug thick glazed rim','Dark coffee meniscus','Mug curved loop handle')):o.location.z+=.018
 for x,y,sign in [(-.61,-.01,-1),(.63,.26,1)]:
  lathe('Diner glazed coffee saucer',(x,y,1.083),[(0,0),(.07,0),(.13,.008),(.15,.018),(.148,.024),(.105,.018),(.075,.009),(0,.009)],cream)
  ring('Diner saucer handpainted rim',(x,y,1.105),.143,.0015,blue)
  tube('Diner sugar spoon shaped handle',[(x+.13,y-.10,1.112),(x+.19,y-.16,1.119),(x+.24,y-.19,1.117)],.004,chrome,N=10)
  # A flat rest spoon with an actual concave bowl (not an ellipsoid filled with silver).
  vs=[];fs=[]
  for j in range(8):
   a=math.tau*j/8;vs.append((x+.26+.020*math.cos(a),y-.20+.033*math.sin(a),1.113))
  vs.append((x+.26,y-.20,1.108))
  for j in range(8):fs.append((8,j,(j+1)%8))
  mesh('Diner spoon pressed concave silver bowl',vs,fs,chrome)
  cube('Diner folded linen place napkin',(x+sign*.17,y-.22,1.089),(.16,.24,.009),paper,.004).rotation_euler.z=sign*.10
  for j in range(10):cube('Diner napkin fine embossed fold',(x+sign*.17-.065+j*.014,y-.22,1.094),(.001,.21,.001),thread,.0002)
 # A simple sugar packet bowl and crisp paper packets at the table rear.
 lathe('Diner sugar packet ceramic holder',(-.54,.72,1.079),[(0,0),(.07,0),(.09,.012),(.105,.067),(.098,.073),(.085,.038),(0,.025)],cream)
 for j in range(4):
  o=cube('Diner folded sugar paper packet',(-.58+j*.026,.72,1.173),(.021,.062,.095),paper,.002);o.rotation_euler.y=-.18+j*.09
  for z in [1.14,1.20]:cube('Diner sugar packet label band',(-.58+j*.026,.688,z),(.018,.001,.004),blue,.0003)
 # Jukebox: recessed trim screws, rotary volume knob, glass gasket and individual speaker slots.
 for x in [-.394,.394]:
  for z in [1.37,2.45]:screw('Diner jukebox raised countersunk screw',(x,2.153,z),.010,chrome)
 lathe('Diner jukebox original rotary chrome knob',(-.23,2.093,1.43),[(0,0),(.03,0),(.03,.018),(.027,.022),(0,.022)],chrome)
 for j in range(20):
  a=math.tau*j/20;tube('Diner jukebox knob radial knurl',[(-.23+.028*math.cos(a),2.093+.028*math.sin(a),1.436),(-.23+.028*math.cos(a),2.093+.028*math.sin(a),1.447)],.0013,dark,N=6)
 for i in range(24):
  x=-.342+i*.030
  tube('Diner jukebox grille fine mesh strand',[(x,2.108,1.33),(x,2.108,1.482)],.0015,dark,N=6)
 for i in range(6):tube('Diner jukebox grille cross weave',[(-.353,2.105,1.34+i*.026),(.353,2.105,1.34+i*.026)],.0013,chrome,N=6)
 # Sleek thicker glass ribs and proper fixtures on the glowing tubes.
 for s in [-1,1]:
  for z in [1.36,2.58]:
   for dx in [-.091,.091]:screw('Diner lamp fixture tiny screw',(s*.75+dx,2.261,z),.006,chrome)
 # Old telephone detailing and a neatly folded newspaper rather than new UI cards.
 for x in [.545,.69]:cube('Diner closed telephone inset hinge',(x,-.55,1.125),(.026,.023,.007),chrome,.003)
 cube('Diner telephone slim side key',(.733,-.57,1.109),(.004,.024,.008),dark,.001)
 newspaper=material('Diner folded newspaper stock',(.54,.51,.38),.94);ink=material('Diner newspaper soft print',(.12,.13,.095),.90)
 for j in range(5):cube('Diner folded newspaper sheet',(-1.81,.49,.915+j*.002),(.40,.31,.001),newspaper,.0003)
 for col in [-1,0,1]:
  for j in range(16):cube('Diner newspaper fine column',(-1.81+col*.115,.355+j*.018,.927),(.094,.0014,.001),ink,.0002)
 # Replace the old lollipop leaf silhouettes with curved slender foliage.
 remove=[o for o in list(bpy.data.objects) if o.name.startswith('Diner plant broad leaf')]
 for o in remove:bpy.data.objects.remove(o,do_unlink=True)
 green=material('Diner detailed pothos leaf',(.039,.16,.046),.68)
 for j in range(20):
  a=j*2.399;stem=(-3.52,2.02,1.48);tip=(-3.52+.30*math.cos(a),2.02+.22*math.sin(a),1.72+.13*math.sin(j*.9));end=(tip[0]+.11*math.cos(a),tip[1]+.08*math.sin(a),tip[2]+.08)
  tube('Diner detailed plant curling stem',[stem,tip],.005,green,N=8);leaf('Diner individually curved pothos leaf',tip,end,.054,green)
 key=bpy.data.objects.get('Diner large warm camera key')
 if key:key.data.energy=420;key.data.color=(1,.78,.52)
 fill=bpy.data.objects.get('Diner cool return fill')
 if fill:fill.data.energy=115
 return ['Chrome double rolled tabletop bead','Tailored booth welting and hundreds of saddle stitches','Coffee saucers, linen napkins, pressed spoons and sugar packets','Detailed telephone hinge and side key','Folded newspaper with original column geometry','Jukebox grille crossweave, knurled knob and screws','Curved veined pothos plant','Fresh performer-free diner atlas']

def process(kind):
 global added
 added=[];interior=kind=='interior';filename='interior-room' if interior else 'vintage-diner';staticname='Interior_Baked_Static' if interior else 'Diner_Baked_Static';atlasname='interior-warm-baked' if interior else 'diner-warm-baked';infopath=ASSETS/('interior-model-info.json' if interior else 'vintage-diner-info.json')
 bpy.ops.wm.open_mainfile(filepath=str(OUT/(filename+'.blend')))
 # Delete the entire hierarchy before shadows are baked; no hidden bodies or proxy performers.
 roots=[o for o in list(bpy.data.objects) if o.name.startswith(('ActorMan','ActorWoman')) or o.get('performer')]
 remove=set(roots)
 for o in roots:remove.update(o.children_recursive)
 for o in list(remove):
  if o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
 details=refine_interior() if interior else refine_diner()
 if interior:
  for key,pos in {'detail':(-.12,1.27,.99),'tea':(0,1.995,1.13),'throw':(1.45,1.3,.95)}.items():
   o=bpy.data.objects.get('Anchor_'+key)
   if o is None:o=bpy.data.objects.new('Anchor_'+key,None);bpy.context.collection.objects.link(o)
   o.location=pos;o['category']=key
 # The earlier sphere helper wound its faces inward. Repair every physical surface
 # before baking so gilt motifs, leaves, porcelain and metal receive real light.
 for o in list(bpy.data.objects):
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 scene=bpy.context.scene;scene.cycles.samples=28;scene.cycles.use_denoising=True;scene.cycles.max_bounces=5;scene.render.threads_mode='FIXED';scene.render.threads=6
 scene.render.resolution_x=1680;scene.render.resolution_y=960;scene.render.resolution_percentage=100
 # No source-image planes, and no actor shadows. Preserve live bulbs, translucent glass and breeze foliage.
 liveprefix=('WindowGlass','InteriorPlant','InteriorGarden','InteriorSconceBulb','InteriorFloorLampShade','InteriorFloorLampBulb') if interior else ('DinerPracticalLeft','DinerPracticalRight')
 static=[o for o in list(bpy.data.objects) if o.type=='MESH' and not o.name.startswith(liveprefix)]
 count=len(static);newcount=len(added)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(filename+'-detailed.blend')))
 print('DETAIL_MASTER_SAVED',kind,'static',count,'added',newcount,'actors_removed',len(remove),flush=True)
 combined=join(static,staticname);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.0025);bpy.ops.object.mode_set(mode='OBJECT');combined.data.uv_layers.active.name='BakedUV'
 img=bpy.data.images.new(atlasname+'-detailed',width=4096,height=4096,alpha=False)
 for m in combined.data.materials:
  if m:n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;n.select=True;m.node_tree.nodes.active=n
 bpy.context.view_layer.objects.active=combined;combined.select_set(True);scene.render.bake.use_clear=True;scene.render.bake.margin=7
 print('DETAIL_BAKE_BEGIN',kind,flush=True)
 bpy.ops.object.bake(type='COMBINED');img.filepath_raw=str(ASSETS/(atlasname+'.jpg'));img.file_format='JPEG';img.save()
 baked=material(('Interior' if interior else 'Diner')+'_Cycles_Baked_Atlas',(1,1,1),1);p=next((n for n in baked.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None);tex=baked.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;baked.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);combined.data.materials.clear();combined.data.materials.append(baked)
 for pgn in combined.data.polygons:pgn.material_index=0
 print('DETAIL_BAKE_FINISH',kind,flush=True)
 # The exported atlas is prelit. Preview it as emission to avoid doubling its baked lighting.
 p=next((n for n in baked.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None);links=baked.node_tree.links
 for l in list(links):
  if l.to_socket==p.inputs['Base Color']:links.remove(l)
 p.inputs['Base Color'].default_value=(0,0,0,1);links.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=1
 scene.render.filepath=str(OUT/(filename+'-detailed-preview.png'));scene.cycles.samples=24;bpy.ops.render.render(write_still=True)
 # Close proof view must use the same real geometry and materials, with no photo plane.
 cam=scene.camera
 if interior:cam.location=(1.3,-3.9,1.78);target=Vector((.1,1.4,1.35));cam.data.lens=42
 else:cam.location=(2.40,-4.4,2.7);target=Vector((0,.40,1.33));cam.data.lens=45
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(filename+'-detailed-close.png'));bpy.ops.render.render(write_still=True)
 for l in list(links):
  if l.to_socket==p.inputs['Emission Color']:links.remove(l)
 p.inputs['Emission Strength'].default_value=0;links.new(tex.outputs['Color'],p.inputs['Base Color'])
 for o in list(bpy.data.objects):
  if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.object.select_all(action='SELECT');path=ASSETS/(filename+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False,export_materials='EXPORT',export_apply=True)
 glb=path.read_bytes();n=struct.unpack_from('<I',glb,12)[0];gltf=json.loads(glb[20:20+n])
 for m in gltf.get('materials',[]):
  source=bpy.data.materials.get(m.get('name',''));pbr=m.setdefault('pbrMetallicRoughness',{})
  if source and 'baseColorTexture' not in pbr:
   factor=list(source.diffuse_color);shader=next((n for n in source.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if shader:factor[3]=shader.inputs['Alpha'].default_value
   pbr['baseColorFactor']=factor
 # Opaque assets should use stable shading, never alpha hashing in their main atlas.
 for m in gltf.get('materials',[]):
  if 'Window glass' in m.get('name',''):m['alphaMode']='BLEND';m['doubleSided']=True
 j=json.dumps(gltf,separators=(',',':')).encode();j+=b' '*((-len(j))%4);tail=glb[20+n:];path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail)
 info=json.loads(infopath.read_text());info['blender']=bpy.app.version_string;info['static_parts']=count;info['added_detail_parts']=newcount;info['triangles']=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH');info['glb_bytes']=path.stat().st_size;info['meshes']=len(gltf.get('meshes',[]));info['nodes']['actors']=[];info['title']='黄昏窗边' if interior else '老式餐馆';info['refinement_details']=details;info['note']='Real Blender geometry; detailed and performer-free. Fresh 4K lighting atlas baked after all actor geometry was removed. Editable detailed .blend keeps original meshes, materials, lights and anchors.'
 if interior:
  info['anchors_gltf_y_up'].update({'detail':[-.12,.99,-1.27],'tea':[0,1.13,-1.995],'throw':[1.45,.95,-1.3]})
 infopath.write_text(json.dumps(info,ensure_ascii=False,indent=2));shutil.copy2(path,OUT/(filename+'.glb'));print('DETAIL_EXPORT_READY',kind,json.dumps({k:info[k] for k in ['glb_bytes','triangles','meshes','added_detail_parts']}),flush=True)

for kind in (['interior','diner'] if MODE=='both' else [MODE]):process(kind)
