"""Loss-controlled geometry encoding supported by GLTFLoader without a decoder.

Positions retain 1/4096 scene-unit precision. Normals use normalized signed bytes.
Repeating world-projected UVs use normalized shorts and KHR_texture_transform.
"""
import json, struct
from pathlib import Path

def compact(path):
 path=Path(path);raw=path.read_bytes();jsonsize=struct.unpack_from('<I',raw,12)[0]
 doc=json.loads(raw[20:20+jsonsize]);binlen=struct.unpack_from('<I',raw,20+jsonsize)[0];oldbin=raw[28+jsonsize:28+jsonsize+binlen]
 if 'KHR_mesh_quantization' in doc.get('extensionsRequired',[]):return
 ids={key:{p['attributes'][key] for mesh in doc['meshes'] for p in mesh['primitives'] if key in p['attributes']} for key in ['POSITION','NORMAL','TEXCOORD_0']}
 replacements={};precision=4096;uvrange=32
 for key,items in ids.items():
  for ai in sorted(items):
   ac=doc['accessors'][ai];vi=ac['bufferView'];view=doc['bufferViews'][vi]
   assert ac['componentType']==5126
   assert all(a.get('bufferView')!=vi or a is ac for a in doc['accessors'])
   count=2 if key=='TEXCOORD_0' else 3;stride=view.get('byteStride',count*4);start=view.get('byteOffset',0)+ac.get('byteOffset',0);encoded=bytearray();values=[]
   for i in range(ac['count']):
    value=struct.unpack_from('<%df'%count,oldbin,start+i*stride)
    if key=='POSITION':
     q=[round(v*precision) for v in value];assert max(q)<32768 and min(q)>=-32768;encoded.extend(struct.pack('<4h',*q,0));values.append(q)
    elif key=='NORMAL':encoded.extend(struct.pack('<4b',*[max(-127,min(127,round(v*127))) for v in value],0))
    else:
     assert max(value)<=uvrange and min(value)>=-uvrange,value
     encoded.extend(struct.pack('<2h',*[max(-32767,min(32767,round(v/uvrange*32767))) for v in value]))
   replacements[vi]=bytes(encoded);view['byteStride']=8 if key=='POSITION' else 4;ac['byteOffset']=0;ac['componentType']=5120 if key=='NORMAL' else 5122
   if key=='POSITION':
    ac.pop('normalized',None);ac['min']=[min(v[i] for v in values) for i in range(3)];ac['max']=[max(v[i] for v in values) for i in range(3)]
   else:ac['normalized']=True;ac.pop('min',None);ac.pop('max',None)
 for node in doc['nodes']:
  if 'mesh' not in node:continue
  if 'matrix' in node:
   for i in [0,1,2,4,5,6,8,9,10]:node['matrix'][i]/=precision
  else:node['scale']=[s/precision for s in node.get('scale',[1,1,1])]
 def texture_transform(value):
  if not isinstance(value,dict):return
  for key,item in value.items():
   if key.endswith('Texture') and isinstance(item,dict) and 'index' in item:
    assert not item.get('extensions',{}).get('KHR_texture_transform')
    item.setdefault('extensions',{})['KHR_texture_transform']={'scale':[uvrange,uvrange]}
   elif isinstance(item,dict):texture_transform(item)
 for material in doc['materials']:texture_transform(material)
 newbin=bytearray()
 for vi,view in enumerate(doc['bufferViews']):
  while len(newbin)%4:newbin.append(0)
  data=replacements.get(vi,oldbin[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);view['byteOffset']=len(newbin);view['byteLength']=len(data);newbin.extend(data)
 while len(newbin)%4:newbin.append(0)
 doc['buffers'][0]['byteLength']=len(newbin)
 for key in ['extensionsUsed','extensionsRequired']:
  doc.setdefault(key,[])
  for extension in ['KHR_mesh_quantization','KHR_texture_transform']:
   if extension not in doc[key]:doc[key].append(extension)
 chunk=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();chunk+=b' '*((-len(chunk))%4)
 path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(chunk)+len(newbin))+struct.pack('<II',len(chunk),0x4e4f534a)+chunk+struct.pack('<II',len(newbin),0x004e4942)+newbin)
 return {'before':len(raw),'after':path.stat().st_size}

if __name__=='__main__':
 import sys
 print(compact(sys.argv[1]))
