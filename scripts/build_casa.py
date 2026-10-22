"""Reconstruct the photographed Casa storefront as real Blender geometry.
Run with Blender --background --factory-startup --python build_casa.py.
All geometry, surface variation, signs, posters and street props are authored here.
Cycles produces two combined-light atlases; browser crossfades the actual baked maps.
"""
import bpy, bmesh, math, random, json, sys
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
skip_renders='--bake-only' in args
args=[a for a in args if not a.startswith('--')]
base=Path(__file__).resolve().parents[1]
SITE=Path(args[0]).resolve() if args else (base if (base/'dist').is_dir() else base/'casa')
ROOT=SITE.parent
ASSETS=SITE/'dist/assets'
OUT=Path(args[1]).resolve() if len(args)>1 else ROOT.parent/'outputs'
ASSETS.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)
random.seed(17)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
static=[];dynamic=[];lamps=[]

def material(name,color,rough=.7,noise=0,scale=30,wood=False,metal=0,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    if noise:
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.72
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[1].position=.8
        ramp.color_ramp.elements[0].color=(*[max(0,c*(1-noise)) for c in color],1)
        ramp.color_ramp.elements[1].color=(*[min(1,c*(1+noise)) for c in color],1)
        coord=n.new('ShaderNodeTexCoord')
        if wood:
            mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(1,22,22)
            l.new(coord.outputs['Generated'],mapping.inputs[0]);l.new(mapping.outputs[0],tex.inputs['Vector'])
        else:l.new(coord.outputs['Generated'],tex.inputs['Vector'])
        l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.013
        l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return m

plaster=material('Warm ochre plaster',(.46,.33,.15),noise=.3,scale=75)
concrete=material('Weathered warm concrete',(.43,.435,.40),noise=.25,scale=110)
wood=material('Dark chocolate wood',(.052,.037,.029),noise=.36,scale=8,wood=True)
benchwood=material('Oak bench grain',(.37,.22,.105),noise=.42,scale=6,wood=True)
black=material('Charcoal paint',(.018,.023,.021),rough=.4)
cream=material('Ivory painted metal',(.69,.65,.50),rough=.36,metal=.25)
gold=material('Warm gold lettering',(.63,.37,.10),rough=.3,metal=.5)
white=material('Chalk ceramic',(.72,.72,.67),rough=.34)
asphalt=material('Asphalt',(.047,.055,.059),noise=.5,scale=140)
paving=material('Old sidewalk stone',(.32,.33,.31),noise=.35,scale=90)
yellow=material('Street yellow',(.54,.35,.05),rough=.8)
paper=material('Poster warm paper',(.65,.46,.20),noise=.06,scale=80)
red=material('Poster red ink',(.28,.045,.024))
posterink=material('Poster dark ink',(.09,.035,.014))
leafmat=material('Plant leaves',(.052,.13,.071),noise=.25)
terra=material('Terracotta',(.30,.10,.06),noise=.25)
neighbour=material('Neighbor stone',(.20,.24,.22),noise=.3)
glass=material('Reflective shop glazing',(.18,.23,.21),rough=.09,metal=.25)
rust=material('Old oxidised metal',(.19,.09,.037),rough=.85,noise=.65,scale=42)
aged=material('Weathered joinery edges',(.13,.10,.069),noise=.42,scale=10,wood=True)
cement=material('Paver pale cement',(.41,.41,.37),noise=.3,scale=50)
stain=material('Concrete rain tracks',(.24,.235,.20),noise=.8,scale=7)
brick=material('Side exposed brick',(.21,.105,.069),noise=.4,scale=20)
floral=material('Tiny red flowers',(.48,.07,.035),rough=.5)
bulb=material('Lamp warm filament',(1,.62,.22),rough=.15,emission=2)

def weather(m,color,strength=.35,stretch=(1,1,1)):
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    original=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
    coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=stretch
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.6;noise.inputs['Detail'].default_value=4
    l.new(coord.outputs['Object'],mapping.inputs[0]);l.new(mapping.outputs[0],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.25;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(strength,strength,strength,1)
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(*color,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],mix.inputs[0])
    if original:l.new(original,mix.inputs[1])
    else:mix.inputs[1].default_value=p.inputs['Base Color'].default_value
    l.new(mix.outputs[0],p.inputs['Base Color'])
weather(concrete,(.25,.23,.18),.48,(6,6,.18))
weather(plaster,(.16,.135,.063),.48,(3,3,.35))
weather(wood,(.019,.014,.011),.37,(1,16,16))
weather(benchwood,(.21,.16,.10),.46,(.12,25,25))
weather(paving,(.17,.18,.14),.50)

def register(o,m,is_static=True):
    if m:o.data.materials.append(m)
    (static if is_static else dynamic).append(o)
    return o
def cube(name,pos,size,m,bevel=.015,is_static=True):
    # Build beveled blocks directly without refreshing the entire scene for every tile.
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:
        v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
    if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=2,affect='EDGES',clamp_overlap=True)
    data=bpy.data.meshes.new(name);bm.to_mesh(data);bm.free();data.update()
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=pos
    return register(o,m,is_static)
