"""Add tactile joinery and set dressing to the existing Blender reconstructions.

Preserves the lighting atlases, moving door, scene anchors and background split.
Both the web assets and the unmerged editable originals receive the same details.
Run: Blender --background --python refine_casa_alley.py -- casa|alley
"""
import bpy, bmesh, math, random, sys, json, struct
import numpy as np
from pathlib import Path
from mathutils import Vector

SITE=Path(__file__).resolve().parents[1]
OUT=SITE.parents[1]/'outputs'
ASSETS=SITE/'dist/assets'
KIND=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'casa'
random.seed(125)
parts=[]

def image(name, rgb, normal=False):
    h,w=rgb.shape[:2]
    im=bpy.data.images.new(name,width=w,height=h,alpha=True)
    if normal:im.colorspace_settings.name='Non-Color'
    rgba=np.ones((h,w,4),np.float32);rgba[:,:,:3]=rgb
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw=str(ASSETS/(name+('.png' if normal else '.jpg')));im.file_format='PNG' if normal else 'JPEG';im.save()
    return im

def texture_mat(name,color,kind='plaster',rough=.75,metal=0):
    m=bpy.data.materials.new('Refinement_'+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF')
    if not p:
        p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs[0],out.inputs['Surface'])
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if kind:
        N=512;rng=np.random.default_rng(724 if kind=='wood' else 831)
        y,x=np.mgrid[0:N,0:N]/N
        if kind=='wood':
            bend=.018*np.sin(x*18)+.008*np.sin(x*49)
            grain=(np.sin((y+bend)*370)+.36*np.sin((y+bend)*785)+.18*np.sin((y+bend)*1670))/1.54
            knots=np.exp(-((x-.32)**2/.002+(y-.47)**2/.00009))+.7*np.exp(-((x-.76)**2/.002+(y-.19)**2/.00008))
            height=.08*grain+.11*np.sin(y*25)-.22*knots
            variation=height+rng.normal(0,.013,(N,N))
        elif kind=='cloth':
            height=.035*(np.sin(x*math.tau*170)+np.sin(y*math.tau*172))
            variation=height+rng.normal(0,.018,(N,N))
        else:
            height=.055*np.sin(x*29)*np.sin(y*38)+.023*np.sin(x*107)*np.sin(y*83)
            variation=height+rng.normal(0,.022,(N,N))
        rgb=np.clip(np.array(color)[None,None,:]*(1+variation[:,:,None]),0,1)
        tex=image('refine-'+KIND+'-'+name.lower().replace(' ','-'),rgb)
        n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=tex;m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
        dy,dx=np.gradient(height)
        vec=np.stack((-dx*(7 if kind=='wood' else 3),-dy*(7 if kind=='wood' else 3),np.ones_like(dx)),axis=2)
        vec/=np.linalg.norm(vec,axis=2)[:,:,None]
        norm=image('refine-'+KIND+'-'+name.lower().replace(' ','-')+'-normal',(vec+1)*.5,True)
        tn=m.node_tree.nodes.new('ShaderNodeTexImage');tn.image=norm
        nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.32
        m.node_tree.links.new(tn.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs[0],p.inputs['Normal'])
    return m

def cube(name,pos,size,mat,bevel=.004,parent=None):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector((v.co.x*size[0],v.co.y*size[1],v.co.z*size[2]))
    if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=3,affect='EDGES',clamp_overlap=True)
    mesh=bpy.data.meshes.new('Refinement_'+name);bm.to_mesh(mesh);bm.free();mesh.update()
    uv=mesh.uv_layers.new(name='DetailUV')
    # Box projections make grain continuous on each plank instead of using noise.
    for poly in mesh.polygons:
        axis=max(range(3),key=lambda i:abs(poly.normal[i]));axes=[i for i in range(3) if i!=axis]
        if axis==1:axes=[0,2]
        for li in poly.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]]/max(size[axes[0]],.001)+.5,co[axes[1]]/max(size[axes[1]],.001)+.5)
    o=bpy.data.objects.new('Refinement_'+name,mesh);bpy.context.collection.objects.link(o);o.location=pos;o.data.materials.append(mat)
    if parent:
        bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world
    parts.append(o);return o

