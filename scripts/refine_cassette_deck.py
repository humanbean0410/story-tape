"""Refine the editable cassette still-life without changing animation interfaces.

Blender --background --python refine_cassette_deck.py -- SITE OUTPUTS
The original cassette-deck.blend remains intact. New editable source contains
individual modeled fasteners, pressed sheet-metal, drive gears and microtextures.
"""
import bpy, bmesh, math, random, json, struct, sys
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
SITE=Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
OUT=Path(args[1]).resolve() if len(args)>1 else SITE.parent.parent/'outputs'
ASSETS=SITE/'dist/assets'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'cassette-deck.blend'))
random.seed(7527012)

def mat(name,color,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');p.name='Principled BSDF'
 output=m.node_tree.nodes.new('ShaderNodeOutputMaterial');output.name='Material Output';m.node_tree.links.new(p.outputs['BSDF'],output.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m

M={m.name:m for m in bpy.data.materials}
ivory=M['Player — warm ivory enamel'];edge=M['Player — softly worn ivory edges']
navy=M['Player — deep midnight blue'];silver=M['Player — brushed aluminium']
chrome=M['Jack — nickel plated metal'];black=M['Mechanism — soft black rubber']
smoky=M['Cassette — smoky transparent resin'];tape=M['Magnetic tape — brown oxide']
red=M['Earphones — deep red flexible vinyl'];redbright=M['Earphones — red polished shell']
paper=M['Paper — uncoated warm white'];fiber=M['Paper — tiny cream edge fibres']
brass=mat('Mechanism — aged brass bearing',(.39,.24,.083),.34,.78)
steel=mat('Mechanism — stamped steel satin',(.25,.28,.28),.43,.86)
gunmetal=mat('Mechanism — graphite anodized metal',(.025,.036,.042),.38,.65)
copper=mat('Mechanism — enamelled copper lead',(.37,.105,.028),.36,.64)
felt=mat('Cassette — pressure pad felt',(.24,.19,.15),.98)
rubber=mat('Player — moulded gasket',(.025,.032,.031),.94)
goldink=mat('Player — warm foil numerals',(.63,.52,.27),.47,.56)

def parent(name):return bpy.data.objects[name]
PLAYER=parent('Player');BAY=parent('CassetteBay');CASSETTE=parent('Cassette');COVER=parent('DoorPivot')

def reg(o,m,pa):
 if m:o.data.materials.append(m)
 o.parent=pa
 return o

def cube(name,pos,size,m,pa,bevel=.005):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
 for v in bm.verts:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
 if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=3,affect='EDGES',clamp_overlap=True)
 d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();d.update()
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;return reg(o,m,pa)

def cyl(name,pos,r,depth,m,pa,vertices=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=pos)
 o=bpy.context.object;o.name=name
 for p in o.data.polygons:p.use_smooth=True
 return reg(o,m,pa)

def ring(name,pos,r,minor,m,pa,segments=48):
 bpy.ops.mesh.primitive_torus_add(major_segments=segments,minor_segments=6,major_radius=r,minor_radius=minor,location=pos)
 o=bpy.context.object;o.name=name
 for p in o.data.polygons:p.use_smooth=True
 return reg(o,m,pa)

def tube(name,pts,r,m,pa,seg=8):
 vs=[];fs=[]
 for j,p in enumerate(pts):
  p=Vector(p);d=(Vector(pts[min(j+1,len(pts)-1)])-Vector(pts[max(0,j-1)])).normalized();u=d.cross(Vector((0,0,1)))
  if u.length<.01:u=d.cross(Vector((0,1,0)))
  u.normalize();v=d.cross(u)
  for k in range(seg):a=math.tau*k/seg;vs.append(tuple(p+r*(math.cos(a)*u+math.sin(a)*v)))
 for j in range(len(pts)-1):
  for k in range(seg):a=j*seg+k;b=j*seg+(k+1)%seg;fs.append((a,b,b+seg,a+seg))
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
 for p in d.polygons:p.use_smooth=True
 return reg(o,m,pa)

def screw(name,pos,r,pa,axis='z'):
 head=cyl(name+' head',pos,r,.009,chrome,pa,24)
 if axis=='x':head.rotation_euler.y=math.pi/2
 elif axis=='y':head.rotation_euler.x=math.pi/2
 slot=cube(name+' slot',(pos[0],pos[1],pos[2]+.0055),(r*1.25,.004,.002),gunmetal,pa,.0006)
 if axis=='x':slot.location=Vector(pos)+Vector((.0055,0,0));slot.rotation_euler.y=math.pi/2
 elif axis=='y':slot.location=Vector(pos)+Vector((0,-.0055,0));slot.rotation_euler.x=math.pi/2

def text(name,body,pos,size,m,pa):
 d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.extrude=.0004;d.bevel_depth=.00012;d.font=bpy.data.fonts.get('AndaleMono') or bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Andale Mono.ttf')
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos;o.parent=pa;d.materials.append(m)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 return bpy.context.object

# A rubber gasket follows the rim, while pressed steel pieces shape the bay.
for x in [-1.412,1.412]:cube('Bay dark neoprene side seal',(x,.051,1.052),(.018,2.25,.011),rubber,BAY,.004)
for y in [-1.053,1.161]:cube('Bay dark neoprene end seal',(0,y,1.052),(2.824,.018,.011),rubber,BAY,.004)
for x in [-1.14,1.14]:
 cube('Bay inset pressed mounting rail',(x,.12,.775),(.20,1.80,.021),steel,BAY,.019)
 for y in [-.44,.18,.77]:
  cyl('Pressed mounting hole',(x,y,.788),.025,.003,gunmetal,BAY,20)
  ring('Stamped hole rolled lip',(x,y,.789),.027,.003,steel,BAY,24)
 screw('Drive plate countersunk screw',(x,.98,.781),.026,BAY)
 cube('Drive plate mounting foot',(x,.90,.795),(.18,.28,.032),gunmetal,BAY,.016)

# Two independent gear assemblies remain below the cassette, visible in the open bay.
for x,y,r in [(-.95,.77,.15),(.89,.79,.17)]:
 cyl('Transport flywheel backing',(x,y,.79),r+.033,.033,gunmetal,BAY,48)
 cyl('Transport nylon spur gear',(x,y,.825),r,.03,M['Cassette — ivory nylon reels'],BAY,48)
 for i in range(28):
  a=i*math.tau/28;o=cube('Transport spur gear tooth',(x+(r+.01)*math.cos(a),y+(r+.01)*math.sin(a),.825),(.022,.022,.031),M['Cassette — ivory nylon reels'],BAY,.002);o.rotation_euler.z=a
 cyl('Transport bearing washer',(x,y,.844),.052,.01,brass,BAY,28)
 screw('Transport center pin',(x,y,.852),.025,BAY)
 for a in range(4):
  ang=a*math.tau/4;cyl('Gear lightening recess',(x+r*.57*math.cos(ang),y+r*.57*math.sin(ang),.842),.024,.003,gunmetal,BAY,16)

for x in [-.62,.62]:
 ring('Spindle circular base gasket',(x,-.03,.773),.188,.016,gunmetal,BAY,48)
 ring('Spindle pressed steel boss',(x,-.03,.786),.144,.009,steel,BAY,48)
 for a in range(3):
  ang=a*math.tau/3;screw('Drive bearing small screw',(x+.18*math.cos(ang),-.03+.18*math.sin(ang),.783),.014,BAY)

# The magnetic head is held by a proper spring, plus guide rollers and wiring.
cube('Magnetic head supporting bracket',(0,-.932,.779),(.53,.22,.031),steel,BAY,.012)
for x in [-.222,.222]:screw('Head adjustment screw',(x,-.932,.801),.021,BAY)
cube('Head copper spring shim',(0,-.848,.792),(.36,.052,.012),brass,BAY,.004)
for x in [-1.025,1.025]:
 ring('Pinch roller chrome lower flange',(x,-.81,.777),.1,.006,chrome,BAY,32)
 ring('Pinch roller chrome upper flange',(x,-.81,.85),.099,.006,chrome,BAY,32)
 cyl('Capstan bearing well',(x,-.61,.781),.063,.026,brass,BAY,28)
 screw('Capstan bracket screw',(x+.115,-.67,.787),.017,BAY)
for i,material in enumerate([red,copper,navy]):
 tube('Head cable loom '+str(i),[(.29+i*.013,-.94,.772),(.44+i*.019,-.81,.777),(.77+i*.018,-.87,.777),(1.29,-.90+i*.031,.78)],.007,material,BAY)
cube('Transport miniature connector',(1.28,-.864,.79),(.115,.15,.04),black,BAY,.009)
for y in [-.90,-.865,-.83]:cube('Connector brass terminal',(1.335,y,.81),(.024,.009,.008),brass,BAY,.001)
text('Bay pressed metal serial','WM-05  /  MECHANICAL MEMORY',(-1.07,.47,.778),.044,gunmetal,BAY)

# A fine inset mesh and graduated wheel make the enclosure read as real hardware.
for x in [-1.69,1.69]:
 for y in [-1.13,.0,1.15]:screw('Enclosure side rivet',(x,y,.359),.025,PLAYER,'x')
for x in [-1.2,-.72,-.24,.24,.72,1.2]:
 for j in range(5):
  o=cyl('Front grille mesh perforation',(x-.093+j*.047,-1.472,.342),.0053,.003,gunmetal,PLAYER,8);o.rotation_euler.x=math.pi/2
for y in [-.92,-.66,-.40,-.14,.12]:
 o=cube('Left case pressed ventilation mould',(-1.752,y,.38),(.014,.13,.027),rubber,PLAYER,.003)
for i in range(8):
 y=.49+i*.059
 cube('Volume engraved graduation',(-1.627,y,.744),(.045,.004,.002),goldink,PLAYER,.0005)
text('Volume dial low-high marker','0     10',(-1.63,.94,.744),.05,M['Label — off-white printing'],PLAYER)
cube('Headphone socket anodized surround',(1.762,.82,.474),(.012,.336,.274),gunmetal,PLAYER,.024)
for y in [.694,.946]:screw('Jack surround tiny screw',(1.776,y,.474),.014,PLAYER,'x')
for node in ['ButtonRewind','ButtonPlay','ButtonStop','ButtonForward']:
 pa=parent(node)
 for x in [-.246,.246]:cube('Button pressed end highlight',(x,0,.045),(.009,.184,.006),chrome,pa,.002)
 for x in [-.18,-.12,-.06,0,.06,.12,.18]:cube('Button tactile lower knurl',(x,-.088,.048),(.011,.011,.003),gunmetal,pa,.001)
cube('Player brand recessed badge',(.84,1.36,.744),(.95,.095,.01),gunmetal,PLAYER,.013)
text('Player etched badge','MEMORY / 05',(.405,1.34,.752),.051,goldink,PLAYER)

# Hinged lid contains its perimeter gasket, fasteners and latch teeth.
for x in [-1.409,1.409]:cube('Cover inner gasket side',(x,-1.285,.044),(.016,2.23,.012),rubber,COVER,.004)
for y in [-.195,-2.378]:cube('Cover inner gasket end',(0,y,.044),(2.819,.016,.012),rubber,COVER,.004)
for x in [-1.044,1.044]:
 for y in [-.035,.035]:
  o=ring('Door hinge end bearing',(x+math.copysign(.159,x),y,.003),.057,.006,gunmetal,COVER,28);o.rotation_euler.y=math.pi/2
for x in [-.155,.155]:cube('Cover latch finger',(x,-2.495,-.045),(.055,.055,.077),gunmetal,COVER,.011)

# Shell reinforcements and exposed pressure pad make the cassette credible close up.
for x in [-1.183,1.183]:
 cube('Cassette corner rounded reinforcing rib',(x,0,.125),(.017,1.38,.033),smoky,CASSETTE,.005)
 for y in [-.625,.625]:ring('Cassette screw recessed collar',(x-math.copysign(.063,x),y,.159),.062,.007,smoky,CASSETTE,24)
for x in [-.89,-.51,.51,.89]:
 cube('Cassette perimeter inner support',(x,-.717,.038),(.025,.075,.161),smoky,CASSETTE,.006)
cube('Cassette brass pressure spring',(0,-.713,.049),(.427,.034,.017),brass,CASSETTE,.005)
cube('Cassette felt pressure pad',(0,-.738,.052),(.155,.049,.041),felt,CASSETTE,.012)
for x in [-.27,.27]:cube('Cassette pressure spring feet',(x,-.704,.024),(.089,.062,.026),smoky,CASSETTE,.007)
for x in [-.97,.97]:
 ring('Cassette guide pin resin boss',(x,-.63,.124),.053,.008,smoky,CASSETTE,32)
 for y in [-.755,-.708]:cube('Cassette tape guide mouth',(x,y,.075),(.121,.028,.058),smoky,CASSETTE,.008)
for name,rad in [('ReelLeft',.46),('ReelRight',.40)]:
 pa=parent(name)
 for i in range(20):ring('Magnetic ribbon individual winding',(0,0,.0627),rad-.085-i*.0067,.00115,tape,pa,72)
 for i in range(6):
  a=i*math.tau/6
  cube('Hub moulded reinforcement',(math.cos(a)*.201,math.sin(a)*.201,.109),(.02,.02,.006),M['Cassette — ivory nylon reels'],pa,.004)
text('Cassette duration marker','C  45',(-1.135,.43,.143),.08,M['Paper label — indigo ink'],CASSETTE)
for x in [-.4,-.2,0,.2,.4]:cube('Cassette tape position tick',(x,.22,.137),(.005,.045,.003),M['Paper label — indigo ink'],CASSETTE,.0004)

# Earbud back seams, flexible cable boots, and a machined jack collar.
for name in ['EarbudLeft','EarbudRight']:
 pa=parent(name)
 o=ring('Earbud enclosure mould line',(0,0,.043),.107,.0045,red,pa,48);o.scale.y=1.28
 for i in range(5):
  cube('Earbud cord strain relief',(0,-.15-i*.016,.012),(.043,.007,.042),red,pa,.002)
 for old in list(pa.children):
  if 'grille perforation' in old.name:
   old.data.materials.clear();old.data.materials.append(gunmetal)
for x in [.061,.073,.085,.097]:
 o=ring('Jack machined collar ridge',(x,0,0),.045,.0018,chrome,parent('JackPlug'),32);o.rotation_euler.y=math.pi/2

# Real UV-backed PBR textures survive glTF export; procedural-only bumps did not.
TEX=OUT/'cassette-materials';TEX.mkdir(exist_ok=True)
def srgb(v):return 12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055
def image(name,size,pixels,colorspace='sRGB'):
 im=bpy.data.images.new(name,width=size,height=size,alpha=True);im.colorspace_settings.name=colorspace;im.pixels.foreach_set(pixels)
 im.filepath_raw=str(TEX/(name+'.png'));im.file_format='PNG';im.save();im.pack();return im

def textured(material,color,rough,kind):
 size=256;base=[];roughmap=[];normal=[]
 for y in range(size):
  for x in range(size):
   n=random.uniform(-1,1)
   if kind=='metal':wave=math.sin(y*.82)*.018+math.sin(y*4.3)*.012+n*.006;strength=.014;ry=math.cos(y*.82)*.032+math.cos(y*4.3)*.055
   elif kind=='paper':wave=n*.014+math.sin(x*.23+y*.17)*.003;strength=.005;ry=n*.006
   else:wave=n*.009;strength=.006;ry=n*.006
   c=[max(0,min(1,channel*(1+wave))) for channel in color]
   base.extend([srgb(c[0]),srgb(c[1]),srgb(c[2]),1])
   v=max(.08,min(.98,rough+wave*.9));roughmap.extend([v,v,v,1])
   nx=random.uniform(-strength,strength);ny=ry;normal.extend([.5+nx,.5+ny,1,1])
 n=material.node_tree.nodes;links=material.node_tree.links;p=next(node for node in n if node.type=='BSDF_PRINCIPLED')
 for socket in ['Base Color','Roughness','Normal']:
  for link in list(p.inputs[socket].links):links.remove(link)
 p.inputs['Base Color'].default_value=(1,1,1,1);material.diffuse_color=(*color,1)
 b=n.new('ShaderNodeTexImage');b.image=image(material.name.replace(' — ','-').replace(' ','-')+'-base',size,base);b.extension='REPEAT';links.new(b.outputs['Color'],p.inputs['Base Color'])
 r=n.new('ShaderNodeTexImage');r.image=image(material.name.replace(' — ','-').replace(' ','-')+'-rough',size,roughmap,'Non-Color');links.new(r.outputs['Color'],p.inputs['Roughness'])
 normaltex=n.new('ShaderNodeTexImage');normaltex.image=image(material.name.replace(' — ','-').replace(' ','-')+'-normal',size,normal,'Non-Color')
 normalnode=n.new('ShaderNodeNormalMap');normalnode.inputs['Strength'].default_value=.45;links.new(normaltex.outputs['Color'],normalnode.inputs['Color']);links.new(normalnode.outputs['Normal'],p.inputs['Normal'])
 p.inputs['Coat Weight'].default_value=.12 if kind=='enamel' else 0

textured(ivory,(.42,.40,.32),.39,'enamel')
textured(edge,(.64,.60,.48),.43,'enamel')
textured(navy,(.011,.025,.036),.36,'enamel')
textured(silver,(.39,.415,.425),.37,'metal')
textured(steel,(.235,.26,.27),.43,'metal')
textured(paper,(.75,.72,.64),.92,'paper')
textured(M['Paper — ivory label strip'],(.86,.83,.75),.93,'paper')
textured(M['Paper — brown envelope'],(.39,.265,.135),.92,'paper')
textured(M['Paper — stone gray backing'],(.39,.415,.40),.94,'paper')
textured(M['Table — pale warm gray linoleum'],(.23,.26,.235),.82,'enamel')
textured(redbright,(.46,.012,.017),.32,'enamel')
textured(M['Paper — translucent masking tape'],(.61,.51,.265),.96,'paper')
# Transparent blue resin is restrained, with stronger real highlights in the lid.
for material,color,alpha,rough in [(smoky,(.19,.29,.295),.27,.20),(M['Door — transparent pale glass'],(.25,.34,.32),.14,.14)]:
 material.diffuse_color=(*color,alpha);p=material.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,alpha);p.inputs['Alpha'].default_value=alpha;p.inputs['Roughness'].default_value=rough

