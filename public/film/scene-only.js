import {PROJECT,productMode,chapter,chapterIndex,setChapter,projectTimeline,assetUrl,notify} from './project-runtime.js?v=product-v1';
import * as THREE from 'three';
import { Scene3D } from './scene3d.js?v=20261013-monologue';
import { Station3D } from './station3d.js?v=20261013-monologue';
import { Interior3D } from './interior3d.js?v=20261013-monologue';
import { Diner3D,Alley3D } from './story-set3d.js?v=20261013-monologue';
import { Courtyard3D } from './courtyard3d.js?v=20261013-monologue';
import { SCRIPT } from './script-book.js?v=20261013-score-r4';
import { MUSIC } from './selected-music.js?v=20261013-score-r4';
import { BGM } from './bgm-shortlist.js?v=20261013-monologue';
import { StoryPlayback } from './story-cues.js?v=20261013-score-r4';
import { LENSES } from './camera-kit.js?v=20261013-monologue';
import { SETS,SET_ORDER,getShot } from './production-config.js?v=20261013-monologue';
import { backstageFrame } from './studio-controls.js?v=20261013-monologue';
import { configureStageReveal } from './stage-reveal.js?v=20261013-monologue';
import { DOLLY_MS,LIGHT_MS,RETURN_MS,SHOT_MS,ease,opening,retreat,workFocal } from './film-motion.js?v=20261013-monologue';
import { TapeDeck } from './tape-deck.js?v=20261013-monologue';
import { SoundStage } from './sound-stage.js?v=20261013-score-r4';
import { SceneControls } from './scene-controls.js?v=20261013-monologue';
if(PROJECT){SET_ORDER.splice(0,SET_ORDER.length,...PROJECT.chapters.map(c=>c.scene));document.title=PROJECT.title+' · 故事磁带';}
const $=id=>document.getElementById(id),reducedMotion=matchMedia('(prefers-reduced-motion: reduce)'),sets=new Map(),loading=new Map(),selection=Object.fromEntries(SET_ORDER.map(id=>[id,'master'])),takeNumbers=Object.fromEntries(SET_ORDER.map(id=>[id,0]));
const state={phase:'ready',backstage:true,light:0,lightTarget:0,pointer:[0,0],last:0,busy:false,cueStart:0,recordStart:0,playlist:false,trainDue:0,storyEnded:false};
let engine,renderer,activeId=PROJECT?PROJECT.chapters[0].scene:(SETS[location.hash.slice(1)]?location.hash.slice(1):'casa'),wideView=null,returning=null,lensMove=null;
const audio=new SoundStage(),selected=()=>getShot(activeId,selection[activeId]),announce=message=>$('announce').textContent=message,isFilming=()=>['dolly','lighting','recording'].includes(state.phase),locked=()=>state.busy||['prologue','dolly','lighting','returning'].includes(state.phase);
const deck=new TapeDeck({reducedMotion,audio,onPlay:openFilm,onPause:()=>{state.playlist=false;if(isFilming())cut();}});
const controls=new SceneControls({select:selectShot,action:beginTake,book:openBook,locked});
let subtitleKey='',openingSeen=false,preludeStart=0;
let playbackStarted=false;
const story=new StoryPlayback({shot:id=>selectShot(id,true),sound:storySound,subtitle:showSubtitle,ended:()=>{if(PROJECT&&chapterIndex===PROJECT.chapters.length-1)notify('complete',chapter().id);state.storyEnded=true;audio.stopMusic(2.4);$('next-act').classList.add('cue-ready');syncUI();}});
if(PROJECT){const normalStart=story.start.bind(story);story.start=(id,now)=>{normalStart(id,now);story.timeline=projectTimeline();};configureProject();}
function showSubtitle(beat){const key=beat?`${activeId}:${beat.index}`:'';if(key===subtitleKey)return;subtitleKey=key;$('film-subtitles').hidden=!beat;$('subtitle-speaker').textContent=beat?.who||'';$('subtitle-text').textContent=beat?.text||'';$('film-subtitles').dataset.line=beat?.index??'';}
function storySound(kind){if(PROJECT&&chapter().sound==='silent'&&kind!=='arrival')return;if(kind==='arrival')cueTrain(2300);else if(kind==='tape-stop'){state.playlist=false;audio.setTapeMotor(false);syncUI();}else audio.foley(kind);}
async function openFilm(id){if($('product-begin'))$('product-begin').hidden=true;if(PROJECT){const index=deck.projectIndex??chapterIndex;setChapter(index);id=chapter().scene;}if(!playbackStarted){playbackStarted=true;notify('start',chapter()?.id);}if(id!==activeId)await switchSet(id,{record:false});selection[activeId]='master';prepareFilmView();state.playlist=true;audio.setScene(activeId);if(openingSeen||PROJECT&&!PROJECT.opening){startFilmTake();return;}openingSeen=true;state.phase='prologue';preludeStart=performance.now();$('film-intro').hidden=false;syncUI();announce(PROJECT?`序幕。${PROJECT.title}。`:'序幕。老派约会之必要，借你一段路。');}
const actNumbers=['第一幕','第二幕','第三幕','第四幕','第五幕','第六幕'];let chapterTimer,chapterHideTimer;
function hideAct(){clearTimeout(chapterTimer);clearTimeout(chapterHideTimer);$('chapter-title').hidden=true;$('chapter-title').classList.remove('shown');}
function showAct(){hideAct();const index=PROJECT?chapterIndex:SET_ORDER.indexOf(activeId);$('act-number').textContent=actNumbers[index];$('act-title').textContent=PROJECT?chapter().title:SCRIPT.scenes.find(s=>s.id===activeId).title;$('chapter-title').hidden=false;requestAnimationFrame(()=>$('chapter-title').classList.add('shown'));chapterTimer=setTimeout(()=>{$('chapter-title').classList.remove('shown');chapterHideTimer=setTimeout(()=>$('chapter-title').hidden=true,600);},3600);}
function syncFilmRect(){if(!engine?.rect)return;const [x,y,w,h]=engine.rect;for(const [key,value]of Object.entries({'--film-left':x,'--film-top':y,'--film-width':w,'--film-height':h}))document.documentElement.style.setProperty(key,`${value}px`);}
function syncUI(){
  const shot=selected(),spec=SETS[activeId],focal=state.phase==='ready'?shot.focal:Math.round(engine?.focalLength??shot.focal);document.body.dataset.phase=state.phase;document.body.dataset.set=activeId;document.body.dataset.backstage=String(state.backstage);
  $('scene-caption').textContent=`${actNumbers[PROJECT?chapterIndex:SET_ORDER.indexOf(activeId)]} / ${spec.name}`;$('film-hud').hidden=['ready','prologue'].includes(state.phase);$('cut').hidden=!isFilming();$('cut').disabled=state.phase==='returning'||state.busy;$('slate').textContent=`SC ${spec.number} · TAKE ${String(takeNumbers[activeId]).padStart(2,'0')}`;
  $('next-act').hidden=PROJECT?chapterIndex===PROJECT.chapters.length-1:activeId===SET_ORDER.at(-1);$('next-act').disabled=locked();$('master-shot').hidden=state.phase!=='recording'||selection[activeId]==='master';$('master-shot').disabled=locked();
  $('camera-readout').textContent=`${focal} MM · F${engine?.shallowFocus?'2.8':'11'} · 24 FPS · 2.39:1`;$('phase-label').textContent={ready:'',prologue:'序幕',dolly:'推轨',lighting:'灯光',recording:state.storyEnded?'本幕结束':`${shot.name} / ${shot.size}`,returning:'退回片场'}[state.phase];
  $('story-follow').hidden=state.phase!=='recording';$('story-follow').setAttribute('aria-pressed',String(!story.manual));$('story-follow').setAttribute('aria-label',story.manual?'继续按剧本运镜':'按剧本运镜中');
  $('sound').setAttribute('aria-pressed',String(!audio.muted));$('sound').setAttribute('aria-label',audio.muted?'打开声音':'静音');deck.setTrack(activeId,state.playlist);if(PROJECT&&$('memory-open'))$('memory-open').hidden=state.phase!=='recording'||!chapter().photoAssetId;syncFilmRect();
}
function openBook(){if(PROJECT){openProjectBook();return;}
  const list=$('set-list');list.replaceChildren();
  for(const scene of SCRIPT.scenes){
    const li=document.createElement('li'),details=document.createElement('details'),summary=document.createElement('summary'),number=document.createElement('small'),name=document.createElement('strong'),beat=document.createElement('p');
    number.textContent=SETS[scene.id].number;name.textContent=scene.title;beat.textContent=`${SETS[scene.id].name} / ${scene.time}`;summary.append(number,name,beat);details.append(summary);details.open=scene.id===activeId;
    const location=document.createElement('p');location.className='script-location';location.textContent=scene.place;details.append(location);
    for(const [who,line] of scene.lines){const p=document.createElement('p');p.className=['动作','结尾'].includes(who)?'script-action':'script-dialogue';if(p.className==='script-dialogue'){const speaker=document.createElement('b');speaker.textContent=who+'　';p.append(speaker);}p.append(document.createTextNode(line));details.append(p);}
    const cue=document.createElement('p');cue.className='script-cue';cue.textContent=`镜头：${scene.camera}\n声音：${scene.sound}`;details.append(cue);
    const score=document.createElement('p');score.className='script-cue';score.textContent=`本幕配乐：${MUSIC[scene.id].artist} / ${MUSIC[scene.id].title}`;details.append(score);
    const music=document.createElement('details'),heading=document.createElement('summary');heading.textContent='其他配乐参考 · 点歌名试听';music.className='music-candidates';music.append(heading);
    const placement=document.createElement('p');placement.textContent=BGM[scene.id].entry;music.append(placement);
    for(const track of BGM[scene.id].tracks){const p=document.createElement('p'),link=document.createElement('a');link.textContent=`${track.artist} / ${track.title} ↗`;link.href=track.url;link.target='_blank';link.rel='noopener noreferrer';p.append(link,document.createElement('br'),document.createTextNode(track.fit));music.append(p);}details.append(music);li.append(details);list.append(li);
  }
  $('scene-book').showModal();$('scene-book').scrollTop=0;
}
function applyShot(shot){engine.lensIndex=Math.max(0,LENSES.indexOf(shot.focal));engine.shallowFocus=!!shot.shallow;engine.active=null;}
function selectShot(id,automatic=false){
  if(locked()||!engine?.ready)return;if(!automatic)story.manual=true;if(automatic&&selection[activeId]===id)return;selection[activeId]=id;const shot=selected();applyShot(shot);audio.unlock().catch(()=>{});
  if(state.phase==='recording'){lensMove={from:engine.focalLength,to:shot.focal,start:performance.now()};engine.flyTo(`shot:${shot.id}`,reducedMotion.matches?0:SHOT_MS);if(shot.effect==='wind')engine.windTarget=1;syncUI();announce(`${shot.name}，${shot.size}，${shot.angle}。继续录制。`);}
  else{engine.focalLength=shot.focal;beginTake();}
}
function chooseShot(step){if(locked()||!engine?.ready)return;const shots=SETS[activeId].shots,i=shots.findIndex(s=>s.id===selection[activeId]);selectShot(shots[(i+step+shots.length)%shots.length].id);}
function ensureSet(id){
  if(sets.get(id)?.ready)return Promise.resolve(sets.get(id));if(loading.has(id))return loading.get(id);
  const promise=new Promise((resolve,reject)=>{const Class={casa:Scene3D,station:Station3D,interior:Interior3D,diner:Diner3D,alley:Alley3D,courtyard:Courtyard3D}[id];const set=new Class($('scene'),{renderer,sceneOnly:true,reducedMotion,onReady:()=>{renderer=set.renderer;resolve(set);},onError:reject,onVisit:()=>{},onHover:()=>{}});set.enabled=false;sets.set(id,set);});loading.set(id,promise);return promise;
}
function prepareWide(set){
  controls.attach(set);if(!set.stageReveal)configureStageReveal(set);set.stageReveal.value=0;set.gearReveal.value=0;set.stopPerformance?.();set.cinemaAmount=0;set.cinematic=false;set.recording=false;set.setBackstage(true);set.resize({preserveView:true});const wide=backstageFrame(set);set.position.copy(wide.pos);set.target.copy(wide.target);set.flight=null;set.orbit=null;wideView=null;lensMove=null;
}
function prepareFilmView(){
  controls.attach(engine);if(!engine.stageReveal)configureStageReveal(engine);engine.stopPerformance?.();engine.flight=null;engine.orbit=null;wideView=null;lensMove=null;state.trainDue=0;state.phase='ready';state.backstage=false;state.light=SETS[activeId].light;state.lightTarget=state.light;engine.setBackstage(false);engine.cinematic=true;engine.recording=true;engine.cinemaAmount=1;engine.stageReveal.value=1;engine.gearReveal.value=1;const shot=PROJECT?getShot(activeId,chapter().beats[0].shot):selected();selection[activeId]=shot.id;applyShot(shot);engine.focalLength=shot.focal;engine.focalTo=shot.focal;engine.resize({preserveView:true});const frame=engine.frame(`shot:${shot.id}`);engine.position.copy(frame.pos);engine.target.copy(frame.target);syncFilmRect();
}
function startFilmTake(){story.stop();state.playlist=true;state.storyEnded=false;$('next-act').classList.remove('cue-ready');takeNumbers[activeId]++;startRecording(performance.now());}
function cueTrain(delay=2300){if(activeId!=='station')return;engine.prepareTrain?.();engine.trainQueued=true;state.trainDue=performance.now()+delay;if(!PROJECT||chapter().sound!=='silent')audio.trainCue(delay/1000);}
function beginTake(){
  if(!engine?.ready||state.busy||['prologue','returning'].includes(state.phase))return;
  if(isFilming()){state.playlist=false;cut();return;}
  state.playlist=true;state.storyEnded=false;$('next-act').classList.remove('cue-ready');story.stop();audio.unlock().then(()=>audio.setScene(activeId)).catch(()=>{});
  controls.clear();const shot=selected();applyShot(shot);engine.stopPerformance?.();state.trainDue=0;const fromPos=engine.position.clone(),fromTarget=engine.target.clone(),fromFocal=workFocal(engine.camera.fov,engine.camera.aspect);
  wideView={pos:fromPos.clone(),target:fromTarget.clone(),fov:engine.camera.fov,focal:fromFocal};engine.setBackstage(false);engine.cinematic=true;engine.cinemaAmount=0;engine.recording=true;engine.focalFrom=fromFocal;engine.focalTo=shot.focal;engine.focalLength=fromFocal;engine.resize({preserveView:true});engine.position.copy(fromPos);engine.target.copy(fromTarget);engine.rig.visible=true;engine.stageReveal.value=0;engine.gearReveal.value=0;
  const frame=engine.frame(`shot:${shot.id}`),via=fromPos.clone().lerp(frame.pos,.5);via.y+=.4;via.z+=.35;engine.flyFrame(frame,reducedMotion.matches?0:DOLLY_MS,via);takeNumbers[activeId]++;state.phase=reducedMotion.matches?'recording':'dolly';state.backstage=false;state.lightTarget=0;state.light=0;state.cueStart=performance.now();state.recordStart=state.cueStart;
  if(reducedMotion.matches)startRecording(state.cueStart);syncUI();announce(`${actNumbers[PROJECT?chapterIndex:SET_ORDER.indexOf(activeId)]}，${SETS[activeId].name}，${shot.name}。开拍。`);
}
function startRecording(now){
  state.phase='recording';state.recordStart=now;state.lightTarget=SETS[activeId].light;engine.cinemaAmount=1;engine.stageReveal.value=1;engine.gearReveal.value=1;engine.focalLength=engine.focalTo??selected().focal;engine.resize({preserveView:true});if(selected().effect==='wind')engine.windTarget=1;story.start(activeId,now);if(PROJECT)notify('chapter',chapter().id);story.manual=PROJECT?selection[activeId]!==chapter().beats[0].shot:selection[activeId]!=='master';showAct();audio.foley('slate');audio.playMusic(activeId);syncUI();announce('录制开始。台词和镜头按剧本展开。');
}
function finishReturn(){
  engine.cinemaAmount=0;engine.stageReveal.value=0;engine.gearReveal.value=0;engine.setBackstage(true);engine.resize({preserveView:true});engine.position.copy(returning.frame.pos);engine.target.copy(returning.frame.target);engine.flight=null;engine.orbit=null;engine.camera.fov=returning.fov;engine.camera.updateProjectionMatrix();state.phase='ready';state.backstage=true;engine.focalLength=selected().focal;const resolve=returning.resolve;returning=null;syncUI();resolve?.();announce('回到片场。点击摄影机选择下一机位。');
}
function cut(){
  if(!engine?.ready||state.phase==='ready')return Promise.resolve();if(returning)return returning.promise;story.stop();hideAct();state.playlist=false;state.trainDue=0;audio.stopTrain();audio.stopMusic(.7);engine.stopPerformance?.();lensMove=null;state.phase='returning';state.lightTarget=0;
  const frame=wideView||{...backstageFrame(engine),fov:engine.mobile?43:35};frame.focal=workFocal(frame.fov,innerWidth/innerHeight);const from={crop:engine.cinemaAmount??1,background:engine.stageReveal.value,gear:engine.gearReveal.value,focal:engine.focalLength,toFocal:frame.focal};returning={start:performance.now(),frame,fov:frame.fov,from};returning.promise=new Promise(resolve=>returning.resolve=resolve);const via=engine.position.clone().lerp(frame.pos,.5);via.y+=.4;via.z+=.35;engine.flyFrame(frame,reducedMotion.matches?0:RETURN_MS,via);const promise=returning.promise;syncUI();if(reducedMotion.matches)finishReturn();return promise;
}
async function switchSet(id,{record=true}={}){
  if(state.busy||id===activeId)return;state.busy=true;syncUI();const previous=engine;state.trainDue=0;audio.stopTrain();audio.stopMusic(.75);audio.preloadMusic(id);
  try{story.stop();hideAct();document.body.classList.add('changing');await new Promise(resolve=>setTimeout(resolve,reducedMotion.matches?0:800));previous.stopPerformance?.();previous.enabled=false;const next=await ensureSet(id);engine=next;activeId=id;selection[id]='master';prepareFilmView();engine.enabled=true;history.replaceState(null,'',location.pathname+location.search+`#${id}`);if(!deck.visible)audio.setScene(id);if(record)startFilmTake();announce(`A${SETS[id].number}，${SETS[id].name}。`);}
  catch(error){console.error('Scene transition:',error);engine=previous;previous.enabled=true;controls.attach(previous);loading.delete(id);sets.delete(id);state.playlist=false;announce('场景暂未加载，请重试。');}
  finally{state.busy=false;document.body.classList.remove('changing');syncUI();}
}
function returnToTape(){if(state.busy)return;story.stop();hideAct();$('film-intro').hidden=true;state.playlist=false;state.trainDue=0;audio.stopTrain();engine?.stopPerformance?.();state.phase='ready';deck.open();syncUI();}
$('book-close').addEventListener('click',()=>$('scene-book').close());$('cut').addEventListener('click',()=>{state.playlist=false;cut();});$('deck-open').addEventListener('click',returnToTape);$('sound').addEventListener('click',()=>{audio.toggle();syncUI();});
$('next-act').addEventListener('click',async()=>{if(locked()||!engine?.ready)return;if(PROJECT){await advanceProjectChapter();return;}const next=SET_ORDER[SET_ORDER.indexOf(activeId)+1];if(!next)return;state.playlist=false;await switchSet(next);});
$('story-follow').addEventListener('click',()=>{story.follow();syncUI();});
$('master-shot').addEventListener('click',()=>{if(state.phase==='recording')selectShot('master');});
addEventListener('pointermove',e=>state.pointer=[e.clientX/innerWidth*2-1,1-e.clientY/innerHeight*2]);addEventListener('pointerout',e=>{if(!e.relatedTarget)state.pointer=[0,0];});addEventListener('resize',()=>{engine?.resize({preserveView:true});syncFilmRect();});
addEventListener('hashchange',async()=>{const id=location.hash.slice(1);if(!engine?.ready)await loading.get(activeId);state.playlist=false;if(SETS[id]){if(deck.visible)deck.hide();await switchSet(id);}else if(!id){returnToTape();}});
addEventListener('keydown',e=>{if(state.busy||deck.visible||$('scene-book').open)return;if(e.code==='ArrowLeft'||e.code==='ArrowRight'){e.preventDefault();chooseShot(e.code==='ArrowRight'?1:-1);}if(e.code==='Space'&&!['BUTTON','SELECT','INPUT'].includes(document.activeElement.tagName)){e.preventDefault();beginTake();}if(e.code==='Escape'&&isFilming()){state.playlist=false;cut();}});
function timecode(ms){const f=Math.floor(ms/1000*24);return[Math.floor(f/86400),Math.floor(f/1440)%60,Math.floor(f/24)%60,f%24].map(x=>String(x).padStart(2,'0')).join(':');}
function animate(now){
  if(state.phase==='prologue'&&now-preludeStart>=(reducedMotion.matches?1200:3200)){$('film-intro').hidden=true;startFilmTake();}
  const dt=Math.min((now-state.last)/1000||.016,.05);state.last=now;
  if(engine?.ready&&state.phase==='dolly'){const elapsed=now-state.cueStart,f=opening(Math.min(1,elapsed/DOLLY_MS));engine.cinemaAmount=f.crop;engine.focalLength=engine.focalFrom+(engine.focalTo-engine.focalFrom)*f.lens;engine.stageReveal.value=f.background;engine.gearReveal.value=f.gear;engine.resize({preserveView:true});syncFilmRect();if(elapsed>=DOLLY_MS){state.phase='lighting';state.lightTarget=SETS[activeId].light;syncUI();}}
  if(engine?.ready&&state.phase==='lighting'&&now-state.cueStart>=DOLLY_MS+LIGHT_MS)startRecording(now);
  if(returning){const progress=Math.min(1,(now-returning.start)/RETURN_MS),f=retreat(progress,returning.from);engine.cinemaAmount=f.crop;engine.focalLength=f.focal;engine.stageReveal.value=f.background;engine.gearReveal.value=f.gear;engine.resize({preserveView:true});syncFilmRect();}
  if(lensMove){const k=ease((now-lensMove.start)/SHOT_MS);engine.focalLength=lensMove.from+(lensMove.to-lensMove.from)*k;if(k===1){lensMove=null;syncUI();}}
  if(state.trainDue&&now>=state.trainDue){state.trainDue=0;if(activeId==='station'&&!deck.visible){engine.trainQueued=false;engine.startTrain();}}
  state.light+=(state.lightTarget-state.light)*(1-Math.exp(-dt*2));if(!deck.visible)engine?.update(now,dt,{light:state.light,mode:state.backstage?'backstage':'filming',pointer:state.pointer,depthView:0,depthAmount:1});if(returning&&now-returning.start>=RETURN_MS)finishReturn();
  const elapsed=state.phase==='recording'?now-state.recordStart:0;$('timecode').textContent=timecode(elapsed);deck.update(now,dt);audio.setTapeMotor(deck.playing,deck.visible);story.update(now,state.phase!=='recording'||deck.visible||$('scene-book').open||$('memory-paper')?.open||document.hidden);controls.update({phase:state.phase,selected:selection[activeId],hidden:deck.visible||state.busy});audio.tick();
  // A take holds its scene indefinitely. Only the next-act prop or tape transport changes acts.
  requestAnimationFrame(animate);
}
syncUI();requestAnimationFrame(animate);function startScene(){return ensureSet(activeId).then(set=>{engine=set;renderer=set.renderer;engine.enabled=true;prepareWide(engine);applyShot(selected());engine.focalLength=selected().focal;document.body.classList.add('ready');syncUI();deck.setReady(true);if(PROJECT){notify('loaded',chapter().id);const button=$('product-begin');if(button){button.disabled=false;button.textContent=PROJECT.opening?'跳过开场，直接播放':'开始播放';}}audio.preloadMusic(activeId);if(!deck.visible){audio.setScene(activeId);}}).catch(error=>{console.error('Initial scene:',error);document.body.classList.add('error');$('fallback').hidden=false;announce('场景加载失败，请重试。');if(deck.visible){$('entry-status').textContent='第一场未能下载完成';$('tape-retry').hidden=false;}});}
for(const id of ['tape-retry','scene-retry'])$(id).addEventListener('click',()=>location.reload());
addEventListener('model-progress',event=>{if(deck.visible&&deck.ready&&!deck.stageReady)$('entry-status').textContent=event.detail.progress<1?`第一场正在就位 · ${Math.round(event.detail.progress*100)}%`:'第一场正在准备画面…';});
deck.trackId=activeId;if(PROJECT){deck.projectIndex=0;deck.stepTrack=step=>{if(deck.animation)return;deck.projectIndex=(deck.projectIndex+step+PROJECT.chapters.length)%PROJECT.chapters.length;setChapter(deck.projectIndex);deck.trackId=chapter().scene;audio.mechanism();$('entry-status').textContent=`${actNumbers[chapterIndex]} · ${chapter().title}`;};}if(PROJECT&&!PROJECT.opening){startScene();}else{deck.open();deck.load().then(()=>{if(deck.ready)startScene();});}