def tube(name,points,r,mat,closed=False):
    # Direct mesh construction avoids curve operators and gives stable export UVs.
    pts=[Vector(p) for p in points];verts=[];faces=[];S=10
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        side=tangent.cross(Vector((0,0,1)))
        if side.length<.1:side=tangent.cross(Vector((0,1,0)))
        side.normalize();up=tangent.cross(side).normalized()
        for j in range(S):verts.append(p+r*(math.cos(j*math.tau/S)*side+math.sin(j*math.tau/S)*up))
    for i in range(len(pts)-1):
        for j in range(S):faces.append((i*S+j,i*S+(j+1)%S,(i+1)*S+(j+1)%S,(i+1)*S+j))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='DetailUV')
    for poly in mesh.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:
            vi=mesh.loops[li].vertex_index;uv.data[li].uv=(vi%S/(S-1),vi//S/max(1,len(pts)-1))
    o=bpy.data.objects.new('Refinement_'+name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(mat);parts.append(o);return o

def disk(name,pos,r,depth,mat,axis='Z'):
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=20,radius1=r,radius2=r,depth=depth)
    mesh=bpy.data.meshes.new(name);bm.to_mesh(mesh);bm.free();mesh.update()
    o=bpy.data.objects.new('Refinement_'+name,mesh);bpy.context.collection.objects.link(o);o.location=pos;o.data.materials.append(mat)
    if axis=='Y':o.rotation_euler.x=math.pi/2
    elif axis=='X':o.rotation_euler.y=math.pi/2
    for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
    parts.append(o);return o

def screw(pos,mat,axis='Z',scale=1):
    disk('Countersunk screw',pos,.012*scale,.0025,mat,axis)
    x,y,z=pos
    if axis=='Z':cube('Screw cross slot',(x,y,z+.0015),(.014*scale,.0016*scale,.0011),dark,0)
    elif axis=='Y':cube('Screw cross slot',(x,y-.0015,z),(.014*scale,.0011,.0016*scale),dark,0)
    else:cube('Screw cross slot',(x-.0015,y,z),(.0011,.0016*scale,.014*scale),dark,0)

def remove_people():
    doomed=[]
    for o in bpy.data.objects:
        chain=[o];ancestor=o.parent
        while ancestor:
            chain.append(ancestor);ancestor=ancestor.parent
        if any(q.name.startswith(('ActorMan','ActorWoman','InteriorPair','DinerPair','AlleyPair','NightSharedCoat','Shared brown coat','Coat subtle','Coat horn')) for q in chain):doomed.append(o)
    for o in doomed:
        if o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)

