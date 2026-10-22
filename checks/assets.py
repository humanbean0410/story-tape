from pathlib import Path
import json,struct,re
assets=Path(__file__).resolve().parents[1]/'dist/assets'
counts={}
for name in ['casa-storefront','cassette-deck','hasedera-station','passenger-train','interior-room','vintage-diner','diner-upholstery','night-alley','night-alley-flora','studio-rig','chinese-courtyard']:
 p=assets/(name+'.glb');raw=p.read_bytes();magic,version,total=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and total==len(raw)
 jlen,jtype=struct.unpack_from('<II',raw,12);assert jtype==0x4e4f534a;doc=json.loads(raw[20:20+jlen]);binary_length,binary_type=struct.unpack_from('<II',raw,20+jlen);assert binary_type==0x004e4942
 assert doc['buffers'][0]['byteLength']<=binary_length
 for v in doc.get('bufferViews',[]):assert v.get('byteOffset',0)+v['byteLength']<=binary_length
 comp={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
 for a in doc.get('accessors',[]):
  if 'bufferView' not in a:continue
  v=doc['bufferViews'][a['bufferView']];element=comp[a['componentType']]*size[a['type']];assert a.get('byteOffset',0)+(a['count']-1)*v.get('byteStride',element)+element<=v['byteLength']
 names={n.get('name','') for n in doc.get('nodes',[])};assert not any(re.match(r'Actor|Performer|InteriorPair|DinerPair|AlleyPair',n) for n in names),name
 if name=='cassette-deck':assert {'Cassette','ReelLeft','ReelRight','DoorPivot','ButtonPlay','ButtonForward','ButtonRewind','JackPlug'}<=names
 counts[name]={'bytes':len(raw),'meshes':len(doc['meshes'])}
print('All GLB buffers, attributes, absent actor hierarchies and cassette animation nodes verified:',json.dumps(counts))