# Project all hard-surface faces in a stable world-space cube UV at true detail scale.
for o in bpy.data.objects:
 if o.type!='MESH':continue
 mesh=o.data
 for oldlayer in list(mesh.uv_layers):mesh.uv_layers.remove(oldlayer)
 uv=mesh.uv_layers.new(name='RefinedSurfaceUV')
 mw=o.matrix_world
 for face in mesh.polygons:
  normal=(mw.to_3x3()@face.normal).normalized();axis=max(range(3),key=lambda k:abs(normal[k]))
  # 0.20 scene units per seamless tile; larger sheets show subtle paper texture.
  for loopid in face.loop_indices:
   v=mw@mesh.vertices[mesh.loops[loopid].vertex_index].co
   coords=(v.y,v.z) if axis==0 else ((v.x,v.z) if axis==1 else (v.x,v.y))
   uv.data[loopid].uv=(coords[0]*5,coords[1]*5)

scene=bpy.context.scene;scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1440;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.view_settings.exposure=-.15
# Broad angled highlights make the aged satin metal visible in a useful review render.
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.25
for o in bpy.data.objects:
 if o.type=='LIGHT':o.data.energy*=.80
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'cassette-deck-detailed.blend'))
scene.render.filepath=str(OUT/'cassette-deck-detailed-preview.png');bpy.ops.render.render(write_still=True)

