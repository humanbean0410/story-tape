"""A small, inhabitable Chinese courtyard, built from geometry in Blender.

The user photographs are architectural references only. No photograph or image
plane forms the set. Blender X = world X; Blender Y = -Three Z; Blender Z = Y.
Run with Blender --background --factory-startup --python this_file.py.
The editable blend keeps individual parts; the web export merges by material.
"""
import bpy, bmesh, math, random, json, struct, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix

SITE=Path(__file__).resolve().parents[1]
OUT=SITE.parents[1]/'outputs'
ASSETS=SITE/'dist/assets'
TEXTURES=ASSETS/'courtyard-textures'
TEXTURES.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
random.seed(8371)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
groups={k:[] for k in ['CourtyardArchitecture','CourtyardFlora','CourtyardForeground','CourtyardEnvironment','CourtyardPracticals']}
root=bpy.data.objects.new('ChineseCourtyard',None);bpy.context.collection.objects.link(root)
material_stats=[]

def noise_field(n,seed,scales):
    rng=np.random.default_rng(seed); out=np.zeros((n,n),np.float32)
    ky=np.fft.fftfreq(n)[:,None];kx=np.fft.fftfreq(n)[None,:]
    for s,weight in scales:
        field=rng.normal(0,1,(n,n));f=np.fft.fft2(field)
        f*=np.exp(-(kx*kx+ky*ky)*(s*s)*math.pi**2)
        v=np.fft.ifft2(f).real;v=(v-v.mean())/(v.std()+1e-8)
        out+=v*weight
    return out

def save_image(name,array,normal=False):
    h,w=array.shape[:2]
    if normal:
        step=max(1,h//256)
        if step>1:
            vectors=array*2-1;vectors=vectors.reshape(h//step,step,w//step,step,3).mean(axis=(1,3));vectors/=np.linalg.norm(vectors,axis=2)[:,:,None];array=(vectors+1)*.5;h,w=array.shape[:2]
        array=np.round(np.clip(array,0,1)*255)/255
    im=bpy.data.images.new(name,width=w,height=h,alpha=True)
    if normal: im.colorspace_settings.name='Non-Color'
    rgba=np.ones((h,w,4),np.float32);rgba[:,:,:3]=np.clip(array,0,1)
    im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(TEXTURES/(name+('.png' if normal else '.jpg')))
    im.file_format='PNG' if normal else 'JPEG';im.save();im.pack();return im

def material(name,color,kind=None,n=512,rough=.8,metal=0,seed=1):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');p.name='Principled BSDF';out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if kind:
        rng=np.random.default_rng(seed);yy,xx=np.mgrid[0:n,0:n]/n
        if kind=='plaster':
            coarse=noise_field(n,seed,[(130,.18),(45,.15),(14,.07),(3,.018)])
            height=noise_field(n,seed+1,[(18,.2),(4,.3),(1,.04)])
            damp=np.clip(coarse-.03,0,.6)
            # Wide, vertical rain streaks and mineral blooms, not film grain.
            streak=np.zeros((n,n),np.float32)
            for i in range(28):
                x0=rng.uniform(0,1);y0=rng.uniform(-.15,.9);length=rng.uniform(.10,.45);width=rng.uniform(.004,.038)
                streak+=np.exp(-((xx-x0+.009*np.sin(yy*13)) / width)**2)*np.clip((yy-y0)/.018,0,1)*np.clip((y0+length-yy)/.055,0,1)*rng.uniform(.02,.18)
            tone=1+coarse*.32-streak-damp*.36
            rgb=np.array(color)[None,None,:]*tone[:,:,None]
            warm=np.clip(-coarse-.09,0,.35);rgb[:,:,0]+=warm*.13;rgb[:,:,1]+=warm*.065
            # Tiny, interrupted plaster fissures remain a surface detail.
            for k in range(13):
                x=int(rng.uniform(0,n));y=int(rng.uniform(0,n));angle=rng.uniform(-1,1)
                for q in range(int(rng.uniform(18,95))):
                    x=(x+int(round(math.sin(angle)+rng.normal(0,.55))))%n;y=(y+1)%n
                    if rng.random()>.22:rgb[y,x,:]*=.68;height[y,x]-=.04
                    angle+=rng.normal(0,.07)
            normal_scale=.65
        elif kind=='wood':
            warp=.012*np.sin(xx*19)+.007*np.sin(xx*43)+.002*np.sin(xx*107)
            grain=np.sin((yy+warp)*math.tau*88)+.44*np.sin((yy+warp)*math.tau*173)
            broad=noise_field(n,seed,[(48,.08),(12,.04),(2,.014)])
            knots=np.zeros((n,n))
            for x0,y0 in [(.2,.23),(.66,.62),(.82,.10)]:
                r=np.sqrt(((xx-x0)/.06)**2+((yy-y0)/.026)**2)
                knots+=np.exp(-r*r*.25)*(.07*np.sin(r*8)-.08)
            height=grain*.021+broad*.16+knots*.14
            rgb=np.array(color)[None,None,:]*(1+grain[:,:,None]*.055+broad[:,:,None]+knots[:,:,None])
            # Hand wear exposes thin warm grain along raised timber edges.
            normal_scale=1.3
        elif kind=='stone':
            v=noise_field(n,seed,[(72,.14),(19,.095),(3,.035),(1,.008)])
            height=noise_field(n,seed+12,[(18,.14),(3,.12),(1,.03)])
            rgb=np.array(color)[None,None,:]*(1+v[:,:,None]);normal_scale=1.15
        elif kind=='bark':
            warp=.025*np.sin(xx*31)+.009*np.sin(xx*97)
            split=np.maximum(0,np.sin((yy+warp)*math.tau*42))**7
            v=noise_field(n,seed,[(32,.08),(4,.02)])
            height=v*.8-split*.14
            rgb=np.array(color)[None,None,:]*(1+v[:,:,None]-split[:,:,None]*.35);normal_scale=1.8
        elif kind=='moss':
            v=noise_field(n,seed,[(40,.11),(8,.06),(2,.035)])
            height=v*.55;rgb=np.array(color)[None,None,:]*(1+v[:,:,None]);normal_scale=.85
        elif kind=='paper':
            v=noise_field(n,seed,[(12,.025),(2,.015),(1,.003)])
            height=v;rgb=np.array(color)[None,None,:]*(1+v[:,:,None]);normal_scale=.30
        tex=save_image(name.lower().replace(' ','-'),rgb)
        tn=m.node_tree.nodes.new('ShaderNodeTexImage');tn.image=tex;m.node_tree.links.new(tn.outputs['Color'],p.inputs['Base Color'])
        dy,dx=np.gradient(height);vec=np.stack((-dx*normal_scale*25,-dy*normal_scale*25,np.ones_like(dx)),2)
        vec/=np.linalg.norm(vec,axis=2)[:,:,None]
        norm=save_image(name.lower().replace(' ','-')+'-normal',(vec+1)*.5,True)
        nt=m.node_tree.nodes.new('ShaderNodeTexImage');nt.image=norm
        nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value={'plaster':.045,'wood':.16,'stone':.14,'bark':.30,'moss':.10,'paper':.035}.get(kind,.12)
        m.node_tree.links.new(nt.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs[0],p.inputs['Normal'])
    material_stats.append(name);return m

plaster=material('Courtyard ivory limewash',(.76,.755,.69),'plaster',1024,.95,seed=8371)
plaster2=material('Courtyard limestone repair',(.69,.68,.605),'plaster',512,.95,seed=9371)
stone=material('Courtyard worn grey sandstone',(.40,.405,.365),'stone',512,.92,seed=450)
stonepale=material('Courtyard raised stone carving',(.52,.525,.46),'stone',512,.85,seed=451)
stone_dark=material('Courtyard damp slate',(.225,.245,.21),'stone',512,.95,seed=452)
wood=material('Courtyard aged elm timber',(.245,.155,.09),'wood',1024,.70,seed=40)
wood_dark=material('Courtyard smoked corridor timber',(.115,.082,.054),'wood',512,.69,seed=42)
wood_edge=material('Courtyard rubbed timber moulding',(.32,.215,.128),'wood',512,.60,seed=46)
bark=material('Courtyard furrowed pine bark',(.22,.205,.17),'bark',512,.99,seed=86)
moss=material('Courtyard living moss',(.115,.195,.044),'moss',512,.99,seed=82)
earth=material('Courtyard loamy garden soil',(.145,.155,.095),'stone',512,.99,seed=190)
tiles=[material('Courtyard fired grey tile %02d'%i,(.28+.021*i,.29+.018*i,.265+.017*i),'stone' if i==2 else None,512,.83,seed=50) for i in range(5)]
leaves=[material('Courtyard pine needle %02d'%i,(.065+.018*i,.15+.022*i,.038+.008*i),None,rough=.82) for i in range(5)]
fern_mats=[material('Courtyard fern blade %02d'%i,(.055+.019*i,.14+.023*i,.045+.006*i),None,rough=.82) for i in range(4)]
iron=material('Courtyard oxidised door iron',(.088,.080,.063),None,rough=.53,metal=.65)
bronze=material('Courtyard aged bronze hardware',(.28,.225,.105),None,rough=.48,metal=.76)
red=material('Courtyard muted red silk tassel',(.37,.022,.014),None,rough=.84)
paper=material('Courtyard lantern mulberry paper',(.82,.69,.44),'paper',512,.87,seed=650)
lampglow=material('CourtyardPracticalGlow',(.96,.64,.26),None,rough=.65)
p=lampglow.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.65,.30,1);p.inputs['Emission Strength'].default_value=.9
terracotta=material('Courtyard bonsai stoneware',(.32,.255,.135),'stone',512,.65,seed=651)
water=material('Courtyard still rainwater',(.09,.155,.135),None,rough=.11,metal=.25)

def register(obj,mat,group):
    if mat: obj.data.materials.append(mat)
    obj.parent=root;groups[group].append(obj);return obj

def mesh(name,verts,faces,mat,group='CourtyardArchitecture',uv=None,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    layer=me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        poly.use_smooth=smooth
        for li in poly.loop_indices:
            vi=me.loops[li].vertex_index;co=me.vertices[vi].co
            layer.data[li].uv=uv[vi] if uv is not None else (co.x*.4,co.z*.4+co.y*.09)
    return register(ob,mat,group)

def cube(name,pos,size,mat,bevel=.012,group='CourtyardArchitecture',rot=0):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector((v.co.x*size[0],v.co.y*size[1],v.co.z*size[2]))
    if bevel: bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(size)*.25),segments=2,affect='EDGES',clamp_overlap=True)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();me.update()
    layer=me.uv_layers.new(name='UVMap');major=max(range(3),key=lambda i:size[i]);shift=random.random()*2
    for poly in me.polygons:
        normal=max(range(3),key=lambda i:abs(poly.normal[i]));axes=[i for i in range(3) if i!=normal]
        if mat in [wood,wood_dark,wood_edge,bark]:
            if major in axes: axes=[major,axes[1] if axes[0]==major else axes[0]]
            factors=[max(size[axes[0]],.01),max(size[axes[1]],.01)]
        elif mat in [plaster,plaster2]:factors=[4.8,4.8]
        else:factors=[max(size[axes[0]],.25),max(size[axes[1]],.25)]
        for li in poly.loop_indices:
            c=me.vertices[me.loops[li].vertex_index].co
            layer.data[li].uv=(c[axes[0]]/factors[0]+shift,c[axes[1]]/factors[1]+shift*.43)
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.location=pos;ob.rotation_euler.z=rot
    return register(ob,mat,group)

