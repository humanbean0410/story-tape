import array, hashlib, json, math, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
tracks=json.loads((ROOT/'dist/assets/music/manifest.json').read_text())
assert list(tracks)==['casa','station','interior','courtyard','diner','alley']
assert [tracks[s]['title'] for s in tracks]==['Friday Morning','A Town with an Ocean View','Aqua','Girls','Moon River','Los Amantes']
ffmpeg='/Applications/Downie 4.app/Contents/Resources/ffmpeg'
def overlap(segment,at,seconds):
 result=subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-i',str(ROOT/'dist'/segment['url']),'-ss',str(at),'-t',str(seconds),'-ac','1','-ar','44100','-f','f32le','pipe:1'],capture_output=True,check=True)
 values=array.array('f');values.frombytes(result.stdout);return values
for scene,track in tracks.items():
 segments=track['segments']
 for i,segment in enumerate(segments):
  data=(ROOT/'dist'/segment['url']).read_bytes()
  assert len(data)==segment['bytes']<1024*1024
  assert hashlib.sha256(data).hexdigest()==segment['sha256']
  assert abs(segment['start']-i*48)<.001
  if i:assert abs(segments[i-1]['start']+segments[i-1]['duration']-segment['start']-track['overlap'])<.001
 assert abs(segments[-1]['start']+segments[-1]['duration']-track['duration'])<.001
 a=overlap(segments[0],48,track['overlap']);b=overlap(segments[1],0,track['overlap']);n=min(len(a),len(b));assert n>13000
 dot=sum(a[i]*b[i] for i in range(n));energy_a=sum(v*v for v in a[:n]);energy_b=sum(v*v for v in b[:n]);correlation=dot/math.sqrt(energy_a*energy_b)
 assert correlation>.96,(scene,correlation)
 assert max(abs(v) for v in a)<1 and max(abs(v) for v in b)<1
 print(f'{scene}: {len(segments)} verified segments; music-boundary correlation {correlation:.5f}')
print('All six selected songs retain continuous audio across overlaps, fit the request limit, and match their manifest checksums.')
