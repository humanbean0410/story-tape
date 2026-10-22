"""Losslessly compress the authored GLBs into bounded, cache-safe requests."""
import gzip, hashlib, json
from pathlib import Path

assets=Path(__file__).parent/'dist'/'assets'
folder=assets/'streamed'
folder.mkdir(exist_ok=True)
manifest={}
retained=set()
for model in sorted(assets.glob('*.glb')):
    original=model.read_bytes()
    packed=gzip.compress(original,compresslevel=9,mtime=0)
    digest=hashlib.sha256(packed).hexdigest()
    chunks=[]
    for index,offset in enumerate(range(0,len(packed),1024*1024)):
        chunk=packed[offset:offset+1024*1024]
        name=f'{model.stem}-{digest[:12]}-{index:02d}.bin'
        (folder/name).write_bytes(chunk)
        retained.add(name)
        chunks.append({'url':f'assets/streamed/{name}','bytes':len(chunk),'sha256':hashlib.sha256(chunk).hexdigest()})
    manifest[f'assets/{model.name}']={'codec':'gzip','bytes':len(original),'packedBytes':len(packed),'sha256':hashlib.sha256(original).hexdigest(),'chunks':chunks}
(assets/'model-packs.json').write_text(json.dumps(manifest,separators=(',',':'))+'\n')
print(f'Packed {len(manifest)} models into {sum(len(m["chunks"]) for m in manifest.values())} requests, each at most 1 MiB; original geometry and textures unchanged.')

# Remove obsolete generated fingerprints after all current packs are written.
for file in folder.glob('*.bin'):
    if file.name not in retained:file.unlink()