def decorate():
    global parts,dark
    parts=[];remove_people()
    for o in list(bpy.data.objects):
        if o.name.startswith('Refinement_'):bpy.data.objects.remove(o,do_unlink=True)
    wood=texture_mat('Walnut joinery',(.14,.092,.052) if KIND=='casa' else (.055,.20,.205),'wood',.58)
    oak=texture_mat('Oak end grain',(.40,.26,.135) if KIND=='casa' else (.22,.14,.075),'wood',.66)
    plaster=texture_mat('Lime plaster',(.47,.35,.18) if KIND=='casa' else (.19,.29,.32),'plaster',.96)
    paper=texture_mat('Warm cotton paper',(.81,.72,.53),'plaster',.93)
    cloth=texture_mat('Woven cloth',(.23,.16,.095),'cloth',.97)
    dark=texture_mat('Soft black painted iron',(.018,.026,.025),None,.48,.48)
    brass=texture_mat('Aged brass',(.48,.32,.12),None,.36,.78)
    ceramic=texture_mat('Ivory glazed ceramic',(.73,.70,.60),None,.27)
    terracotta=texture_mat('Terracotta lip',(.29,.12,.065),'plaster',.87)
    leaf=texture_mat('Living foliage',(.037,.12,.052),None,.76)
    if KIND=='casa':
        # Nested bead mouldings catch light from every scene camera.
        for cx in [-.75,1.83]:
            for xx in [cx-1.105,cx+1.105]:
                cube('Window vertical wood veneer',(xx,-1.828,1.78),(.052,.012,2.52),wood,.004)
                tube('Recessed window bead',[(xx+.032,-1.84,.4),(xx+.032,-1.84,2.56)],.008,oak)
                for z in [1.34,2.06,2.50]:screw((xx,-1.837,z),brass,'Y',.65)
            for zz in [1.26,1.70,2.12,2.56]:
                cube('Wood grain cross rail',(cx,-1.823,zz),(2.23,.017,.034),wood,.004)
                cube('Brass glass gasket',(cx,-1.839,zz-.024),(2.20,.008,.006),brass,.002)
            # Frame the lower panels with two levels of recessed beading.
            for zz in [.375,1.08]:
                cube('Lower panel raised bead',(cx,-1.842,zz),(1.955,.026,.038),wood,.005)
                cube('Lower panel inner moulding',(cx,-1.86,zz+(.027 if zz<.5 else -.027)),(1.91,.01,.012),oak,.003)
            for xx in [cx-.95,cx+.95]:cube('Panel edge moulding',(xx,-1.841,.728),(.038,.022,.73),wood,.004)
            arc=[(cx+math.cos(a)*1.14,-1.804,2.55+math.sin(a)*1.14) for a in np.linspace(0,math.pi,70)]
            tube('Arch highlight wood bead',arc,.010,oak)
        # Closely spaced rim screws and folded metal lap joints.
        for xx in np.linspace(-3.18,3.18,10):
            screw((xx,-1.991,3.65),brass,'Y',.75);screw((xx,-1.991,4.40),brass,'Y',.75)
        # Straight timber lengths retain grain and rounded hand worn corners.
        for cx,length in [(-.76,1.97),(1.85,1.86)]:
            for yy in [-2.07,-2.22,-2.37]:
                cube('Oak seat tactile veneer',(cx,yy,.801),(length-.02,.125,.009),oak,.003)
                for xx in [cx-length*.4,cx+length*.4]:screw((xx,yy,.808),dark)
            for xx in [cx-length*.4,cx+length*.4]:
                cube('Bench leg wood face',(xx,-2.402,.46),(.096,.008,.45),oak,.003)
                for z in [.43,.68]:screw((xx,-2.409,z),brass,'Y',.65)
        # Four sheets curl away from the wall at the bottom edge, with tiny pinheads.
        for i in range(4):
            cx=-2.81+(i%2)*.46;z=2.20-(i//2)*.64
            points=[(cx-.215,-1.840,z-.25),(cx-.105,-1.848,z-.294),(cx+.10,-1.866,z-.287),(cx+.217,-1.846,z-.278)]
            tube('Poster curled paper edge',points,.0045,paper)
            for xx in [cx-.18,cx+.18]:screw((xx,-1.850,z+.265),brass,'Y',.30)
            cube('Paper lower tear',(cx+.12,-1.843,z-.285),(.055,.008,.012),paper,.002)
        # More legible foreground display through the actual glazing: plate rims,
        # ribbed pastries, envelopes, ceramic handles and brass shelf rail.
        for cx in [-1.20,-.75,-.30]:
            disk('Display porcelain saucer',(cx,-1.24,1.29),.17,.018,ceramic)
            tube('Saucer rolled lip',[(cx+.163*math.cos(a),-1.24+.163*math.sin(a),1.304) for a in np.linspace(0,math.tau,50)],.008,ceramic)
            for k in range(3):
                yy=-1.30+k*.055
                cube('Pastry ridged churro',(cx,yy,1.338),(.25,.032,.036),oak,.010)
                for j in [-1,0,1]:tube('Churro toasted ridge',[(cx-.11,yy+j*.008,1.358),(cx+.11,yy+j*.008,1.358)],.003,terracotta)
        cube('Display shelf warm oak',(-.75,-1.25,1.245),(2.08,.48,.058),oak,.010)
        tube('Pastry display brass guard',[(-1.75,-1.51,1.28),(-1.75,-1.51,1.43),(.25,-1.51,1.43),(.25,-1.51,1.28)],.009,brass)
        for cx in [1.46,2.08]:
            disk('Window cup',(cx,-1.25,1.385),.079,.15,ceramic)
            tube('Ceramic cup handle',[(cx+.079,-1.25,1.4),(cx+.13,-1.25,1.405),(cx+.14,-1.25,1.45),(cx+.10,-1.25,1.46),(cx+.07,-1.25,1.445)],.012,ceramic)
            disk('Cup dark interior',(cx,-1.25,1.462),.067,.001,dark)
            disk('Cup saucer',(cx,-1.25,1.315),.123,.012,ceramic)
        cube('Display folded menu',(1.73,-1.05,1.54),(.29,.012,.43),paper,.004)
        # The photographed side door keeps its runtime hinge: affix real backplates.
        door=bpy.data.objects.get('DoorPivot')
        for zz in [1.25,1.55]:
            o=cube('Door oval handle backplate',(-3.402,.37,zz),(.012,.072,.070),brass,.025,parent=door)
        for yy in [-.49,.58]:
            for zz in [.45,1.42,2.55]:
                o=disk('Door brass hinge knuckle',(-3.40,yy,zz),.021,.10,brass)
                if door:
                    bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=door;o.matrix_world=world
        # Fine stucco edges and repaired concrete chips along wall joints.
        for zz in [4.55,5.6]:
            for i in range(18):
                x=-3.08+i*.34;cube('Spalled concrete seam',(x,-1.581,zz+.022),(random.uniform(.03,.09),.013,random.uniform(.006,.018)),plaster,.003)
        # A real terracotta planter beside the bench, with layered rim and leaves.
        disk('Terracotta planter',(3.0,-2.30,.47),.175,.50,terracotta)
        tube('Rolled planter lip',[(3+.180*math.cos(a),-2.30+.180*math.sin(a),.73) for a in np.linspace(0,math.tau,40)],.023,terracotta)
        disk('Planter soil',(3,-2.30,.717),.156,.01,dark)
        for j in range(16):
            a=j*2.39;rr=.04+(j%4)*.04;end=(3+math.cos(a)*rr,-2.3+math.sin(a)*rr,.84+.04*(j%4))
            tube('Plant small stalk',[(3,-2.3,.72),end],.004,leaf)
            o=cube('Glossy pointed leaf',end,(.12,.034,.014),leaf,.012);o.rotation_euler.z=a
    else:
        # Empty seat with an intentionally folded scarf: no suspended cloth.
        bx=-2.06;by=1.77
        for j in range(5):
            cube('Bench teal grain surface',(bx,by-.39+j*.18,.608),(2.43,.147,.011),wood,.003)
            for x in [bx-1.06,bx+1.06]:screw((x,by-.39+j*.18,.617),brass,scale=.75)
        for j in range(4):
            z=.78+j*.145;y=by+.412+j*.025
            o=cube('Bench back wood grain',(bx,y,z),(2.43,.014,.10),wood,.003);o.rotation_euler.x=-.13
            for x in [bx-1.1,bx+1.1]:screw((x,y-.010,z),brass,'Y',.80)
        for i in range(3):
            o=cube('Folded wool scarf layer',(-1.63,1.72,.653+i*.024),(.50-.02*i,.32,.023),cloth,.014);o.rotation_euler.z=-.11
        for i in range(13):tube('Scarf soft fringe',[(-1.865+i*.035,1.53,.68),(-1.87+i*.035,1.48,.666)],.0028,cloth)
        cube('Creased letter on empty bench',(-2.65,1.61,.628),(.32,.20,.004),paper,.002)
        cube('Letter envelope flap',(-2.65,1.62,.632),(.29,.11,.003),paper,.001)
        # Retain the original facade coordinates exactly, adding weathered edging
        # rather than placing any photographic background planes.
        facade_specs=[(-3.08,2.73,0,5.6,4.8),(-.27,4.57,math.pi/2,3.65,5.25),(-.27,8.60,math.pi/2,4.4,5.85),(4.06,3.8,-math.pi/2,4.1,5.70),(4.06,8.,-math.pi/2,4.3,5.2),(1.88,10.95,0,4.3,5.75)]
        for fi,(cx,cy,angle,w,h) in enumerate(facade_specs):
            def world(x,y,z):return(cx+x*math.cos(angle)-y*math.sin(angle),cy+x*math.sin(angle)+y*math.cos(angle),z)
            # Inset brick and limewash repairs cluster near the ground, not random
            # speckling across the whole frame.
            for row in range(5):
                for col in range(5):
                    x=w*.32-.42+col*.17+(row%2)*.075
                    o=cube('Exposed weathered lower brick',world(x,-.023,.18+row*.075),(.16,.031,.063),terracotta,.004);o.rotation_euler.z=angle
            for row in [0,1]:
                for j in range(12):
                    x=-w*.46+j*w*.079
                    o=cube('Limewash chipped plinth',world(x,-.025,.08+row*.039),(.045+random.random()*.11,.026,.020+random.random()*.014),plaster,.003);o.rotation_euler.z=angle
            dx=-w*.23
            for z in [.24,.82,1.40]:
                o=cube('Door iron strap hinge',world(dx-.43,-.166,z),(.105,.019,.043),dark,.005);o.rotation_euler.z=angle
                for off in [-.025,.025]:disk('Door hinge rivet',world(dx-.43+off,-.18,z),.008,.006,brass,'Y').rotation_euler.z=angle
            for x,z in [(-w*.23,h-.95),(w*.25,h-.95)]:
                # Split shutter grain boards, meeting stile and forged holdbacks.
                for sx in [-1,1]:
                    o=cube('Shutter grain edge',world(x+sx*.31,-.172,z),(.025,.021,1.05),wood,.003);o.rotation_euler.z=angle
                    o=cube('Shutter forged holdback',world(x+sx*.38,-.188,z-.34),(.054,.025,.077),dark,.008);o.rotation_euler.z=angle
                for zz in [z-.55,z+.55]:
                    o=cube('Weathered sill drip groove',world(x,-.245,zz),(.88,.023,.012),dark,.003);o.rotation_euler.z=angle
            # Linear wall cracks, caulking and old screw bosses.
            for j in range(5):
                x=-w*.44+j*.10
                tube('Lime plaster settlement crack',[world(x,-.020,h*.42),world(x+.022,-.020,h*.42-.11),world(x-.006,-.020,h*.42-.16),world(x+.041,-.020,h*.42-.24)],.0019,dark)
        # Warm lantern glass seams, brass corners, and a true point bulb silhouette.
        lx=-2.56;ly=2.05;lz=3.12
        for x in [lx-.13,lx+.13]:
            tube('Lantern brass glazing edge',[(x,1.918,lz-.23),(x,1.918,lz+.23)],.007,brass)
        for z in [lz-.22,lz+.22]:tube('Lantern glazing edge',[(lx-.12,1.917,z),(lx+.12,1.917,z)],.006,brass)
        for z in [2.60,3.30]:
            for j in range(3):
                cube('Lantern bracket rivet',(-2.56+.030*(j-1),2.593,z),(.014,.020,.014),brass,.005)
        # Botanical massing gains fine leaves around the existing modeled roses.
        for cx,cy,h,r in [(-3.74,1.67,.31,.23),(-3.47,1.09,.25,.20),(-3.97,1.02,.24,.17)]:
            tube('Terracotta worn pot rim',[(cx+r*math.cos(a),cy+r*math.sin(a),h+.012) for a in np.linspace(0,math.tau,44)],.012,terracotta)
            for j in range(14):
                a=j*2.397;z=h+.11+(j%3)*.065
                x=cx+math.cos(a)*r*.82;y=cy+math.sin(a)*r*.82
                o=cube('Rose serrated leaf',(x,y,z),(.085,.028,.010),leaf,.008);o.rotation_euler.z=a
        # Street drainage/iron cover and a narrow utility manhole give the empty
        # foreground something tangible without competing with the bench.
        cube('Set drain outer iron frame',(1.15,1.07,.017),(.60,.43,.025),dark,.015)
        for j in range(9):cube('Set drain slit',(1.15,.90+j*.045,.033),(.49,.021,.006),brass,.003)
    return parts

def merge_details():
    # Keep moving-door attachments in their hierarchy. All fixed pieces share
    # ten joined primitives, so hundreds of tiny fasteners do not add draw calls.
    groups={}
    for o in parts:
        key=(o.data.materials[0].name,o.parent.name if o.parent else '')
        groups.setdefault(key,[]).append(o)
    for (name,parent),objects in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
        o=bpy.context.object;o.name='Refinement_'+name.removeprefix('Refinement_')+('_Door' if parent else '')
        o['detail_refinement']=True

def export_web():
    filename='casa-storefront.glb' if KIND=='casa' else 'night-alley.glb'
    path=ASSETS/filename
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False,export_materials='EXPORT',export_apply=True)
    # Preserve compact byte normals on the dense pre-existing reconstruction.
    glb=path.read_bytes();size=struct.unpack_from('<I',glb,12)[0];data=json.loads(glb[20:20+size]);binlen=struct.unpack_from('<I',glb,20+size)[0];old=glb[28+size:28+size+binlen]
    normals={p['attributes']['NORMAL'] for m in data['meshes'] for p in m['primitives'] if 'NORMAL' in p['attributes']};replacement={}
    for ai in normals:
        a=data['accessors'][ai];v=data['bufferViews'][a['bufferView']]
        if a['componentType']!=5126:continue
        stride=v.get('byteStride',12);start=v.get('byteOffset',0)+a.get('byteOffset',0)
        rep=bytearray()
        for i in range(a['count']):rep.extend(struct.pack('<4b',*[max(-127,min(127,round(n*127))) for n in struct.unpack_from('<3f',old,start+i*stride)],0))
        replacement[a['bufferView']]=bytes(rep);v['byteStride']=4;a['byteOffset']=0;a['componentType']=5120;a['normalized']=True;a.pop('min',None);a.pop('max',None)
    # Imported original alley geometry already carries a 1/1024 node scale.
    # Quantize its integer-valued coordinates directly, while new metre-valued
    # details get the compensating node scale. Neither world transform changes.
    pos_factors={}
    for model in data['meshes']:
        for primitive in model['primitives']:
            ai=primitive['attributes']['POSITION'];a=data['accessors'][ai]
            pos_factors[ai]=1 if max(abs(n) for n in a['min']+a['max'])>32 else 1024
    for ai,factor in pos_factors.items():
        a=data['accessors'][ai];v=data['bufferViews'][a['bufferView']]
        if a['componentType']!=5126:continue
        stride=v.get('byteStride',12);start=v.get('byteOffset',0)+a.get('byteOffset',0);rep=bytearray();values=[]
        for i in range(a['count']):
            q=[round(n*factor) for n in struct.unpack_from('<3f',old,start+i*stride)]
            assert min(q)>=-32768 and max(q)<32768
            rep.extend(struct.pack('<4h',*q,0));values.append(q)
        replacement[a['bufferView']]=bytes(rep);v['byteStride']=8;a['byteOffset']=0;a['componentType']=5122
        a['min']=[min(q[j] for q in values) for j in range(3)];a['max']=[max(q[j] for q in values) for j in range(3)]
    for node in data['nodes']:
        if 'mesh' not in node:continue
        ai=data['meshes'][node['mesh']]['primitives'][0]['attributes']['POSITION'];factor=pos_factors[ai]
        if factor==1:continue
        if 'matrix' in node:
            for i in [0,1,2,4,5,6,8,9,10]:node['matrix'][i]/=factor
        else:node['scale']=[s/factor for s in node.get('scale',[1,1,1])]
    uv_ids={p['attributes']['TEXCOORD_0'] for m in data['meshes'] for p in m['primitives'] if 'TEXCOORD_0' in p['attributes']}
    for ai in uv_ids:
        a=data['accessors'][ai];v=data['bufferViews'][a['bufferView']]
        if a['componentType']!=5126:continue
        stride=v.get('byteStride',8);start=v.get('byteOffset',0)+a.get('byteOffset',0);rep=bytearray();valid=True
        for i in range(a['count']):
            uv=struct.unpack_from('<2f',old,start+i*stride)
            if min(uv)<-.0001 or max(uv)>1.0001:valid=False;break
            rep.extend(struct.pack('<2H',*[max(0,min(65535,round(n*65535))) for n in uv]))
        if valid:
            replacement[a['bufferView']]=bytes(rep);v['byteStride']=4;a['byteOffset']=0;a['componentType']=5123;a['normalized']=True;a.pop('min',None);a.pop('max',None)
    binary=bytearray()
    for vi,v in enumerate(data['bufferViews']):
        while len(binary)%4:binary.append(0)
        raw=replacement.get(vi,old[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);v['byteOffset']=len(binary);v['byteLength']=len(raw);binary.extend(raw)
    while len(binary)%4:binary.append(0)
    data['buffers'][0]['byteLength']=len(binary)
    for key in ['extensionsUsed','extensionsRequired']:
        data.setdefault(key,[])
        if 'KHR_mesh_quantization' not in data[key]:data[key].append('KHR_mesh_quantization')
    chunk=json.dumps(data,separators=(',',':')).encode();chunk+=b' '*((-len(chunk))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(chunk)+len(binary))+struct.pack('<II',len(chunk),0x4e4f534a)+chunk+struct.pack('<II',len(binary),0x004e4942)+binary)
    return path,data