def tube(name,points,radii,mat,group='CourtyardArchitecture',seg=10,corrugate=False):
    vs=[];fs=[];uv=[];pts=[Vector(p) for p in points];dist=0
    if name.startswith(('Pine','Bonsai')) and len(pts)>2:
        source=pts;rr=list(radii) if isinstance(radii,(list,tuple)) else [radii]*len(source);dense=[];dr=[]
        for i in range(len(source)-1):
            p0=source[max(0,i-1)];p1=source[i];p2=source[i+1];p3=source[min(len(source)-1,i+2)]
            for j in range(6):
                t=j/6;dense.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t));dr.append(rr[i]*(1-t)+rr[i+1]*t)
        dense.append(source[-1]);dr.append(rr[-1]);pts=dense;radii=dr
    for k,p in enumerate(pts):
        tangent=(pts[min(k+1,len(pts)-1)]-pts[max(k-1,0)]).normalized()
        side=tangent.cross(Vector((0,0,1)))
        if side.length<.02:side=tangent.cross(Vector((0,1,0)))
        side.normalize();up=tangent.cross(side).normalized()
        r=radii[k] if isinstance(radii,(tuple,list)) else radii
        if k:dist+=(p-pts[k-1]).length
        for j in range(seg):
            a=j*math.tau/seg;rr=r*(1+(.085*math.sin(j*2.83+k*.42) if corrugate else 0))
            vs.append(tuple(p+rr*(side*math.cos(a)+up*math.sin(a))));uv.append((dist*.65,j/seg))
    for k in range(len(pts)-1):
        for j in range(seg):fs.append((k*seg+j,k*seg+(j+1)%seg,(k+1)*seg+(j+1)%seg,(k+1)*seg+j))
    fs.extend([tuple(range(seg-1,-1,-1)),tuple((len(pts)-1)*seg+j for j in range(seg))])
    return mesh(name,vs,fs,mat,group,uv,True)

def cylinder(name,pos,r,depth,mat,group='CourtyardArchitecture',seg=16,axis='Z',r2=None):
    direction=Vector((0,0,1)) if axis=='Z' else Vector((0,1,0)) if axis=='Y' else Vector((1,0,0))
    a=Vector(pos)-direction*depth*.5;b=Vector(pos)+direction*depth*.5
    return tube(name,[a,b],[r,r if r2 is None else r2],mat,group,seg)

def sphere(name,pos,radii,mat,group='CourtyardArchitecture',seg=16,rings=10,rough=0):
    vs=[];fs=[];uv=[]
    for j in range(rings+1):
        t=j/rings*math.pi
        for i in range(seg):
            a=i/seg*math.tau;rr=1+rough*math.sin(a*5+t*3)*math.sin(t)
            vs.append((pos[0]+radii[0]*math.sin(t)*math.cos(a)*rr,pos[1]+radii[1]*math.sin(t)*math.sin(a)*rr,pos[2]+radii[2]*math.cos(t)*rr));uv.append((i/seg,j/rings))
    for j in range(rings):
        for i in range(seg):q=j*seg+i;w=j*seg+(i+1)%seg;fs.append((q,w,w+seg,q+seg))
    return mesh(name,vs,fs,mat,group,uv,True)