# Merge siblings inside each animated root. Every control/hinge/reel remains intact.
groups={}
for o in list(bpy.data.objects):
 if o.type=='MESH':groups.setdefault(o.parent.name if o.parent else None,[]).append(o)
for pa,objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name=(pa or 'Opening')+'_static'
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type in {'MESH','EMPTY'}:o.select_set(True)
path=ASSETS/'cassette-deck.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_yup=True,export_cameras=False,export_lights=False,export_animations=False,export_image_format='AUTO')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compact_cassette_glb import compact
compact(path)
docbytes=path.read_bytes();doc=json.loads(docbytes[20:20+struct.unpack_from('<I',docbytes,12)[0]])
required=['CassetteOpening','Cassette','ReelLeft','ReelRight','DoorPivot','Player','JackPlug','Earphones','EarbudLeft','EarbudRight','ButtonPlay','ButtonRewind','ButtonForward','ButtonStop','VolumeWheel']
nodes={n.get('name') for n in doc['nodes']}
assert all(n in nodes for n in required),(set(required)-nodes)
meta=json.loads((ASSETS/'cassette-deck-info.json').read_text())
meta.update({'refinement_version':'20261012-physical-detail','editable_source':'cassette-deck-detailed.blend','static_meshes':len(doc.get('meshes',[])),'triangles':sum(len(p.vertices)-2 for o in bpy.data.objects if o.type=='MESH' for p in o.data.polygons),'materials':len(doc.get('materials',[])),'file_size_bytes':path.stat().st_size,'texture_images':len(doc.get('images',[])), 'encoding':'Built-in GLTFLoader KHR_mesh_quantization: 1/4096 scene-unit positions, signed-byte normals, signed-short repeating UVs with KHR_texture_transform.', 'details':['Pressed sheet-metal transport well with mounting rails and rolled perforations','Two 28-tooth spur gears, spindle bosses and brass capstan bearings','Magnetic-head bracket, tension shim, wire loom and plug','Neoprene lid seal, hinge bearings, latching fingers, case rivets','Graduated knurled volume wheel, etched badge and inset speaker mesh','Cassette pressure felt, brass spring, shell reinforcing ribs and tape windings','Earbud mould seams, flexible strain relief and machined jack collar','UV-mapped exported PBR paper fibre, satin brushed metal and warm enamel textures']})
(ASSETS/'cassette-deck-info.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));(OUT/'cassette-deck-detailed-info.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('CASSETTE_REFINEMENT_COMPLETE',json.dumps({'bytes':path.stat().st_size,'meshes':meta['static_meshes'],'triangles':meta['triangles'],'images':meta['texture_images'],'required_nodes_verified':required,'editable_source':str(OUT/'cassette-deck-detailed.blend')},ensure_ascii=False))