# First preserve a useful editable original, retaining all the initial parts and
# procedural materials. Then augment the compact web mesh in the same coordinates.
original=OUT/('casa-scene.blend' if KIND=='casa' else 'night-alley.blend')
bpy.ops.wm.open_mainfile(filepath=str(original));decorate()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(KIND+'-detailed.blend')))
print('EDITABLE_DETAIL_READY',KIND,len(parts),flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ASSETS/('casa-storefront.glb' if KIND=='casa' else 'night-alley.glb')))
decorate();added=len(parts);merge_details();path,gltf=export_web()
meta_path=ASSETS/('model-info.json' if KIND=='casa' else 'night-alley-info.json')
meta=json.loads(meta_path.read_text())
meta['refinement']={'date':'2026-10-12','detail_parts':added,'textures':'512 px authored albedo and tangent normal maps','people':0,'editable_blend':KIND+'-detailed.blend'}
meta['glb_bytes']=path.stat().st_size;meta['meshes']=len(gltf['meshes'])
if KIND=='alley':
    meta['nodes']['actors']=[];meta['nodes'].pop('coat',None)
    meta['note']='A modeled empty blue-hour alley. Refined wood grain, window hardware, plaster repairs, bare bench with folded scarf and letter, lantern brass and rose foliage. No people or photographic backdrop.'
    meta['encoding']='Preserved original quantized positions and normalized byte normals; refinement uses float positions and UVs.'
meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('WEB_DETAIL_READY',KIND,added,len(gltf['meshes']),path.stat().st_size,flush=True)