def ring(name,pos,r,wire,mat,group='CourtyardArchitecture',axis='Y',seg=36):
    if axis=='Y':pts=[(pos[0]+r*math.cos(a),pos[1],pos[2]+r*math.sin(a)) for a in np.linspace(0,math.tau,seg+1)]
    elif axis=='Z':pts=[(pos[0]+r*math.cos(a),pos[1]+r*math.sin(a),pos[2]) for a in np.linspace(0,math.tau,seg+1)]
    else:pts=[(pos[0],pos[1]+r*math.cos(a),pos[2]+r*math.sin(a)) for a in np.linspace(0,math.tau,seg+1)]
    return tube(name,pts,wire,mat,group,8)

def rough_rock(name,pos,scale,mat=stone_dark,group='CourtyardFlora'):
    # Low strata break the silhouette; these are not round low-poly boulders.
    rng=random.Random(name);seg=13;rings=7;vs=[];fs=[];uv=[]
    offsets=[rng.uniform(-.22,.22) for i in range(seg)]
    for j in range(rings+1):
        t=j/rings*math.pi
        for i in range(seg):
            a=i/seg*math.tau;rr=1+offsets[i]*math.sin(t)+rng.uniform(-.035,.035)
            vs.append((pos[0]+scale[0]*math.sin(t)*math.cos(a)*rr,pos[1]+scale[1]*math.sin(t)*math.sin(a)*rr,pos[2]+scale[2]*math.cos(t)*rr));uv.append((i/seg,j/rings))
    for j in range(rings):
        for i in range(seg):q=j*seg+i;w=j*seg+(i+1)%seg;fs.append((q,w,w+seg,q+seg))
    ob=mesh(name,vs,fs,mat,group,uv,True);return ob

def roof(name,cx,cy,z,width,depth,group='CourtyardArchitecture',tile_scale=1):
    # Each overlapping curved clay tile has thickness and a shaped, hollow lip.
    columns=int(width/(.165*tile_scale));rows=int(depth/(.28*tile_scale));xs=np.linspace(cx-width/2,cx+width/2,columns+1)
    vs_by_mat=[([],[],[]) for _ in tiles]
    for row in range(rows):
        t=row/max(1,rows-1);yy=cy-depth/2+t*depth
        # Shallow curved roof pitch, with a gentle upward kick at the drip edge.
        zz=z+.42*t+.11*((1-t)**5);length=.36*tile_scale
        for col,x in enumerate(xs):
            target=vs_by_mat[(col+row*3)%len(tiles)];vs,fs,uv=target;base=len(vs);w=.10*tile_scale
            for end in [0,1]:
                y=yy+end*length;z0=zz+end*.042
                for k in range(7):
                    a=(k/6-.5)*math.pi;vs.append((x+w*math.sin(a),y,z0+.066*tile_scale*math.cos(a)));uv.append((k/6,end))
            for end in [0,1]:
                y=yy+end*length;z0=zz+end*.042-.016*tile_scale
                for k in range(7):
                    a=(k/6-.5)*math.pi;vs.append((x+w*math.sin(a),y,z0+.066*tile_scale*math.cos(a)));uv.append((k/6,end))
            for k in range(6):
                fs.extend([(base+k,base+k+1,base+8+k,base+7+k),(base+14+k,base+21+k,base+22+k,base+15+k),(base+k,base+14+k,base+15+k,base+k+1),(base+7+k,base+8+k,base+22+k,base+21+k)])
            fs.extend([(base,base+7,base+21,base+14),(base+6,base+20,base+27,base+13)])
    for i,(vs,fs,uv) in enumerate(vs_by_mat):mesh(name+' tile courses '+str(i),vs,fs,tiles[i],group,uv,True)
    # Solid timber fascia, exposed rafter tails, and terracotta drip scallops.
    cube(name+' lower fascia',(cx,cy-depth/2-.03,z+.085),(width+.14,.15,.18),wood_dark,.010,group)
    cube(name+' upper ridge fascia',(cx,cy+depth/2,z+.41),(width+.14,.17,.20),wood_dark,.010,group)
    for x in np.linspace(cx-width/2,cx+width/2,max(2,int(width/.30))):
        o=cube(name+' rafter tail',(x,cy-depth/2+.015,z-.015),(.08,.46,.12),wood,.008,group);o.rotation_euler.x=.13
    for x in np.linspace(cx-width/2,cx+width/2,columns+1):
        ring(name+' floral tile end',(x,cy-depth/2-.025,z+.135),.062*tile_scale,.012*tile_scale,random.choice(tiles),group,'Y',20)
        cylinder(name+' endtile center',(x,cy-depth/2-.030,z+.135),.018,.017,tiles[2],group,12,'Y')
    return

# Foundation, edge masonry and paving: the central stone path is genuinely jointed.
cube('Foundation',(0,2.15,-.20),(10.6,10.8,.38),stone_dark,.015)
cube('Courtyard floor soil',(0,2.20,-.015),(9.8,10.2,.085),earth,.012)
for side in [-1,1]:
    for j in range(12):cube('Garden low stone coping',(side*2.50,-2.25+j*.79,.11),(.38,.76,.28),stone,.018)
for j in range(15):
    yy=-2.73+j*.64
    widths=[.81,.88,.91,.82,.74] if j%2 else [.67,.92,.82,.87,.88]
    x=-2.2
    for i,w in enumerate(widths):
        if x+w>2.28:break
        ob=cube('Timeworn flagstone %02d %02d'%(j,i),(x+w/2,yy,.04+random.uniform(-.008,.009)),(w-.017,.625,.115),stone if (j+i)%3 else stone_dark,.024)
        ob.rotation_euler.z=random.uniform(-.006,.006);x+=w
        # Small irregular chips along selected paving corners.
        if (i+j)%8==0:rough_rock('Paving edge chip %d %d'%(j,i),(x-.03,yy-.295,.09),(.024,.022,.006),earth)
for j in range(15):
    for i in range(3):cube('Corridor flagstone',(3.8+i*.50,-2.4+j*.66,.025),(.487,.647,.10),stone,.018,group='CourtyardForeground')

# Three high pale courtyard walls; a real opening remains in the back facade.
cube('Rear wall left',(-3.02,6.65,2.68),(3.55,.38,5.35),plaster,.015)
cube('Rear wall right',(3.03,6.65,2.68),(3.54,.38,5.35),plaster,.015)
cube('Rear wall above stone portal',(0,6.65,4.48),(2.5,.38,1.75),plaster,.015)
cube('Left courtyard wall',(-4.76,2.13,2.85),(.38,9.55,5.70),plaster,.012)
cube('Right garden rear wall',(5.25,4.92,2.55),(.35,3.70,5.10),plaster2,.012)
for x in [-3.05,3.07]:
    cube('Rear stone damp base',(x,6.42,.29),(3.40,.055,.55),stone_dark,.012)
for j in range(6):cube('Left masonry wall foot',(-4.52,-2.1+j*1.42,.22),(.115,1.4,.40),stone_dark,.012)
# Real exposed brick repairs below the limewash, carefully grouped low down.
for cx,cy in [(-3.5,6.43),(3.15,6.43)]:
    for j in range(5):
        for i in range(7-j):
            cube('Limewash spalled brick repair',(cx+i*.19+(j%2)*.07,cy-.018,.30+j*.095),(.18,.045,.083),tiles[(j+i)%5],.007)
for k in range(7):
    cube('Rear wall stone string course',(0,6.405,3.73+k*.066),(2.56+.03*(k%2),.075,.045),stonepale if k%2 else stone,.006)
for cx in [-3.1,3.0]:
    cube('Small high ventilation recess',(cx,6.444,4.83),(.22,.028,.43),wood_dark,.005)
    for x in [cx-.08,cx,cx+.08]:cube('Vent vertical thin grille',(x,6.398,4.83),(.021,.022,.43),wood,.003)