def sphere(name,pos,r,m,scale=(1,1,1),is_static=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=r,location=pos);o=bpy.context.object;o.name=name;o.scale=scale
    for f in o.data.polygons:f.use_smooth=True
    return register(o,m,is_static)
def cylinder(name,pos,r,depth,m,vertices=12,is_static=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=pos);o=bpy.context.object;o.name=name
    for f in o.data.polygons:f.use_smooth=True
    return register(o,m,is_static)
def line(name,points,r,m,is_static=True):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=1;data.bevel_depth=r;data.bevel_resolution=1
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for p,xyz in zip(s.points,points):p.co=(*xyz,1)
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False)
    return register(o,m,is_static)
def face(name,verts,m,is_static=True):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],[list(range(len(verts)))]);data.update()
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);return register(o,m,is_static)

script_font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Apple Chancery.ttf')
plain_font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial.ttf')
def text(name,body,pos,size,m,font=None,rot=(math.pi/2,0,0),extrude=.003,is_static=True):
    curve=bpy.data.curves.new(name,'FONT');curve.body=body;curve.size=size;curve.align_x='CENTER';curve.font=font or plain_font;curve.extrude=extrude;curve.bevel_depth=.001;curve.bevel_resolution=1;curve.resolution_u=6
    o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=rot
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False);register(o,m,is_static);return o

# Building envelope. An actual corner, with a separate front and side wall.
cube('Upper building',(0,.8,6.4),(6.4,4.7,4.0),concrete,.018)
# Walls surround real door and side-window voids, so opening the door reveals the room.
cube('Left corner wall',(-3.15,-1.065,2.1),(.22,.97,4.2),plaster,.018)
cube('Door header wall',(-3.15,.045,3.59),(.22,1.25,1.22),plaster,.015)
cube('Side wall between openings',(-3.15,.96,2.1),(.22,.59,4.2),plaster,.018)
cube('Side wall rear',(-3.15,2.65,2.1),(.22,1.01,4.2),plaster,.018)
cube('Side window header',(-3.15,1.70,3.32),(.22,.89,1.76),plaster,.015)
cube('Side window sill wall',(-3.15,1.70,.53),(.22,.89,1.06),plaster,.015)
cube('Door threshold',(-3.15,.04,.17),(.40,1.20,.08),cement,.008)

cube('Right facade edge',(3.12,-1.65,2.05),(.20,.24,4.1),wood)
cube('Back shop wall',(0,3.04,2.0),(6.25,.15,4.0),plaster)
cube('Interior ceiling',(0,.8,3.72),(6.3,4.6,.16),wood)
cube('Shop floor',(0,.8,.19),(6.2,4.5,.14),paving)

# The building continues beyond the photograph, avoiding a floating diorama edge.
cube('Right adjacent envelope',(6.05,1.60,4.0),(5.72,4.85,8.0),concrete,.02)
cube('Right adjacent ground facade',(6.03,-.865,2.0),(5.70,.11,4.0),plaster,.018)
for xx in [4.5,6.75]:
    cube('Adjacent upper recess',(xx,-.877,5.95),(1.62,.04,2.03),black,.008)
    cube('Adjacent upper glass',(xx,-.910,5.95),(1.43,.022,1.85),glass,.004,False)
    for xxx in [xx-.78,xx+.78]:cube('Adjacent window frame',(xxx,-.942,5.95),(.05,.045,2.08),cream,.005)
    for zz in [4.90,7.00]:cube('Adjacent window frame',(xx,-.942,zz),(1.64,.06,.05),cream,.005)
    cube('Adjacent ground shutter',(xx,-.963,1.58),(1.68,.06,2.45),wood,.015)
    for zz in [.38+j*.12 for j in range(21)]:cube('Adjacent shutter horizontal rib',(xx,-1.003,zz),(1.62,.032,.012),aged,.002)
