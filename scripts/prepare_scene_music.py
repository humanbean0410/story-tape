"""Normalize the six supplied tracks and pack bounded, overlapping score segments."""
import concurrent.futures
import hashlib
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
FFMPEG = '/Applications/Downie 4.app/Contents/Resources/ffmpeg'
DOWNLOADS = Path('/Users/wqr/Downloads')
ASSETS = SITE / 'dist/assets/music'
STEP, OVERLAP = 48.0, 0.32
TRACKS = [
 ('casa', 'Khruangbin', 'Friday Morning', 'Khruangbin - Friday Morning (Official Video)_320k.mp3'),
 ('station', 'Joe Hisaishi', 'A Town with an Ocean View', 'Joe Hisaishi - A Town with an Ocean View (Visualizer)_320k.mp3'),
 ('interior', 'Ryuichi Sakamoto', 'Aqua', 'Aqua（Instrumental）_320k.mp3'),
 ('courtyard', 'Takagi Masakatsu', 'Girls', 'Girls_320k.mp3'),
 ('diner', 'Vince Guaraldi Trio', 'Moon River', 'Vince Guaraldi Trio - Moon River_320k.mp3'),
 ('alley', 'Hermanos Gutiérrez', 'Los Amantes', 'Hermanos Gutiérrez - Los Amantes [Official Audio]_320k.mp3'),
]

def run(args):
 result = subprocess.run([FFMPEG, '-hide_banner', '-nostdin', '-y', *args], capture_output=True, text=True)
 if result.returncode:
  raise RuntimeError(result.stderr[-2500:])
 return result.stderr

def prepare(track):
 scene, artist, title, filename = track
 source = DOWNLOADS / filename
 print(f'Preparing {scene}: {title}', flush=True)
 stats_log = run(['-i', str(source), '-vn', '-af', 'loudnorm=I=-18:TP=-2:LRA=20:print_format=json', '-f', 'null', '-'])
 stats = json.loads(stats_log[stats_log.rfind('{'):stats_log.rfind('}')+1])
 norm = ('loudnorm=I=-18:TP=-2:LRA=20:linear=true'
         f":measured_I={stats['input_i']}:measured_TP={stats['input_tp']}"
         f":measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}"
         f":offset={stats['target_offset']}")
 segments = []
 with tempfile.TemporaryDirectory(prefix=f'casa-score-{scene}-') as temp:
  pcm = Path(temp) / 'normalized.wav'
  run(['-i', str(source), '-vn', '-af', norm, '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', str(pcm)])
  with wave.open(str(pcm)) as audio:
   duration = audio.getnframes() / audio.getframerate()
  for index in range(math.ceil(duration / STEP)):
   start = index * STEP
   length = min(STEP + OVERLAP, duration - start)
   temporary = Path(temp) / f'{index:02d}.mp3'
   run(['-ss', str(start), '-i', str(pcm), '-t', f'{length:.6f}', '-map_metadata', '-1',
        '-ar', '44100', '-ac', '2', '-c:a', 'libmp3lame', '-b:a', '128k', '-write_xing', '1', str(temporary)])
   data = temporary.read_bytes()
   assert len(data) < 1024 * 1024, 'Each music request must stay below one MiB.'
   digest = hashlib.sha256(data).hexdigest()
   name = f'{scene}-{index:02d}-{digest[:12]}.mp3'
   (ASSETS / name).write_bytes(data)
   segments.append({'url': f'assets/music/{name}', 'start': start, 'duration': round(length, 6),
                    'bytes': len(data), 'sha256': digest})
 result = {'artist': artist, 'title': title, 'duration': round(duration, 6), 'overlap': OVERLAP,
           'loudness': '-18 LUFS / -2 dBTP', 'source': 'User supplied audio', 'segments': segments}
 print(f'Ready {scene}: {duration:.1f}s, {len(segments)} segments', flush=True)
 return scene, result

ASSETS.mkdir(parents=True, exist_ok=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results = dict(pool.map(prepare, TRACKS))
ordered = {scene: results[scene] for scene, *_ in TRACKS}
(ASSETS / 'manifest.json').write_text(json.dumps(ordered, ensure_ascii=False, indent=2)+'\n')
(SITE / 'dist/selected-music.js').write_text('export const MUSIC='+json.dumps(ordered, ensure_ascii=False, indent=2)+';\n')
print('All six scores packed:', sum(len(t['segments']) for t in ordered.values()), 'segments.', flush=True)