# Stone entrance, worn staircase, timber threshold, and the shaded room beyond.
for i in range(3):cube('Doorway broad worn step',(0,5.63+i*.29,.085+i*.10),(2.55-i*.14,.53,.17+i*.02),stone,.024)
for x in [-1.15,1.15]:
    cube('Doorway stone jamb',(x,6.395,1.88),(.235,.30,2.95),stonepale,.035)
    cube('Doorway inner bevel',(x-math.copysign(.11,x),6.217,1.91),(.055,.035,2.71),stone,.009)
    for z in [.60,1.5,2.5]:cube('Portal masonry block seam',(x,6.211,z),(.233,.011,.008),stone_dark,.001)
cube('Carved stone lintel',(0,6.37,3.40),(2.65,.36,.25),stonepale,.036)
cube('Portal recessed shadow rail',(0,6.181,3.33),(2.44,.02,.055),stone_dark,.008)
cube('Carved stone lintel upper',(0,6.40,3.56),(2.83,.39,.075),stone,.012)
# Curved stone shoulders: geometry, not a drawn arch.
for side in [-1,1]:
    profile=[(side*.94,6.18,3.31),(side*1.00,6.18,3.25),(side*1.035,6.18,3.15),(side*1.05,6.18,3.02)]
    tube('Carved portal curved shoulder',profile,.053,stonepale,seg=12)
cube('Threshold old elm',(0,6.30,.37),(2.02,.235,.15),wood_dark,.020)
cube('Door inner room floor',(0,7.7,.31),(2.44,2.3,.15),wood_dark,.012)
for x in [-1.2,1.2]:cube('Inner timber passage side',(x,7.65,1.80),(.08,2.15,2.88),wood_dark,.003)
cube('Inner timber passage ceiling',(0,7.68,3.14),(2.4,2.12,.1),wood_dark,.003)
cube('Inner timber back wall',(0,8.76,1.8),(2.4,.10,2.94),wood_dark,.003)
for x in [-.72,.0,.72]:
    cube('Inner back door vertical stile',(x,8.65,1.80),(.07,.1,2.80),wood,.008)
    for z in [1.02,2.21]:cube('Inner back door panel',(x+.0,8.655,z),(.62,.075,1.06),wood,.006)
cube('Interior recessed shelf',(0,8.50,1.31),(1.9,.28,.065),wood_edge,.009)

def decorated_door(name,hinge,side,angle):
    # Each open leaf is transformed as a single small group after all ornaments
    # are built, keeping platework, hinge pins and lattice physically attached.
    before=len(groups['CourtyardArchitecture']);cx=hinge[0]+side*.47;cy=hinge[1]
    cube(name+' broad outer frame',(cx,cy,1.84),(.98,.12,2.87),wood,.018)
    for dx in [-.43,.43]:cube(name+' carved stile',(cx+dx,cy-.082,1.84),(.080,.060,2.76),wood_edge,.011)
    for z in [.49,1.22,2.18,3.18]:cube(name+' raised cross rail',(cx,cy-.087,z),(.89,.062,.092),wood_edge,.012)
    for z,h in [(.82,.58),(1.69,.85)]:
        cube(name+' inset weathered panel',(cx,cy-.068,z),(.70,.022,h),wood_dark,.014)
        for dx in [-.36,.36]:cube(name+' panel bevel stile',(cx+dx,cy-.101,z),(.022,.024,h+.05),wood_edge,.005)
        for zz in [z-h/2,z+h/2]:cube(name+' panel bevel rail',(cx,cy-.103,zz),(.73,.028,.028),wood_edge,.005)
    # Nine narrow bars each way form a real upper lattice, with dark air behind.
    cube(name+' dark lattice recess',(cx,cy-.069,2.68),(.72,.013,.91),wood_dark,.002)
    for x in np.linspace(cx-.34,cx+.34,10):cube(name+' upper lattice vertical',(x,cy-.105,2.68),(.013,.018,.87),wood_edge,.001)
    for z in np.linspace(2.26,3.09,13):cube(name+' upper lattice horizontal',(cx,cy-.12,z),(.69,.017,.012),wood_edge,.001)
    for z in np.linspace(.56,3.11,15):
        for x in [cx-.39,cx+.39]:
            sphere(name+' small iron stud',(x,cy-.128,z),(.020,.012,.020),iron,seg=10,rings=6)
    for zz in [.65,1.90,2.85]:
        cube(name+' iron strap hinge',(hinge[0]+side*.12,cy-.127,zz),(.27,.018,.032),iron,.005)
        cylinder(name+' hinge pin',(hinge[0],cy-.03,zz),.025,.13,iron,seg=12)
    cylinder(name+' knocker backplate',(cx-side*.25,cy-.142,1.76),.068,.023,iron,seg=24,axis='Y')
    sphere(name+' knocker mount',(cx-side*.25,cy-.16,1.80),(.029,.024,.029),bronze,seg=12,rings=8)
    ring(name+' iron ring knocker',(cx-side*.25,cy-.171,1.72),.065,.010,iron,seg=36)
    added=groups['CourtyardArchitecture'][before:];origin=Vector(hinge);rot=Matrix.Rotation(angle,4,'Z')
    bpy.context.view_layer.update()
    transform=Matrix.Translation(origin)@rot@Matrix.Translation(-origin)
    for o in added:o.matrix_world=transform@o.matrix_world
    return added

# The opened leaves frame a dark doorway, with no character meshes.
decorated_door('Door left',(-1.02,6.22,0),1,math.radians(69))
decorated_door('Door right',(1.02,6.22,0),-1,math.radians(-63))

# Rear door hood: bracketing and real stacked roof courses.
roof('Rear gate roof',0,6.17,3.72,3.37,1.12,tile_scale=1.05)
for x in [-1.43,1.43]:
    cube('Gate carved bracket shoulder',(x,6.16,3.47),(.14,.39,.18),wood,.014)
    tube('Gate bracket rolled profile',[(x,6.29,3.38),(x,6.15,3.40),(x,5.96,3.54),(x,5.91,3.68)],.065,wood_edge,seg=12)
    cube('Gate interlocking bracket pad',(x,6.00,3.67),(.30,.31,.11),wood,.010)
for x in np.linspace(-1.45,1.45,9):
    cube('Gate under-eave slatted ceiling',(x,6.14,3.735),(.13,1.04,.036),wood_dark,.004)

# Two recessed side windows with tiled eyebrows and exact wood lattice.
for yy,z in [(1.32,2.35),(4.36,2.55)]:
    # Exterior sill and inner shadow are discrete volumes so side views retain depth.
    cube('Left window plaster inset',(-4.535,yy,z),(.055,1.07,1.61),stone,.010)
    cube('Left window deep shadow',(-4.49,yy,z),(.065,.91,1.44),wood_dark,.005)
    for y in [yy-.47,yy+.47]:cube('Left window stone reveal',(-4.43,y,z),(.15,.085,1.64),stonepale,.015)
    for zz in [z-.80,z+.80]:cube('Left window stone lintel sill',(-4.42,yy,zz),(.22,1.13,.11),stonepale,.018)
    for y in np.linspace(yy-.40,yy+.40,7):cube('Left window lattice upright',(-4.40,y,z),(.040,.022,1.43),wood,.003)
    for zz in np.linspace(z-.67,z+.67,11):cube('Left window lattice crossbar',(-4.36,yy,zz),(.024,.85,.019),wood_edge,.002)
    # A miniature tiled eyebrow rotated to sit on the side wall.
    start={g:len(groups[g]) for g in groups};roof('Window hood',0,0,z+.84,1.28,.59,tile_scale=.78)
    rot=Matrix.Rotation(math.pi/2,3,'Z');offset=Vector((-4.57,yy,0))
    for g in groups:
        for o in groups[g][start[g]:]:
            if o.location.length>1e-8:o.location=offset+rot@o.location;o.rotation_euler.z+=math.pi/2
            else:
                for v in o.data.vertices:v.co=offset+rot@v.co