for xx in [3.22,5.7,8.1]:cube('Adjacent wall masonry seam',(xx,-.89,5.85),(.012,.025,4.28),neighbour,0)
# Recessed upper windows and concrete joints.
for px in [-1.4,1.35]:
    cube('Upper window recess',(px,-1.565,6.7),(2.20,.055,2.2),black,.008)
    cube('Upper window glass',(px,-1.606,6.7),(2.04,.025,2.02),glass,.005,False)
    for xx in [px-1.09,px+1.09]:cube('Upper window upright',(xx,-1.64,6.7),(.045,.045,2.23),cream,.007)
    for zz in [5.61,7.8]:cube('Upper window lintel',(px,-1.64,zz),(2.22,.06,.06),cream,.005)
for zz in [4.55,5.6,7.8]:cube('Concrete horizontal joint',(0,-1.562,zz),(6.4,.025,.013),neighbour,0)
for xx in [-2.4,-.1,2.3]:cube('Concrete vertical joint',(xx,-1.563,6.4),(.012,.025,3.8),neighbour,0)

# Sign fascia and ornamental edging; lettering is extruded mesh, not a photo plane.
cube('Sign fascia',(0,-1.79,4.02),(6.65,.25,.79),black,.025)
for zz in [3.62,4.42]:cube('Sign ivory horizontal border',(0,-1.952,zz),(6.72,.065,.07),cream,.01)
for xx in [-3.32,3.32]:cube('Sign ivory edge',(xx,-1.95,4.02),(.075,.065,.86),cream,.01)
sign=text('Embossed Casa lettering','Casa de las Bellas',(0,-1.973,3.76),.60,gold,script_font,extrude=.012)
bpy.context.view_layer.update()
sign.scale*=5.90/sign.dimensions.x
sign.location.z=3.67
face('Fascia_glass',[(-3.24,-1.935,3.68),(3.24,-1.935,3.68),(3.24,-1.935,4.35),(-3.24,-1.935,4.35)],glass,False)
cube('Side sign fascia',(-3.35,.44,4.02),(.23,4.0,.79),black,.02)
for zz in [3.62,4.42]:cube('Side sign ivory rim',(-3.49,.44,zz),(.065,4.04,.07),cream,.008)
face('SideFascia_glass',[(-3.478,-1.49,3.67),(-3.478,2.44,3.67),(-3.478,2.44,4.36),(-3.478,-1.49,4.36)],glass,False)
text('Side embossed lettering','Churros & Coffee',(-3.49,.43,3.80),.34,gold,script_font,rot=(math.pi/2,0,-math.pi/2),extrude=.008)
cube('Poster pillar',(-2.58,-1.68,1.93),(1.08,.22,3.30),wood,.02)
for xx in [-3.12,-2.06]:cube('Pillar trim',(xx,-1.82,1.92),(.055,.035,3.33),wood,.006)
cube('Pillar foot',(-2.58,-1.74,.24),(1.19,.30,.27),wood,.025)

def arched_window(name,cx,width=2.30):
    y=-1.73;radius=width/2;spring=2.55;bottom=1.30
    points=[(cx-radius,y,bottom),(cx-radius,y,spring)]+[(cx+math.cos(a)*radius,y,spring+math.sin(a)*radius) for a in [math.pi-i*math.pi/32 for i in range(33)]]+[(cx+radius,y,bottom)]
    face(name+'_glass',points,glass,False)
    line(name+'_arch',[(cx+math.cos(a)*radius,y-.035,spring+math.sin(a)*radius) for a in [math.pi-i*math.pi/48 for i in range(49)]],.062,wood)
    for px in [cx-radius,cx+radius]:cube(name+'_jamb',(px,y-.05,1.50),(.12,.15,2.66),wood,.012)
    for zz in [1.27,1.70,2.12,2.56]:cube(name+'_crossbar',(cx,y-.08,zz),(width,.14,.075),wood,.014)
    cube(name+'_below',(cx,y+.02,.73),(width,.16,1.06),wood,.018)
    for px in [cx-radius+.14,cx+radius-.14]:cube(name+'_lower_panel_trim',(px,y-.075,.73),(.035,.025,.8),wood,.003)
    for zz in [.33,1.13]:cube(name+'_lower_panel_trim',(cx,y-.075,zz),(width-.28,.025,.035),wood,.003)
    # Arch fanlight spokes, an important silhouette in the source storefront.
    for a in [math.pi/4,math.pi/2,3*math.pi/4]:line(name+'_fanlight',[(cx,y-.075,spring),(cx+math.cos(a)*radius,y-.075,spring+math.sin(a)*radius)],.038,wood)
    # Actual spandrel wall follows the curve, rather than floating rectangular strips.
    top=3.71;outer=radius+.10
    for side in [-1,1]:
        for j in range(24):
            a0=math.pi/2+j*math.pi/48 if side<0 else j*math.pi/48
            a1=a0+math.pi/48
            x0=cx+math.cos(a0)*radius;z0=spring+math.sin(a0)*radius
            x1=cx+math.cos(a1)*radius;z1=spring+math.sin(a1)*radius
            verts=[(x0,y+.022,z0),(x1,y+.022,z1),(x1,y+.022,top),(x0,y+.022,top)]
            face(name+'_curved_ochre_spandrel',verts if side<0 else list(reversed(verts)),plaster)
    for px in [cx-outer,cx+outer]:cube(name+'_ochre_outer_jamb',(px,y+.04,3.09),(.10,.17,1.14),plaster,.006)
    # Separate recessed bead strips and aged narrow panel edges.
    for zz in [1.22,2.10,2.55]:
        cube(name+'_frame_moulding',(cx,y-.16,zz),(width+.09,.036,.032),aged,.005)
    for px in [cx-radius+.05,cx+radius-.05]:
        line(name+'_jamb_wear',[(px,y-.132,.26),(px+.009,y-.132,.82),(px,y-.132,1.14)],.004,aged)
    line(name+'_fanlight_hub',[(cx+math.cos(a)*.18,y-.12,spring+math.sin(a)*.18) for a in [math.pi-j*math.pi/24 for j in range(25)]],.025,wood)

