"""Validate the performer-free exports and add prop anchors without touching geometry."""
import json,struct,re,shutil,sys
from pathlib import Path
SITE=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve();ASSETS=SITE/'dist/assets'
for stem,infostem in [('interior-room','interior-model-info'),('vintage-diner','vintage-diner-info')]:
 path=ASSETS/(stem+'.glb');b=path.read_bytes();assert struct.unpack_from('<III',b)==(0x46546c67,2,len(b))
 n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);assert not any(re.search(r'Actor|Performer|ManBody|WomanBody',node.get('name','')) for node in g.get('nodes',[]))
 for m in g.get('materials',[]):
  if 'Window glass' in m.get('name',''):
   m['alphaMode']='BLEND';m['doubleSided']=True;m['pbrMetallicRoughness']['baseColorFactor']=[.42,.48,.34,.065]
 info=json.loads((ASSETS/(infostem+'.json')).read_text())
 if stem=='interior-room':
  anchors={'detail':[-.12,.99,-1.27],'tea':[0,1.13,-1.995],'throw':[1.45,.95,-1.3]}
  nodes={node.get('name'):node for node in g['nodes']}
  for key,pos in anchors.items():
   name='Anchor_'+key
   if name in nodes:node=nodes[name];node.pop('matrix',None);node['translation']=pos
   else:
    node={'name':name,'translation':pos,'extras':{'category':key}};idx=len(g['nodes']);g['nodes'].append(node);g['scenes'][g.get('scene',0)]['nodes'].append(idx)
   info['anchors_gltf_y_up'][key]=pos
  info['frames_gltf_y_up']['detail']['target']=anchors['detail'];info['frames_gltf_y_up']['detail']['scale']='书页特写'
  for key in ['man','woman']:
   if key in info['frames_gltf_y_up']:info['frames_gltf_y_up'][key]['scale']='窗边空座近景'
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);tail=b[20+n:];path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail)
 info['glb_bytes']=path.stat().st_size;(ASSETS/(infostem+'.json')).write_text(json.dumps(info,ensure_ascii=False,indent=2));shutil.copy2(path,OUT/(stem+'.glb'))
 gbytes=path.read_bytes();sz=struct.unpack_from('<I',gbytes,12)[0];binary_len,binary_type=struct.unpack_from('<II',gbytes,20+sz);assert binary_type==0x004e4942;assert g['buffers'][0]['byteLength']<=binary_len
 print(stem,{'actors':0,'meshes':len(g['meshes']),'bytes':len(gbytes),'details':info.get('added_detail_parts'),'triangles':info['triangles'],'atlas':info['atlas']})