# The right-hand dark timber corridor is a usable foreground, not a flat frame.
for yy in [-1.6,1.0,3.65,6.26]:
    for xx in [3.22,5.22]:
        cylinder('Timber corridor octagonal post',(xx,yy,1.8),.115,3.5,wood_dark,'CourtyardForeground',12)
        cube('Timber column stone foot',(xx,yy,.18),(.39,.39,.30),stone,.025,'CourtyardForeground')
        cube('Timber column top bracket',(xx,yy,3.37),(.27,.48,.17),wood,.012,'CourtyardForeground')
        tube('Corridor curved bracket',[(xx,yy,3.10),(xx,yy-.08,3.25),(xx,yy-.25,3.36),(xx,yy-.44,3.37)],.060,wood_dark,'CourtyardForeground',12)
for xx in [3.24,5.22]:
    cube('Corridor long frieze',(xx,2.32,3.49),(.20,8.52,.23),wood_dark,.009,'CourtyardForeground')
    cube('Corridor raised moulding',(xx-.04,2.32,3.39),(.22,8.62,.043),wood_edge,.007,'CourtyardForeground')
for yy in np.linspace(-1.77,6.46,25):cube('Corridor exposed ceiling rafters',(4.22,yy,3.59),(2.28,.09,.115),wood,.010,'CourtyardForeground')
# Corridor canopy is double slopes; repeated curved tiles seen from high cameras.
roofstart=len(groups['CourtyardForeground'])
roof('Right corridor roof',0,0,3.62,8.50,2.50,'CourtyardForeground',tile_scale=1.2)
bpy.context.view_layer.update()
rooftransform=Matrix.Translation((4.22,2.2,0))@Matrix.Rotation(-math.pi/2,4,'Z')
for o in groups['CourtyardForeground'][roofstart:]:o.matrix_world=rooftransform@o.matrix_world
for yy in [-.37,2.2,4.80]:
    cube('Corridor low rail',(5.04,yy,0.81),(.07,2.42,.084),wood,.006,'CourtyardForeground')
    cube('Corridor bottom rail',(5.04,yy,.26),(.073,2.42,.067),wood,.006,'CourtyardForeground')
    for y in np.linspace(yy-1.12,yy+1.12,15):cube('Corridor balustrade',(5.04,y,.535),(.043,.035,.51),wood_dark,.004,'CourtyardForeground')
# Near right lattice window: real intersecting fretwork gives spatial occlusion.
cube('Near corridor lattice frame',(5.19,-.10,2.07),(.12,2.43,2.04),wood_dark,.010,'CourtyardForeground')
# Cut the frame interior visually with inset lattice against open air, rather
# than an opaque black card. Four frame edges and a sparse spiral key pattern.
frame=groups['CourtyardForeground'].pop();bpy.data.objects.remove(frame,do_unlink=True)
for y in [-1.31,1.11]:cube('Near lattice outer vertical',(5.19,y,2.07),(.13,.11,2.08),wood_dark,.010,'CourtyardForeground')
for z in [1.04,3.10]:cube('Near lattice outer rail',(5.19,-.10,z),(.13,2.52,.12),wood_dark,.010,'CourtyardForeground')
for y in np.linspace(-1.25,1.05,8):cube('Near lattice thin upright',(5.19,y,2.07),(.059,.035,1.97),wood,.003,'CourtyardForeground')
for z in np.linspace(1.10,3.04,7):cube('Near lattice thin cross rail',(5.19,-.10,z),(.052,2.32,.035),wood,.003,'CourtyardForeground')
for j in range(3):
    for k in range(4):
        y=-1.14+k*.56;z=1.18+j*.61
        for dy,dz,w,h in [(.11,.20,.035,.38),(.26,.38,.31,.035),(.41,.27,.035,.25),(.33,.16,.19,.035)]:
            cube('Near lattice return fret',(5.16,y+dy,z+dz),(.034,w,h),wood_edge,.002,'CourtyardForeground')

def lantern(name,x,y,z,scale=1):
    group='CourtyardPracticals';w=.36*scale;d=.36*scale;h=.53*scale
    # Paper panes, wood corner mitres, suspension, low flared roof and tassels.
    for yy in [y-d/2,y+d/2]:cube(name+' illuminated paper pane',(x,yy,z),(w,.009,h),lampglow,.001,group)
    for xx in [x-w/2,x+w/2]:cube(name+' side paper pane',(xx,y,z),(.009,d,h),paper,.001,group)
    for xx in [x-w/2,x+w/2]:
        for yy in [y-d/2,y+d/2]:cube(name+' wood mitred corner',(xx,yy,z),(.037,.037,h+.10),wood_dark,.005,group)
    for zz in [z-h/2-.03,z+h/2+.03]:
        cube(name+' square timber cap',(x,y,zz),(w+.12,d+.12,.065),wood_dark,.006,group)
        cube(name+' rolled cap moulding',(x,y,zz+.038),(w+.15,d+.15,.022),wood_edge,.004,group)
    # Central slatted top, cap bosses, and slender red silk fringe.
    tube(name+' hanging chain',[(x,y,z+h/2+.13),(x,y,z+h/2+.38)],.009,iron,group,8)
    ring(name+' suspension loop',(x,y,z+h/2+.37),.028,.006,iron,group,'Y',20)
    for cx in [x-w*.44,x+w*.44]:
        tube(name+' red tassel cord',[(cx,y,z-h/2-.06),(cx,y,z-h/2-.16)],.006,red,group,6)
        sphere(name+' knotted tassel crown',(cx,y,z-h/2-.16),(.025,.025,.033),red,group,12,8)
        for j in range(18):
            a=j*math.tau/18;r=.018
            tube(name+' fine silk tassel thread',[(cx+r*math.cos(a),y+r*math.sin(a),z-h/2-.18),(cx+r*.85*math.cos(a),y+r*.85*math.sin(a),z-h/2-.43)],.0023,red,group,4)
    return [x,z,-y]

practicals=[lantern('Lantern near',3.91,-.24,2.98,1.02),lantern('Lantern inner',4.04,3.78,2.97,.90)]
# Paired teacups on the empty corridor table suggest occupants without avatars.
cube('Corridor elm writing table',(4.15,2.35,.82),(1.15,.66,.095),wood,.024,'CourtyardForeground')
for xx in [3.68,4.62]:
    for yy in [2.09,2.61]:cube('Writing table slender foot',(xx,yy,.44),(.085,.085,.75),wood_dark,.012,'CourtyardForeground')
for xx in [3.9,4.42]:
    cylinder('Handmade tea saucer',(xx,2.32,.881),.083,.018,terracotta,'CourtyardForeground',32)
    cylinder('Small ceramic tea bowl',(xx,2.32,.917),.053,.070,terracotta,'CourtyardForeground',24,r2=.061)
    cylinder('Dark tea surface',(xx,2.32,.952),.047,.001,water,'CourtyardForeground',24)
    ring('Tea bowl fine rim',(xx,2.32,.954),.059,.0035,terracotta,'CourtyardForeground','Z',28)