arched_window('LeftWindow',-.75)
arched_window('RightWindow',1.83)
cube('Window central mullion',(.54,-1.70,1.93),(.13,.24,3.28),wood,.015)

# Visible interior: counter, shelves, small cups and warm pendants.
cube('Interior counter',(0,.6,1.0),(4.8,.80,1.5),wood)
cube('Counter oak top',(0,.6,1.80),(4.9,.88,.09),benchwood)
for zz in [2.05,2.70]:cube('Back shelf',(0,2.80,zz),(5.3,.32,.045),benchwood,.008)
# A coffee bar can be seen through the glass: grinder, pastry tray, cups and menu paper.
cube('Coffee machine',(1.35,.55,2.06),(.62,.44,.46),black,.035)
cube('Coffee machine chrome face',(1.35,.31,2.09),(.52,.026,.30),cream,.01)
for xx in [1.20,1.43]:line('Coffee spout',[(xx,.28,2.0),(xx,.23,1.96)],.018,cream)
cube('Pastry tray',(-.85,.35,1.87),(.72,.40,.028),cream,.015)
for xx in [-1.1,-.9,-.7]:
    sphere('Fresh pastry',(xx,.32,1.93),.105,benchwood,scale=(1,.7,.4))
for xx in [-1.45,-.3,.2]:
    cylinder('Counter cup',(xx,.42,1.91),.065,.13,white)
    line('Cup handle',[(xx+.056,.42,1.9),(xx+.09,.42,1.9),(xx+.09,.42,1.96),(xx+.056,.42,1.96)],.009,white)
cube('Back cabinet',(-1,2.89,1.17),(3.20,.19,1.70),wood,.02)
for xx in [-1.8,-.95,-.1]:cube('Cabinet panel bead',(xx,2.77,1.17),(.75,.027,1.51),aged,.012)
for i in range(18):
    xx=-2.5+i*.28;zz=2.08 if i%2 else 2.73
    cylinder('Cup',(xx,2.65,zz+.09),.061,.18,white)
for px in [-.6,1.5]:
    line('Pendant cable',[(px,.3,3.6),(px,.3,2.95)],.007,black)
    sphere('Pendant shade',(px,.3,2.96),.15,cream,scale=(1,1,.48))
    sphere('Pendant bulb',(px,.3,2.88),.065,bulb,is_static=False)

# A real hinged side door, with an independent origin for runtime opening.
doorpivot=bpy.data.objects.new('DoorPivot',None);bpy.context.collection.objects.link(doorpivot);doorpivot.location=(-3.29,-.54,.19)
parts=[]
parts.append(cube('Door lower panel',(-3.29,.04,.84),(.095,1.17,1.30),wood,.015,False))
parts.append(cube('Door upper header',(-3.29,.04,2.69),(.095,1.17,.36),wood,.015,False))
for yy in [-.48,.56]:parts.append(cube('Door glazed upright',(-3.29,yy,1.99),(.095,.13,1.04),wood,.012,False))
parts.append(cube('Door glass middle rail',(-3.29,.04,2.075),(.095,1.05,.085),wood,.008,False))