function configureProject(){
  const begin=document.createElement('button');begin.id='product-begin';begin.type='button';begin.className=PROJECT.opening?'skip-tape-opening':'direct-film-begin';begin.disabled=true;begin.textContent='场景正在就位…';begin.addEventListener('click',async()=>{if(!engine?.ready||state.busy)return;begin.hidden=true;deck.animation=null;audio.stopTapeOpening();deck.hide();try{await audio.unlock();}catch{}await openFilm(chapter().scene);});document.body.append(begin);
  const title=$('opening-title');title.querySelector('small').textContent=`一盘磁带 · ${PROJECT.chapters.length} 幕 · ${PROJECT.author||'你的故事'}`;title.querySelector('p').textContent=PROJECT.title;
  $('film-intro').querySelector('small').textContent='序幕 · STORY TAPE';$('film-intro').querySelector('h1').textContent=PROJECT.title;$('film-intro').querySelector('p').textContent=PROJECT.subtitle;$('film-intro').querySelector('span').textContent=PROJECT.dedication||'给这段故事，留一点时间。';
  const normalSetScene=audio.setScene.bind(audio),normalStop=audio.stopMusic.bind(audio);let uploaded=null,fadeTimer;
  audio.preloadMusic=()=>Promise.resolve(null);
  audio.playMusic=async()=>{
    audio.stopMusic(.2);clearTimeout(fadeTimer);const current=chapter();
    if(audio.ambient)audio.ambient.gain.setTargetAtTime(current.sound==='silent'?0:1,audio.ctx.currentTime,.3);
    if(current.sound!=='upload'||!current.audioAssetId)return false;
    const element=new Audio(assetUrl(current.audioAssetId));element.preload='auto';element.loop=false;element.crossOrigin='anonymous';
    const bus=audio.bus(1.1),node=audio.ctx.createMediaElementSource(element);node.connect(bus);uploaded={element,bus,node};
    try{await element.play();return true;}catch{announce('上传的声音暂时无法播放。你可以打开声音后重试。');return false;}
  };
  audio.stopMusic=(fade=.7)=>{
    normalStop(fade);if(!uploaded)return;const previous=uploaded;uploaded=null;previous.bus.gain.setTargetAtTime(0,audio.ctx.currentTime,Math.max(.03,fade/3));setTimeout(()=>{previous.element.pause();previous.element.src='';previous.node.disconnect();previous.bus.disconnect();},(fade+.1)*1000);
  };
  audio.setScene=(id,force)=>{normalSetScene(id,force);if(audio.ambient&&chapter().sound==='silent'&&id!=='tape')audio.ambient.gain.setTargetAtTime(0,audio.ctx.currentTime,.15);};
  const paperButton=document.createElement('button');paperButton.className='edge-tool';paperButton.id='memory-open';paperButton.type='button';paperButton.textContent='留在这里的照片';paperButton.hidden=true;paperButton.addEventListener('click',()=>{const dialog=$('memory-paper');const image=dialog.querySelector('img');image.src=assetUrl(chapter().photoAssetId);image.alt=chapter().title;dialog.querySelector('p').textContent=chapter().title;story.last=performance.now();dialog.showModal();});document.querySelector('.quiet-corners>div').prepend(paperButton);
  const dialog=document.createElement('dialog');dialog.id='memory-paper';dialog.className='memory-paper';const close=document.createElement('button');close.className='paper-close';close.textContent='×';close.setAttribute('aria-label','收起照片');close.addEventListener('click',()=>dialog.close());const image=document.createElement('img'),caption=document.createElement('p');dialog.append(close,image,caption);document.body.append(dialog);dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});
  addEventListener('message',e=>{if(e.origin===location.origin&&e.source===parent&&e.data?.type==='story-tape:pause'){story.stop();audio.stopMusic(.2);audio.stopTrain();audio.setTapeMotor(false);}});
}
function openProjectBook(){
  const book=$('scene-book');book.querySelector('h1').textContent=PROJECT.title;book.querySelector('.book-note').textContent=PROJECT.subtitle||'你的台词本';book.querySelector('.eyebrow').textContent=`STORY TAPE / ${PROJECT.chapters.length} CHAPTERS`;book.querySelector('.book-foot').hidden=true;const list=$('set-list');list.replaceChildren();
  for(const [index,c]of PROJECT.chapters.entries()){const li=document.createElement('li'),details=document.createElement('details'),summary=document.createElement('summary');summary.textContent=`${actNumbers[index]} · ${c.title}`;details.open=index===chapterIndex;details.append(summary);for(const beat of c.beats){const p=document.createElement('p');p.className='script-dialogue';const b=document.createElement('b');b.textContent=beat.speaker+'　';p.append(b,document.createTextNode(beat.text));details.append(p);}li.append(details);list.append(li);}book.showModal();
}
async function advanceProjectChapter(){
  if(chapterIndex>=PROJECT.chapters.length-1)return;setChapter(chapterIndex+1);deck.projectIndex=chapterIndex;const next=chapter().scene;
  if(next===activeId){story.stop();audio.stopMusic(.7);prepareFilmView();startFilmTake();}else await switchSet(next);
}