cube('Writing table closed cotton folio',(4.20,2.47,.886),(.30,.21,.018),paper,.005,'CourtyardForeground',rot=.07)
cube('Folio narrow red ribbon',(4.20,2.47,.897),(.025,.22,.003),red,.001,'CourtyardForeground',rot=.07)

def moss_patch(name,cx,cy,r1,r2,z=.054,group='CourtyardFlora'):
    vs=[(cx,cy,z+.002)];uv=[(.5,.5)];fs=[];N=18
    for i in range(N):
        a=i/N*math.tau;rad=1+random.uniform(-.22,.22)
        vs.append((cx+math.cos(a)*r1*rad,cy+math.sin(a)*r2*rad,z+random.uniform(-.002,.002)));uv.append((.5+.5*math.cos(a),.5+.5*math.sin(a)))
    for i in range(N):fs.append((0,i+1,(i+1)%N+1))
    return mesh(name,vs,fs,moss,group,uv)

for side in [-1,1]:
    for j in range(25):
        x=side*random.uniform(2.72,4.25);y=random.uniform(-1.8,5.65)
        moss_patch('Garden irregular moss carpet',x,y,random.uniform(.18,.54),random.uniform(.16,.47),.047)
for j in range(23):
    moss_patch('Flagstone crevice moss',random.choice([-2.2,-1.38,-.5,.37,1.20]),random.uniform(-2.4,5.4),random.uniform(.03,.09),random.uniform(.05,.13),.098)

def fern(name,pos,size=1):
    # Each arched frond has individual tapering pinnate blades and a slender rachis.
    collected=[([],[],[]) for _ in fern_mats]
    base=Vector(pos)
    for f in range(9):
        angle=f*2.399;direction=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-math.sin(angle),math.cos(angle),0))
        length=size*(.36+random.random()*.20);points=[]
        for j in range(13):
            t=j/12;center=base+direction*(length*t*.78)+Vector((0,0,length*(.86*t-.44*t*t)));points.append(tuple(center))
        tube(name+' arched fern rachis',points,.0032*size,fern_mats[2],'CourtyardFlora',5)
        for j in range(1,12):
            t=j/12;c=Vector(points[j]);w=length*.21*math.sin(t*math.pi)**.8*(1-.34*t)
            for s in [-1,1]:
                tip=c+side*(w*s)+direction*(.036*size)+Vector((0,0,.020*size))
                vs,fs,uv=collected[(j+f)%4];b=len(vs);fl=.012*size*(1-.5*t)
                vs.extend([tuple(c),tuple(c+direction*fl+side*w*s*.52+Vector((0,0,.011*size))),tuple(tip),tuple(c-direction*fl+side*w*s*.50)]);uv.extend([(0,0),(.45,1),(1,.5),(.45,0)]);fs.extend([(b,b+1,b+2),(b,b+2,b+3)])
    for i,(vs,fs,uv) in enumerate(collected):mesh(name+' pinnate leaflets '+str(i),vs,fs,fern_mats[i],'CourtyardFlora',uv)

for i,(x,y,s) in enumerate([(-3.65,-1.0,.8),(-3.15,.1,.8),(-3.80,1.1,1.15),(-2.9,3.5,.9),(-3.25,5.4,.8),(2.99,5.39,1.10),(3.07,4.3,.7),(2.92,.58,.65),(-.95,5.55,.5),(1.25,5.4,.65)]):fern('Courtyard fern '+str(i),(x,y,.08),s)

def leafy_shrub(name,pos,scale=1):
    vs_by=[([],[],[]) for _ in fern_mats];base=Vector(pos)
    for j in range(29):
        a=j*2.399;tip=base+Vector((math.cos(a)*random.uniform(.11,.25)*scale,math.sin(a)*random.uniform(.11,.25)*scale,random.uniform(.22,.48)*scale))
        tube(name+' slender twig',[base,tip],.004,wood_dark,'CourtyardFlora',5)
        axis=(tip-base).normalized();side=axis.cross(Vector((0,0,1))).normalized()
        for q in range(3):
            c=base+(tip-base)*(.37+.22*q)
            for s in [-1,1]:
                length=.085*scale;pt=c+side*length*s+axis*.033*scale
                v,fs,uv=vs_by[(q+j)%4];b=len(v);mid=(c+pt)/2;w=.019*scale
                v.extend([tuple(c),tuple(mid+Vector((0,0,w))),tuple(pt),tuple(mid-Vector((0,0,w*.5)))]);fs.extend([(b,b+1,b+2),(b,b+2,b+3)]);uv.extend([(0,0),(.5,1),(1,0),(.5,0)])
    for i,(vs,fs,uv) in enumerate(vs_by):mesh(name+' fine leaves '+str(i),vs,fs,fern_mats[i],'CourtyardFlora',uv)

for i,(x,y,s) in enumerate([(-3.5,4.7,1.35),(-4.01,2.8,.8),(-3.6,-.35,1.4),(2.94,3.6,.65),(-2.8,5.0,.9)]):leafy_shrub('Small garden shrub '+str(i),(x,y,.08),s)

# Distinctively tilted, asymmetrical Chinese pine with articulated branches.
needle_batches=[([],[],[]) for _ in leaves]
tuft_count=0
def needle_tuft(center,direction,size=.19,seed=0):
    global tuft_count
    rng=random.Random(seed+712);c=Vector(center);direction=Vector(direction).normalized();side=direction.cross(Vector((0,0,1)))
    if side.length<.1:side=direction.cross(Vector((0,1,0)))
    side.normalize();up=side.cross(direction).normalized();tuft_count+=1
    # Needles are three-dimensional triangular slivers; no leaf photographs.
    for k in range(30):
        a=k*2.399+rng.uniform(-.1,.1);lean=rng.uniform(.28,1.5)
        ray=(direction*.70+side*math.cos(a)*lean+up*math.sin(a)*lean).normalized()
        length=size*rng.uniform(.62,1.20);start=c+direction*rng.uniform(-.01,.018);tip=start+ray*length
        width=.0028*size/.19;perp=ray.cross(direction)
        if perp.length<.1:perp=ray.cross(side)
        perp.normalize();mid=start+ray*length*.48
        vs,fs,uv=needle_batches[(k+seed)%len(leaves)];b=len(vs)
        vs.extend([tuple(start),tuple(mid+perp*width),tuple(tip),tuple(mid-perp*width),tuple(mid+ray.cross(perp)*width*.7)])
        fs.extend([(b,b+1,b+2),(b,b+2,b+3),(b,b+4,b+2)]);uv.extend([(0,0),(.5,1),(1,0),(.5,0),(.5,.5)])

trunk=[(-2.57,3.43,.14),(-2.51,3.46,.60),(-2.32,3.47,1.18),(-2.05,3.49,1.88),(-1.72,3.47,2.48),(-1.44,3.52,3.08),(-1.18,3.60,3.61),(-.99,3.72,4.00)]
tube('Pine leaning ridged trunk',trunk,[.215,.192,.169,.147,.119,.094,.063,.025],bark,'CourtyardFlora',22,True)
for i in range(7):
    a=i*math.tau/7;tube('Pine exposed spreading root',[trunk[0],(-2.57+.23*math.cos(a),3.43+.23*math.sin(a),.09),(-2.57+.53*math.cos(a),3.43+.47*math.sin(a),.045)],[.053,.037,.009],bark,'CourtyardFlora',9,True)