for zz in [.49,1.51,2.56]:parts.append(cube('Door panel rail',(-3.356,.04,zz),(.035,1.04,.048),wood,.007,False))
for yy in [-.46,.54]:parts.append(cube('Door panel stile',(-3.357,yy,1.52),(.035,.044,2.33),wood,.006,False))
for zz in [1.89,2.26]:parts.append(cube('Door glass',(-3.357,.04,zz),(.02,.79,.29),glass,.007,False))
parts.append(line('Door brass handle',[(-3.40,.37,1.25),(-3.46,.37,1.25),(-3.46,.37,1.55),(-3.40,.37,1.55)],.014,gold,False))
for o in parts:
    matrix=o.matrix_world.copy();o.parent=doorpivot;o.matrix_world=matrix
for yy in [-.57,.67]:cube('Door frame',(-3.32,yy,1.54),(.16,.12,2.9),wood,.015)
cube('Door lintel',(-3.32,.04,2.98),(.16,1.34,.12),wood)

# Posters: separate inset boards, raised typography, and line-art churros.
poster_titles=[('CHURRO RING','TRY OUR'),('SIGNATURE','CHURROS + ICE CREAM'),('ICE CREAM','CHURROS'),('TAKE OUT','FREE CHURRORING')]
for i,(heading,subtitle) in enumerate(poster_titles):
    px=-2.81+(i%2)*.46;zz=2.20-(i//2)*.64
    cube('Poster paper',(px,-1.819,zz),(.435,.017,.595),paper,.004)
    text('Poster heading',heading,(px,-1.833,zz+.18),.057,posterink,extrude=.0005)
    text('Poster subtitle',subtitle,(px,-1.834,zz+.10),.027,red,extrude=.0003)
    text('Poster imprint','Casa Bellas',(px,-1.834,zz-.23),.043,posterink,script_font,extrude=.0003)
    if i<2:
        for r in [.086,.108,.13]:line('Poster churro ring',[(px+math.cos(a)*r,-1.840,zz-.04+math.sin(a)*r*.7) for a in [j*math.tau/40 for j in range(41)]],.005,red)
    else:
        for j in range(4):line('Poster churro drawing',[(px-.07+j*.045,-1.840,zz-.16),(px-.11+j*.045,-1.840,zz+.02)],.009,red)

# Photo's projecting churro box, side lanterns and wall infrastructure.
cube('Projecting churro sign',(-2.96,-2.06,3.33),(.45,.40,.61),black,.018)
cube('Churro sign paper',(-3.198,-2.06,3.33),(.008,.32,.49),paper,.005)
text('Churro box lettering','CHURROS',(-3.21,-2.06,3.20),.11,posterink,rot=(math.pi/2,0,-math.pi/2),extrude=.003)
for yy in [.85,2.45]:
    cube('Lantern wall mount',(-3.31,yy,2.78),(.06,.14,.30),black,.01)
    line('Lantern bracket',[(-3.35,yy,2.85),(-3.58,yy,2.95),(-3.58,yy,2.74)],.019,black)
    cube('Lantern chamber',(-3.58,yy,2.56),(.17,.19,.26),black,.012)
    for xx in [-3.677,-3.482]:
        cube('Lantern_glass',(xx,yy,2.56),(.009,.155,.20),bulb,.002,False)
    cube('Lantern cap',(-3.58,yy,2.72),(.24,.25,.07),black,.012)
    cylinder('Lantern finial',(-3.58,yy,2.80),.035,.095,black)
line('Rain downpipe',[(3.10,-1.57,7.95),(3.10,-1.59,4.57),(3.16,-1.74,4.44),(3.16,-1.84,3.52),(3.18,-1.84,.25)],.023,rust)
for zz in [1.1,2.7,4.95,6.55]:cube('Pipe bracket',(3.1,-1.62,zz),(.13,.10,.02),rust,.004)
line('Facade surface wire',[(.55,-1.573,7.85),(.53,-1.573,5.60),(.57,-1.573,4.48)],.006,black)
for zz in [5.0,6.28,7.3]:sphere('Wire fixing',(.54,-1.59,zz),.024,neighbour)
# Small genuine facade imperfections, all mesh geometry in the editable Blender source.
for cx,cz in [(-2.4,5.3),(.55,5.62),(2.32,4.61)]:
    line('Hairline concrete crack',[(cx,-1.578,cz),(cx+.032,-1.578,cz-.16),(cx+.07,-1.578,cz-.19),(cx+.06,-1.578,cz-.32),(cx+.09,-1.578,cz-.48)],.0025,stain)
for j in range(7):
    xx=-2.40+j*.79
    cube('Weathered sign rim joint',(xx,-1.992,4.41),(.011,.008,.041),rust,.001)
# Small side window with shutters and a red flower box, as visible in the reference.
for zz in [1.12,2.40]:cube('Side window sill',(-3.28,1.7,zz),(.10,.84,.04),wood,.006)
cube('Side window glass',(-3.347,1.7,1.76),(.018,.69,1.11),glass,.007,False)
for yy in [1.26,2.14]:
    shutter=cube('Timber side shutter',(-3.42,yy,1.76),(.09,.20,1.48),wood,.012)
    for zz in [1.08,1.35,1.62,1.89,2.16,2.41]:cube('Shutter slat',(-3.477,yy,zz),(.024,.185,.035),aged,.004)
cube('Window flower box',(-3.51,1.70,1.05),(.34,.80,.17),wood,.008)
for i in range(15):
    xx=-3.52+random.uniform(-.13,.13);yy=1.7+random.uniform(-.32,.32);zz=1.17+random.uniform(0,.15)
    sphere('Flower foliage',(xx,yy,zz),.05,leafmat,scale=(1,1,.45))
    if i%2:sphere('Red flowers',(xx-.02,yy,zz+.025),.022,floral)

# Wooden benches: slatted seats, end legs, end grain and braces.
def bench(cx,length=1.97):
    for yy in [-2.07,-2.22,-2.37]:cube('Bench oak seat',(cx,yy,.76),(length,.137,.074),benchwood,.012)
    for xx in [cx-length*.40,cx+length*.40]:
        cube('Bench trestle support',(xx,-2.215,.46),(.10,.36,.52),benchwood,.012)
        cube('Bench cross brace',(xx,-2.215,.63),(.14,.36,.08),benchwood,.008)
        for yy in [-2.08,-2.35]:
            screw=cylinder('Bench seat recessed screw',(xx,yy,.801),.011,.002,black,vertices=8)
            for offset in [-.022,.022]:line('Seat plank end grain',[(xx+offset,-2.03,.798),(xx+offset-.01,-2.21,.798),(xx+offset,-2.39,.798)],.0015,aged)
    for i in range(5):
        yy=-2.05-i*.073
        line('Oak seat grain',[(cx-length/2+.08,yy,.799),(cx-.12,yy+random.uniform(-.009,.009),.799),(cx+length/2-.08,yy,.799)],.0015,aged)

    cube('Bench long brace',(cx,-2.215,.43),(length*.83,.07,.07),benchwood,.006)
bench(-.76);bench(1.85,1.86)

# Checkerboard raised curb, pavement with actual tile gaps, and a quiet side street.
for i in range(13):cube('Checkerboard curb',(-3.3+i*.55,-2.40,.18),(.543,.67,.34),white if i%2 else black,.008)
for ix in range(22):
    for iy in range(25):
        px=-4.35+ix*.54;yy=-8.10+iy*.29+(ix%2)*.145
        if px<-3.5 and yy>-2.5:continue
        o=cube('Sidewalk paver',(px,yy,-.047+random.uniform(-.005,.005)),(.526,.278,.074),paving,.005)
        o.rotation_euler.z=random.uniform(-.004,.004)
cube('Sidewalk foundation',(1.6,-6.1,-.11),(11.8,8.5,.1),paving,.01)
cube('Street road',(-6.40,1.0,-.095),(4.40,32,.10),asphalt,.005)
for yy in range(-12,17,2):cube('Street painted line',(-4.46,yy,-.035),(.095,1.05,.004),yellow,0)
cube('Far sidewalk',(-9.08,4,-.02),(1.2,30,.14),paving,.008)

# Drains, curb chips and a side walkway, with a railing and utility guard.
for i in range(11):
    cube('Sidewalk drainage slit',(-4.01,-3.14+i*.05,-.004),(.35,.018,.015),black,.002)
for zz in [.36,1.04]:line('Side grey railing', [(-3.92,2.72,zz),(-3.92,5.70,zz)],.021,neighbour)
for yy in [2.72,3.5,4.3,5.05,5.7]:line('Railing uprights',[(-3.92,yy,.04),(-3.92,yy,1.06)],.016,neighbour)
for iy in range(14):
    cube('Side walkway slab',(-3.75,-.9+iy*.48,-.015),(.67,.47,.065),cement,.004)
for i in range(12):
    cube('Sidewalk crack infill',(-3.9+random.random()*6,-3.72+random.random()*1.1,-.006),(.04+random.random()*.11,.009,.0015),asphalt,0)
# Warning guard resembles the striped street hardware in the original photo.
cube('Street guard base',(-4.25,.10,.06),(.35,.33,.10),black,.012)
for j in range(7):
    ring=cylinder('Striped pole guard',(-4.25,.10,.12+j*.083),.065,.083,yellow if j%2 else black)
line('Short hanging chain',[(-4.25,.10,.53),(-4.05,.33,.39),(-3.92,.62,.47)],.010,rust)
# A quiet leafless street tree supplies actual geometry for reflected branches in glazing.
line('Street tree trunk',[(-7.95,-4.6,0),(-7.93,-4.6,2.8),(-7.75,-4.55,4.3)],.085,neighbour)
for i in range(11):
    a=random.random()*math.tau;z=2.7+random.random()*1.45
    start=(-7.92,-4.6,z);end=(-7.92+math.cos(a)*random.uniform(.8,2.2),-4.6+math.sin(a)*random.uniform(.6,1.65),z+random.uniform(.7,1.6))
    line('Tree bare branch',[start,((start[0]+end[0])*.5,(start[1]+end[1])*.5,z+.55),end],.018,neighbour)
    for j in range(3):
        t=.4+j*.22;root=tuple(start[k]+(end[k]-start[k])*t for k in range(3))
        line('Tree fine twig',[root,(root[0]+random.uniform(-.5,.5),root[1]+random.uniform(-.5,.5),root[2]+random.uniform(.3,.7))],.006,neighbour)
# Side exposed brickwork and service panel keep the long wall from being featureless.
for row in range(13):
    for col in range(3):cube('Exposed corner brick',(-3.273,2.89+col*.18+(row%2)*.085,.28+row*.075),(.033,.17,.064),brick,.003)
cube('Small wall service box',(-3.31,2.76,1.30),(.09,.22,.28),cream,.012)
for i in range(4):cube('Service box vent',(-3.36,2.76,1.22+i*.03),(.007,.16,.006),black,.001)

# A small plant, street stool, utility pole and wires make the side view a real place.
for yy in [-1.6,-1.22]:
    for xx in [-4.1,-3.80]:line('Street stool leg',[(xx,yy,.01),(xx+.025,yy,.69)],.022,cream)
cube('Street stool seat',(-3.94,-1.41,.72),(.40,.44,.044),cream)
line('Street stool back',[(-4.10,-1.2,.72),(-4.1,-1.2,1.03),(-3.80,-1.2,1.03),(-3.8,-1.2,.72)],.022,cream)
cylinder('Utility pole',(-4.32,4.5,3.25),.07,6.5,neighbour)
for zz in [5.9,6.22]:cube('Pole crossbar',(-4.32,4.5,zz),(1.4,.1,.08),black)
for xx in [-4.85,-4.45,-4.0]:
    line('Utility wire',[(xx,yy,6.20-.25*math.sin((yy+6)/17*math.pi)) for yy in [-8+j*.6 for j in range(50)]],.008,black)
for i in range(4):
    xx=-9.8 if i%2==0 else -3.0;yy=7+i*3.2
    cube('Neighbor building',(xx,yy,2.8),(3,2.4,5.6),neighbour,.025)
    for zz in [1.6,3.5]:
        for offset in [-.65,.65]:cube('Neighbor window',(xx+offset,yy-1.215,zz),(.66,.02,.94),black,.005)

# Anchor metadata exported as empty nodes; the browser projects these 3D points.
anchors={'prologue':(0,-2.02,4.0),'ai-product':(-.75,-1.87,2.15),'film':(1.83,-1.87,2.15),'editorial':(-2.58,-1.87,1.90),'research':(-.75,-2.24,.83),'about':(-3.43,.05,1.65)}
for key,p in anchors.items():
    o=bpy.data.objects.new('Anchor_'+key,None);bpy.context.collection.objects.link(o);o.location=p;o['category']=key

def area(name,pos,target,power,size,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
def point(name,pos,power,color):
    data=bpy.data.lights.new(name,'POINT');data.energy=power;data.shadow_soft_size=.12;data.color=color
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=pos;lamps.append(o);return o
daykey=area('Overcast sky',(-4,-6,10),(0,-1,1.8),1200,8,(.85,.93,1))
fill=area('Street bounce',(3,-6,5),(0,0,1.3),500,5,(1,.94,.80))
for xx in [-.3,2.1]:
    cube('Fascia lamp casing',(xx,-1.98,3.53),(.32,.17,.09),black,.025)
    cube('Fascia lamp glass',(xx,-1.985,3.48),(.22,.115,.012),bulb,.015,False)
    point('Fascia practical',(xx,-2.00,3.38),0,(1,.55,.20))
for yy in [.85,2.45]:point('Side lantern practical',(-3.72,yy,2.58),0,(1,.57,.26))
for px in [-.6,1.5]:point('Interior practical',(px,.3,2.87),0,(1,.57,.23))

world=bpy.data.worlds.new('Street sky');world.use_nodes=True;bpy.context.scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.54,.62,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.28
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.cycles.device='CPU'
scene.cycles.samples=12
scene.cycles.max_bounces=3
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1100;scene.render.resolution_y=770;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
camera_data=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camera_data);bpy.context.collection.objects.link(cam)
cam.location=(-8.0,-12.0,6.1);cam.rotation_euler=(Vector((-.15,-.55,2.80))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=45;scene.camera=cam

# Preserve an editable original with procedural materials before joining/baking.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casa-scene.blend'))
print('MODEL_READY',len(static),'static parts,',len(dynamic),'dynamic parts',flush=True)
if not skip_renders:
    scene.render.filepath=str(OUT/'blender-day.png');bpy.ops.render.render(write_still=True)

# Pack a single UV atlas for static surfaces, then bake the real Cycles illumination.
bpy.ops.object.select_all(action='DESELECT')
for o in static:o.select_set(True)
bpy.context.view_layer.objects.active=static[0];bpy.ops.object.join();combined=bpy.context.object;combined.name='Storefront_Baked_Static'
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
combined.data.uv_layers.active.name='BakedUV'
atlas_size=4096
def bake(name):
    img=bpy.data.images.new(name,width=atlas_size,height=atlas_size,alpha=False)
    for m in combined.data.materials:
        if m:
            node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;node.select=True;m.node_tree.nodes.active=node
    bpy.context.view_layer.objects.active=combined;combined.select_set(True)
    scene.render.bake.use_clear=True;scene.render.bake.margin=8
    bpy.ops.object.bake(type='COMBINED')
    img.filepath_raw=str(ASSETS/(name+'.jpg'));img.file_format='JPEG';img.save()
    print('BAKED',name,flush=True);return img
day=bake('casa-day-baked')
# Blue hour uses the same mesh and UVs, a separate world/area/practical-light solution.
daykey.data.energy=90;daykey.data.color=(.31,.44,.72);fill.data.energy=75;fill.data.color=(.37,.51,.66)
world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.09,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.16
for o in lamps:o.data.energy=75 if 'Interior' in o.name else 55
night=bake('casa-night-baked')
if not skip_renders:
    scene.render.filepath=str(OUT/'blender-night.png');bpy.ops.render.render(write_still=True)

# GLB carries genuine geometry and the day atlas. Night atlas crossfades at runtime.
baked=bpy.data.materials.new('Cycles_Baked_Atlas');baked.use_nodes=True
nodes=baked.node_tree.nodes;links=baked.node_tree.links;p=nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=1
tex=nodes.new('ShaderNodeTexImage');tex.image=day;links.new(tex.outputs['Color'],p.inputs['Base Color'])
combined.data.materials.clear();combined.data.materials.append(baked)
for poly in combined.data.polygons:poly.material_index=0
# Preserve the baked UVs while reducing redundant fine text and bevel triangles.
bpy.context.view_layer.objects.active=combined
mod=combined.modifiers.new('Web delivery reduction','DECIMATE');mod.ratio=.5
bpy.ops.object.modifier_apply(modifier=mod.name)
for o in list(bpy.data.objects):
    if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'casa-storefront.glb'),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False,export_materials='EXPORT',export_apply=True)
stats={'static_parts':len(static),'dynamic_parts':len(dynamic),'mesh_vertices':len(combined.data.vertices),'mesh_triangles':sum(len(p.vertices)-2 for p in combined.data.polygons),'atlas_size':atlas_size,'software':bpy.app.version_string,'anchors':anchors,'note':'Fully modeled in Blender; two Cycles combined-light atlases; no photo background.'}
(ASSETS/'model-info.json').write_text(json.dumps(stats,indent=2))
import shutil
shutil.copy2(ASSETS/'casa-storefront.glb',OUT/'casa-storefront.glb')
print('EXPORT_READY',json.dumps(stats),flush=True)