branch_specs=[
    (2,(-3.9,3.15,2.15),(-4.24,3.10,2.44)),
    (3,(-3.16,2.48,2.71),(-3.56,2.40,2.92)),
    (4,(-.49,2.50,2.79),(.21,2.38,2.99)),
    (4,(-2.79,4.32,3.14),(-3.3,4.61,3.24)),
    (5,(-.15,3.91,3.50),(.54,4.04,3.59)),
    (5,(-2.65,3.60,3.52),(-3.0,3.58,3.82)),
    (6,(-.55,2.8,3.90),(-.14,2.45,4.09)),
    (7,(-.94,4.23,4.14),(-1.1,4.76,4.32)),
]
for bi,(ti,end,tip) in enumerate(branch_specs):
    start=Vector(trunk[ti]);end=Vector(end);tip=Vector(tip)
    mid=start*.60+end*.40+Vector((0,0,-.20))
    tube('Pine articulated bough '+str(bi),[start,mid,end,tip],[.055 if ti<5 else .040,.041,.022,.007],bark,'CourtyardFlora',12,True)
    direction=(tip-end).normalized()
    for j in range(18):
        t=.20+j*.044;point=mid.lerp(tip,min(t,1));side=Vector((-direction.y,direction.x,0));s=1 if j%2 else -1
        twig_tip=point+side*s*random.uniform(.19,.40)+direction*.12+Vector((0,0,random.uniform(.02,.13)))
        tube('Pine fine side twig',[point,twig_tip],[.011,.0035],bark,'CourtyardFlora',7,True)
        for q in range(5):
            c=point.lerp(twig_tip,.40+q*.14)
            needle_tuft(c,(twig_tip-point)+Vector((0,0,.12)),.23 if ti<5 else .21,bi*100+j*5+q)
        needle_tuft(twig_tip,(twig_tip-point)+Vector((0,0,.12)),.21,bi*1000+j)
for q in range(10):needle_tuft(Vector(trunk[-1])+Vector((random.uniform(-.15,.15),random.uniform(-.12,.12),random.uniform(-.02,.17))),(random.uniform(-1,1),random.uniform(-1,1),1),.20,900+q)
for i,(vs,fs,uv) in enumerate(needle_batches):mesh('Pine fine needle clusters '+str(i),vs,fs,leaves[i],'CourtyardFlora',uv,False)

# Courtyard stone display pedestals, relief sculpture and sculpted bonsai.
def pedestal(name,x,y,h=.66):
    cube(name+' square base',(x,y,.16),(.63,.57,.22),stone,.018)
    cube(name+' fluted lower plinth',(x,y,.29),(.52,.48,.07),stonepale,.012)
    cube(name+' square slender pillar',(x,y,h*.60),(.24,.24,h*.65),stone_dark,.012)
    for dx in [-.126,.126]:cube(name+' pillar fine raised flute',(x+dx,y,h*.59),(.02,.215,h*.50),stone,.005)
    cube(name+' moulded shoulder',(x,y,h-.03),(.40,.35,.10),stonepale,.018)
    cube(name+' flat top slab',(x,y,h+.05),(.66,.56,.085),stone,.018)
pedestal('Left carved stone display',-3.72,5.02,.91)
relief=rough_rock('Carved resting guardian relief',(-3.72,5.05,1.34),(.42,.19,.44),stone_dark,'CourtyardArchitecture')
for a in np.linspace(-.5,3.3,6):
    tube('Stone relief scrolling cloud',[(-3.72+.27*math.cos(a),4.842,1.37+.24*math.sin(a)),(-3.72+.21*math.cos(a+.3),4.823,1.37+.18*math.sin(a+.3)),(-3.72+.12*math.cos(a+.6),4.818,1.37+.12*math.sin(a+.6))],.019,stone,'CourtyardArchitecture',8)
pedestal('Near bonsai stone stand',-3.61,-.76,.59)
cylinder('Bonsai oval stoneware basin',(-3.61,-.76,.765),.24,.23,terracotta,seg=40,r2=.32)
ring('Bonsai ceramic rolled rim',(-3.61,-.76,.88),.314,.019,terracotta,'CourtyardArchitecture','Z',44)
cylinder('Bonsai dark soil',(-3.61,-.76,.882),.298,.005,earth,seg=40)
smalltrunk=[(-3.61,-.76,.88),(-3.65,-.76,1.11),(-3.49,-.75,1.27),(-3.38,-.73,1.37)]
tube('Bonsai twisted trunk',smalltrunk,[.028,.021,.014,.004],bark,'CourtyardFlora',12,True)
small_needles_start=[(len(v),len(f),len(uv)) for v,f,uv in needle_batches]
for j in range(18):
    a=j*2.399;c=Vector((-3.50,-.75,1.31))+Vector((.22*math.cos(a)*math.sin(j/18*math.pi),.15*math.sin(a),.10*math.cos(j/18*math.pi)))
    tube('Bonsai fine branch',[smalltrunk[2],c],[.006,.0016],bark,'CourtyardFlora',6)
    needle_tuft(c,(math.cos(a),math.sin(a),.9),.090,5000+j)
# Only newly added needle data becomes the miniature bonsai foliage.
for i,(vs,fs,uv) in enumerate(needle_batches):
    sv,sf,suv=small_needles_start[i]
    mesh('Bonsai fine needle clusters '+str(i),vs[sv:],[tuple(v-sv for v in f) for f in fs[sf:]],leaves[i],'CourtyardFlora',uv[suv:],False)

for i,(x,y,scale) in enumerate([(-3.35,2.18,(.33,.40,.43)),(2.86,4.98,(.31,.24,.60)),(-4.01,.45,(.33,.25,.63)),(-2.94,4.14,(.46,.36,.22)),(2.90,-.76,(.32,.33,.27))]):
    rough_rock('Garden worn scholar rock '+str(i),(x,y,scale[2]*.80),scale)
    moss_patch('Rock base moss '+str(i),x,y,scale[0]*1.12,scale[1]*1.1,.072)
    for j in range(6):
        a=random.uniform(0,math.tau);moss_patch('Rock small moss ledge',x+scale[0]*.4*math.cos(a),y+scale[1]*.5*math.sin(a),.047,.035,scale[2]*1.3)

# Rain cistern / tiny drainage rill: a quiet sound source with a real water surface.
cube('Stone rainwater basin',(2.92,5.80,.37),(.71,.50,.60),stone,.06)
cube('Basin recessed water shadow',(2.92,5.80,.68),(.53,.35,.012),wood_dark,.018)
cube('Basin still rainwater',(2.92,5.80,.688),(.49,.315,.003),water,.015)
for side in [-1,1]:cube('Basin thick lip',(2.92+side*.315,5.8,.685),(.077,.50,.072),stonepale,.013)
for y in [5.59,6.01]:cube('Basin end lip',(2.92,y,.685),(.66,.08,.072),stonepale,.013)
tube('Old bamboo drip spout',[(3.2,6.10,.92),(3.0,5.92,.90),(2.89,5.80,.85)],.022,wood_edge,seg=12)

# Distant geometry, separately revealed when the film opens the set.
cube('Beyond courtyard rear garden wall',(0,11.18,3.05),(14,.34,6.10),plaster2,.02,'CourtyardEnvironment')
for xx in [-5.72,5.69]:cube('Beyond courtyard tall neighboring wall',(xx,7.88,3.65),(.35,7.1,7.3),plaster2,.015,'CourtyardEnvironment')
roof('Neighboring rear grey roof',0,10.20,5.13,12.15,2.11,'CourtyardEnvironment',tile_scale=1.3)
for j in range(8):
    rough_rock('Beyond courtyard foliage crown '+str(j),(random.uniform(-5,5),9.30,random.uniform(4.8,5.9)),(random.uniform(.3,.6),.36,.27),fern_mats[j%4],'CourtyardEnvironment')

# Named empties survive glTF as accurate shot and interaction anchors.
anchors={
 'CourtyardWideAnchor':(0,2.4,10.8),
 'CourtyardDoorAnchor':(.5,1.7,4.8),
 'CourtyardCorridorAnchor':(3.8,1.65,2),
 'CourtyardPineAnchor':(-3.7,1.5,2.8),
 'CourtyardLanternAnchor':(2.4,2.7,1.5),
 'CourtyardThresholdAnchor':(0,1.65,-5.05),
 'CourtyardBookAnchor':(4.20,.93,-2.47),
 'CourtyardClapperAnchor':(.2,.27,2.2),
}
for name,(x,y,z) in anchors.items():
    ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob);ob.parent=root;ob.location=(x,-z,y)

# Studio proof lighting exists only in the editable .blend. Runtime adds its own
# lamps at the metadata positions and moves an authored camera through the set.
def light(name,pos,energy,color,size=4,type='AREA'):
    d=bpy.data.lights.new(name,type);d.energy=energy;d.color=color
    if type=='AREA':d.shape='DISK';d.size=size
    ob=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(ob);ob.location=pos
    if type=='AREA':ob.rotation_euler=(Vector((0,3,1.8))-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
light('Soft afternoon roof opening',(-1,2.0,8.4),1650,(1,.94,.82),6.0)
light('Open courtyard bounce',(0,-3.5,4.3),540,(.81,.89,1),5)
light('Near lantern practical',(3.91,-.24,2.98),24,(1,.62,.28),type='POINT')
light('Inner lantern practical',(4.04,3.78,2.97),19,(1,.64,.31),type='POINT')
world=bpy.data.worlds.new('Courtyard overcast sky');world.use_nodes=True;world.node_tree.nodes.clear();wb=world.node_tree.nodes.new('ShaderNodeBackground');wo=world.node_tree.nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(wb.outputs[0],wo.inputs['Surface']);wb.inputs[0].default_value=(.56,.63,.67,1);wb.inputs[1].default_value=.45;bpy.context.scene.world=world
camdata=bpy.data.cameras.new('Courtyard proof camera');cam=bpy.data.objects.new('Courtyard proof camera',camdata);bpy.context.collection.objects.link(cam)
cam.location=(.5,-4.8,1.75);target=Vector((0,6.25,1.9));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=33
bpy.context.scene.camera=cam;bpy.context.scene.render.engine='BLENDER_EEVEE';bpy.context.scene.render.resolution_x=1400;bpy.context.scene.render.resolution_y=820;bpy.context.scene.render.resolution_percentage=100
bpy.context.scene.render.image_settings.file_format='JPEG';bpy.context.scene.render.image_settings.quality=92
bpy.context.scene.view_settings.view_transform='AgX';bpy.context.scene.view_settings.look='AgX - Medium High Contrast'
scene=bpy.context.scene
try:scene.eevee.taa_render_samples=64
except:pass
scene.render.filepath=str(OUT/'chinese-courtyard-proof.jpg')
print('COURTYARD GEOMETRY CREATED',sum(len(v) for v in groups.values()),'objects',tuft_count,'needle tufts',flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'chinese-courtyard-detailed.blend'))
# Render before merging to preserve editability and validate light and proportions.
bpy.ops.render.render(write_still=True)

def merge_group(objects,name):
    # Build a material-isolated mesh directly; no Blender operator quadratics.
    bymat={}
    for ob in objects:
        if ob.type!='MESH':continue
        mat=ob.data.materials[0] if ob.data.materials else None;bymat.setdefault(mat,[]).append(ob)
    parent=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(parent);parent.parent=root
    for mi,(mat,obs) in enumerate(bymat.items()):
        vertices=[];faces=[];uvs=[];smooth=[]
        for ob in obs:
            me=ob.data;transform=ob.matrix_world;base=len(vertices)
            vertices.extend([tuple(transform@v.co) for v in me.vertices])
            sourceuv=me.uv_layers.active
            for p in me.polygons:
                faces.append(tuple(base+v for v in p.vertices));smooth.append(p.use_smooth)
                uvs.extend([tuple(sourceuv.data[li].uv) for li in p.loop_indices])
        data=bpy.data.meshes.new(name+' '+mat.name);data.from_pydata(vertices,[],faces);data.update();uv=data.uv_layers.new(name='UVMap')
        for k,p in enumerate(data.polygons):p.use_smooth=smooth[k]
        for i,val in enumerate(uvs):uv.data[i].uv=val
        ob=bpy.data.objects.new(name+'_'+str(mi).zfill(2)+'_'+mat.name,data);bpy.context.collection.objects.link(ob);data.materials.append(mat);ob.parent=parent
    for ob in objects:bpy.data.objects.remove(ob,do_unlink=True)
    return parent

bpy.context.view_layer.update()
for group,objects in groups.items():merge_group(objects,group)
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.data.objects:
    if ob==root or ob.parent is not None:ob.select_set(True)
bpy.context.view_layer.objects.active=root
path=ASSETS/'chinese-courtyard.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_texcoords=True,export_normals=True,export_cameras=False,export_lights=False,export_extras=True)
sys.path.insert(0,str(Path(__file__).resolve().parent));from compact_courtyard_glb import compact;compact(path)
stats={'meshCount':sum(o.type=='MESH' for o in bpy.data.objects),'triangles':sum(sum(max(0,len(p.vertices)-2) for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'glbBytes':path.stat().st_size,'needleTufts':tuft_count,'materials':len(material_stats)}
info={
 'source':'Original Blender geometry; architectural reference: supplied IMG_8369.PNG / IMG_8370.PNG / IMG_8371.PNG / IMG_8402.PNG',
 'title':'庭院 · 松影慢行','coordinateSystem':'Three.js Y-up; Blender X=X, Y=-Z, Z=Y',
 'bounds':{'min':[-6,-.4,-12.2],'max':[6,7.5,3.5]},
 'sceneBounds':{'min':[-4.9,0,-7.1],'max':[5.4,5.7,3.0]},
 'practicalPositions':practicals,
 'environmentNames':['CourtyardEnvironment'],
 'foregroundNames':['CourtyardForeground'],
 'features':['Mottled lime plaster PBR textures','Individually modeled curved overlapping roof tiles','Wooden doors with real lattice and iron ring knockers','Asymmetrical articulated pine with modeled needles','Dark timber corridor with paper lanterns and fine red tassels','Stone flagstone joints, steps, ferns and moss gardens','Empty tea table with two cups and physical folio'],
 'anchors':{name:list(pos) for name,pos in anchors.items()},
 'recommendedShots':[
  {'id':'wide','position':[0,2.4,10.8],'target':[0,2,-3],'fov':42},
  {'id':'door','position':[.5,1.7,4.8],'target':[0,1.8,-6.3],'fov':42},
  {'id':'corridor','position':[3.8,1.65,2],'target':[-.6,1.7,-4.4],'fov':48},
  {'id':'pine','position':[-3.7,1.5,2.8],'target':[-1.4,2.5,-3.6],'fov':42},
  {'id':'lantern','position':[2.4,2.7,1.5],'target':[3.6,3.0,.24],'fov':44},
  {'id':'threshold','position':[0,1.65,-5.05],'target':[.7,1.8,1.5],'fov':50},
 ],
 'stats':stats,'editableSource':str(OUT/'chinese-courtyard-detailed.blend')}
(ASSETS/'chinese-courtyard-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
print('COURTYARD EXPORT COMPLETE',json.dumps(stats),flush=True)
