/* Blender storefront, Cycles atlases, Three.js camera and object entrances. */
import { Scene3D } from './scene3d.js';
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const categories = [
    {id:'prologue',n:'00',object:'招牌',title:'这间店',display:'The\nPrologue',sub:'从街角开始',kicker:'THE SIGN / 一切从这里开始',intro:'有些想法，适合先放进一个地方。这里的橱窗、海报与长椅，收纳着不同形状的创作。',p:[.639,.331],depth:.78,zoom:1.8},
    {id:'ai-product',n:'01',object:'左橱窗',title:'AI × Product',display:'AI ×\nProduct',sub:'把可能变成可用',kicker:'THE LEFT WINDOW / 想象与使用之间',intro:'把新技术放进真实的使用情境里。从一个问题出发，让想象成为可以触碰的体验。',p:[.594,.536],depth:.70,zoom:2.65},
    {id:'film',n:'02',object:'右橱窗',title:'Film / Documentary',display:'Film /\nDocumentary',sub:'看见正在发生的事',kicker:'THE RIGHT WINDOW / 观察先于表达',intro:'镜头靠近日常，故事藏在缝隙。保留街角的时间，也保留没有被安排的瞬间。',p:[.836,.550],depth:.66,zoom:2.7},
    {id:'editorial',n:'03',object:'墙上海报',title:'Editorial',display:'Editorial',sub:'为想法找到语言',kicker:'THE POSTERS / 文字也有自己的光',intro:'把观察放慢，把思考展开。文字、图像和编辑，共同构成一个想法抵达别人的方式。',p:[.392,.569],depth:.83,zoom:3.25},
    {id:'research',n:'04',object:'长椅',title:'Research',display:'Research',sub:'坐下来，再问一次',kicker:'THE BENCH / 给问题留一点时间',intro:'从细小的观察开始，验证一个判断。研究不急着给出答案，先把问题问清楚。',p:[.602,.730],depth:.95,zoom:2.6},
    {id:'about',n:'05',object:'门',title:'About',display:'About',sub:'走进创作的背后',kicker:'THE DOOR / 走进来，聊一聊',intro:'产品、影像、研究、文字。在这些不同的语言之间，寻找一种有温度的表达。',p:[.373,.712],depth:.84,zoom:2.4}
  ];
  const byId = Object.fromEntries(categories.map(c => [c.id,c]));
  const scene = $('scene'), room = $('room'), hotspots = $('hotspots');
  const state = {mode:'idle',active:null,light:0,lightTarget:0,depthAmount:1,depthView:0,depthTarget:0,zoom:1,center:[.5,.515],pointer:[0,0],drift:[0,0],flight:null,started:0,muted:true,audio:null,filmPlaying:false,filmElapsed:0,filmLast:0,frame:0,viewport:null,last:0};
  const markerMap = new Map();
  let engine3d=null;
  let transitionToken = 0, pendingTimer = null;
  const lerp=(a,b,t)=>a+(b-a)*t;
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const ease=t=>t*t*(3-2*t);
  const announce=text=>$('announce').textContent=text;
  const escape=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function geometry(){return {w:innerWidth,h:innerHeight,mobile:innerWidth<=600};}
  function resize(){state.viewport=geometry();engine3d?.resize();positionMarkers();}
  addEventListener('resize',resize);
  function project(c){return engine3d?.ready?engine3d.project(c.id):[-999,-999];}
  function positionMarkers(){categories.forEach(c=>{const p=project(c);const el=markerMap.get(c.id);if(el){el.style.left=p[0]+'px';el.style.top=p[1]+'px';}});}
  function moveCamera(c,duration=1350){engine3d?.flyTo(c?.id||null,duration);state.flight=reducedMotion.matches||!duration?null:{start:performance.now(),duration};}

  categories.forEach(c=>{
    const button=document.createElement('button');button.className='hotspot';button.dataset.category=c.id;button.setAttribute('aria-label',`${c.object}：${c.title}`);button.innerHTML=`<span class="number">${c.n}</span><span class="object-label">${escape(c.title)}</span>`;
    button.addEventListener('click',()=>visit(c.id));button.addEventListener('pointerenter',()=>showCallout(c));button.addEventListener('focus',()=>showCallout(c));button.addEventListener('pointerleave',hideCallout);button.addEventListener('blur',hideCallout);hotspots.append(button);markerMap.set(c.id,button);
  });
  function showCallout(c){
    if(state.mode!=='shooting')return;
    const p=project(c);$('callout-number').textContent=`${c.n} / ${c.object}`;$('callout-title').textContent=c.title;$('callout-sub').textContent=c.sub;
    $('callout').style.left=clamp(p[0]+30,20,innerWidth-280)+'px';$('callout').style.top=clamp(p[1]-105,150,innerHeight-200)+'px';$('callout').classList.add('visible');
  }
  function hideCallout(){$('callout').classList.remove('visible');}
  function setMode(mode){state.mode=mode;document.body.dataset.state=mode;hotspots.inert=mode!=='shooting';$('opening').inert=mode!=='idle';$('set-controls').hidden=mode==='idle';$('instruction').textContent=mode==='idle'?'从一个街角，进入很多种可能。':state.viewport?.mobile?'轻点店铺里的物件，进入下一幕。':'移动鼠标看一看。点击店里的物件，进入下一幕。';$('location-note').hidden=mode!=='idle';}
  function action(){
    if(state.mode!=='idle')return;state.started=performance.now();state.lightTarget=1;$('lighting').setAttribute('aria-pressed','true');$('lighting').textContent='灯光开';setMode('shooting');moveCamera(null,850);$('slate').textContent='SCENE 001 / CAMERA ROLLING';announce('开拍。六个店铺物件已成为作品入口。');
    setTimeout(()=>{if(state.mode==='shooting')markerMap.get('ai-product').focus({preventScroll:true});},reducedMotion.matches?0:1300);
  }
  function cut(){
    if(state.mode==='room'||state.mode==='entering')return;
    clearTimeout(pendingTimer);transitionToken++;state.active=null;state.lightTarget=0;state.depthTarget=0;moveCamera(null,900);setMode('idle');hideCallout();$('slate').textContent='SCENE 001 / EXT. DAY';$('action').focus({preventScroll:true});if(!state.muted)toggleSound();history.replaceState(null,'',location.pathname+location.search);announce('停机。回到安静的街景。');
  }
  $('action').addEventListener('click',action);$('cut').addEventListener('click',cut);
  $('lighting').addEventListener('click',()=>{state.lightTarget=state.lightTarget?0:1;$('lighting').textContent=state.lightTarget?'灯光开':'灯光关';$('lighting').setAttribute('aria-pressed',String(!!state.lightTarget));});
  addEventListener('pointermove',e=>{if(e.pointerType==='touch'||state.mode==='room'&&state.active!=='research'||state.mode==='entering')return;state.pointer=[(e.clientX/innerWidth-.5)*2,(e.clientY/innerHeight-.5)*2];},{passive:true});
  document.documentElement.addEventListener('pointerleave',()=>state.pointer=[0,0]);
  reducedMotion.addEventListener('change',()=>{state.pointer=[0,0];if(state.flight)moveCamera(state.active?byId[state.active]:null,0);});

  function visit(id,{historyMode='push',instant=false}={}){
    const c=byId[id];if(!c)return;
    if(state.mode==='idle')action();
    clearTimeout(pendingTimer);const token=++transitionToken;
    if(room.open){room.classList.remove('visible');room.close();}
    state.active=id;state.depthTarget=0;state.filmPlaying=false;state.filmElapsed=0;hideCallout();setMode('entering');moveCamera(c,instant?0:1350);
    $('transition-caption').querySelector('span').textContent=c.title;
    if(historyMode==='push')history.pushState({scene:id},'',`#${id}`);
    document.title=`${c.title} · Casa de las Bellas`;
    pendingTimer=setTimeout(()=>{if(token!==transitionToken)return;renderRoom(c);setMode('room');room.inert=true;room.showModal();requestAnimationFrame(()=>room.classList.add('visible'));$('room-scroll').scrollTop=0;pendingTimer=setTimeout(()=>{if(token!==transitionToken)return;room.inert=false;$('back').focus({preventScroll:true});},instant||reducedMotion.matches?0:760);announce(`进入${c.title}。按 Escape 返回街景。`);},instant||reducedMotion.matches?0:1000);
  }
  function back({historyMode='replace'}={}){
    const c=byId[state.active];clearTimeout(pendingTimer);transitionToken++;state.filmPlaying=false;state.depthTarget=0;state.active=null;room.classList.remove('visible');room.inert=false;if(room.open)room.close();setMode('returning');moveCamera(null,1000);state.returnFocus=c?.id||null;if(!state.flight)setMode('shooting');document.title='Casa de las Bellas · 开拍';
    if(historyMode==='replace')history.replaceState(null,'',location.pathname+location.search);
    if(c&&!state.flight)markerMap.get(c.id).focus({preventScroll:true});announce('返回街景。');
  }
  $('back').addEventListener('click',()=>{if(history.state?.scene){history.back();}else back();});
  room.addEventListener('cancel',e=>{e.preventDefault();if(history.state?.scene)history.back();else back();});
  addEventListener('popstate',()=>{const id=location.hash.slice(1);if(byId[id])visit(id,{historyMode:'none',instant:true});else if(state.active||state.mode==='entering')back({historyMode:'none'});});
  addEventListener('keydown',e=>{
    const tag=e.target.tagName;if(['INPUT','TEXTAREA','SELECT','BUTTON','SUMMARY'].includes(tag))return;
    if(e.code==='Space'&&state.mode==='idle'){e.preventDefault();action();}
    if(e.key==='Escape'&&state.mode==='shooting')cut();
    if(e.key==='Escape'&&state.mode==='entering')back();
  });

  function entry(n,title,meta,html,open=false){return `<details class="entry-row"${open?' open':''}><summary><span class="entry-num">${n}</span><span><strong>${title}</strong><small>${meta}</small></span><span class="entry-plus">+</span></summary><div class="entry-body"><span class="demo-tag">CONCEPT STUDY / 概念样片</span>${html}</div></details>`;}
  function renderRoom(c){
    $('room-locator').textContent=`${c.n} / ${c.object}`;$('room-kicker').textContent=c.kicker;$('room-title').textContent=c.display;$('room-intro').textContent=c.intro;$('room-footer-number').textContent=`SCENE ${c.n}`;
    const content=$('room-content');
    if(c.id==='prologue'){
      content.innerHTML=`<p class="prologue-quote">这间店，<br>就是我的作品集。</p><div class="in-scene-index">${categories.slice(1).map(d=>`<button data-visit="${d.id}"><small>${d.n}</small><span>${escape(d.title)}</span><span>↗</span></button>`).join('')}</div>`;
      content.querySelectorAll('[data-visit]').forEach(b=>b.addEventListener('click',()=>visit(b.dataset.visit)));
    }else if(c.id==='ai-product'){
      content.innerHTML='<div class="entry-list">'+entry('01','可用的想象','INTERACTION / STORYBOARD',`<p>从一句话走向一个拍摄计划。先让想法被看见，再讨论它是否值得实现。</p><form class="demo-form" id="story-form"><label for="story-input">写下一个想拍的日常场景</label><textarea id="story-input" maxlength="120" rows="2" placeholder="例如：雨后的一间街角小店">雨后的一间街角小店</textarea><button type="submit" class="text-action">生成三镜头草案 <span>↗</span></button><small class="demo-tag">本地交互演示 · 规则生成</small></form><ol id="storyboard" class="storyboard" aria-live="polite"></ol>`,true)+entry('02','人与界面之间','PRODUCT / DESIGN NOTE','<p>技术可以复杂，第一次接触它的动作应当简单。这个场景把功能藏进熟悉的物件：橱窗展示，门邀请，长椅让人停留。</p><h3>让动作先于解释</h3><p>用灯光说明状态，用镜头说明位置，用返回路径说明安全感。一个好的界面，帮助人知道此刻在哪里，以及下一步可以做什么。</p>')+'</div>';
      const generate=()=>{const raw=$('story-input').value.trim();if(!raw){$('story-input').focus();return;}const subject=escape(raw);$('storyboard').innerHTML=`<li><small>01 / WIDE / 6 SEC</small><strong>建立：${subject}</strong><p>先拍下完整的空间。固定镜头，让环境成为故事的起点。</p></li><li><small>02 / MEDIUM / 8 SEC</small><strong>靠近：寻找一个动作</strong><p>跟随人、光或风。让一个真实发生的变化决定镜头的方向。</p></li><li><small>03 / CLOSE / 6 SEC</small><strong>看见：留住一个细节</strong><p>停在最微小的痕迹上，用环境声结束，给观众一点余地。</p></li>`;};$('story-form').addEventListener('submit',e=>{e.preventDefault();generate();});generate();
    }else if(c.id==='film'){
      content.innerHTML='<div class="entry-list">'+entry('01','街角，二十秒','OBSERVATION / 00:20',`<p>同一张照片，另一种观看速度。一个二十秒的缓慢推进，练习从全景看见细节。</p><div id="film-screen" class="film-screen"><img src="assets/casa.jpg" alt="镜头缓慢靠近 Casa de las Bellas 街角"><div class="film-overlay"><span>STREET STUDY / 001</span><span id="film-clock">00:00</span></div></div><div class="film-progress"><i id="film-progress"></i></div><div class="film-controls"><button id="film-play" class="text-action" aria-pressed="false">播放样片 <span>▶</span></button><small>STILL PHOTO / CAMERA STUDY</small></div>`,true)+entry('02','在光改变之前','DOCUMENTARY / SHOT NOTES','<p>一盏灯亮起，玻璃变成镜子。店里与街上，开始拥有两种时间。</p><div class="quote">等待，是一种<br>参与拍摄的方式。</div><p>一个关于观察的拍摄提案：保持相同机位，记录招牌、橱窗和长椅在不同时刻的变化。素材将来自真实的等待与现场记录。</p>')+'</div>';
      $('film-play').addEventListener('click',()=>{state.filmPlaying=!state.filmPlaying;$('film-screen').classList.toggle('playing',state.filmPlaying);$('film-play').innerHTML=state.filmPlaying?'暂停样片 <span>Ⅱ</span>':'继续播放 <span>▶</span>';$('film-play').setAttribute('aria-pressed',String(state.filmPlaying));state.filmLast=performance.now();});
    }else if(c.id==='research'){
      content.innerHTML='<div class="entry-list">'+entry('01','一间店，几层空间','SPATIAL STUDY / INTERACTIVE',`<p>街道、橱窗、招牌、长椅，都有自己的几何结构。移动视点，会改变遮挡、角度与透视。</p><div class="depth-key"><span>远 / STREET</span><span>近 / BENCH</span></div><div class="depth-strip"></div><button class="depth-toggle" id="depth-toggle" aria-pressed="false">查看场景网格</button><label class="range-control" for="depth-range"><span>视差</span><input id="depth-range" type="range" min="0" max="150" value="100" aria-label="视差强度"><output id="depth-value">100%</output></label><p>店铺由 Blender 重建，表面光照由 Cycles 烘焙。模型依据一张参考照片估计比例，是空间复现，不是测量级建筑模型。</p>`,true)+entry('02','物件可以成为导航吗？','INTERACTION / DESIGN QUESTION','<p>把同一套内容分别放在菜单和店铺物件中，比较访客能否发现入口、理解分类并顺利返回。</p><h3>先观察三个动作</h3><p>第一次点击落在哪里？多久找到感兴趣的作品？读完后能否回到街景？这些是可验证的问题，而不是已经完成的研究结果。</p>')+'</div>';
      $('depth-toggle').addEventListener('click',()=>{state.depthTarget=state.depthTarget?0:1;$('depth-toggle').setAttribute('aria-pressed',String(!!state.depthTarget));$('depth-toggle').textContent=state.depthTarget?'返回场景材质':'查看场景网格';});
      $('depth-range').addEventListener('input',e=>{state.depthAmount=Number(e.target.value)/100;$('depth-value').value=e.target.value+'%';});
    }else if(c.id==='editorial'){
      content.innerHTML='<div class="entry-list">'+entry('01','慢一点，才看见','FIELD NOTES / 2 MIN',`<article class="note-text"><p><span class="drop-cap">有</span>些地方，第一眼并不特别。它们只是街边的一间小店，有一块招牌，两扇窗，一张长椅。</p><p>再看一眼，细节开始出现。玻璃接住对面的街道，海报留着一天的邀请，长椅等待还没有发生的谈话。一个空间的性格，往往在这些不用解释的东西里。</p><p>创作有时也一样。与其急着给一个想法加上标题，先让它待在日常里，看看它会与什么相遇。</p><p>慢一点。世界已经在那里。</p><span class="article-end">— A NOTE FROM THE STREET —</span></article>`,true)+entry('02','把作品放进一间店','EDITORIAL / DESIGN ESSAY','<article class="note-text"><p>一个目录告诉人有什么。一间店还可以告诉人：这些东西为什么在一起。</p><p>橱窗向外展示，门向内邀请，海报表达立场，长椅保留停顿。每个物件既是入口，也是阅读内容前的一点情绪。</p><p>当空间成为作品集，导航也成为叙事的一部分。点击不是离开首页，而是决定把镜头对准哪里。</p><span class="article-end">— SPACE AS A TABLE OF CONTENTS —</span></article>')+'</div>';
    }else if(c.id==='about'){
      content.innerHTML=`<p class="prologue-quote">在不同的语言之间，<br>把想法拍出来。</p><div class="note-text"><p>这里是一间创作工作室的空间提案。用产品理解使用，用影像观察日常，用研究追问原因，用文字把思考传递出去。</p><p>“开拍”是一种开始：把灯打开，把注意力放到眼前，让一个想法真正发生。</p></div><div class="process-line"><span>OBSERVE</span><span>→ QUESTION</span><span>→ MAKE</span><span>→ SHARE</span></div><dl class="colophon"><dt>场景</dt><dd>根据用户提供的 Casa de las Bellas 照片，用 Blender 重建的三维店铺</dd><dt>形式</dt><dd>可进入的空间作品集 / 概念版</dd><dt>内容</dt><dd>个人介绍、真实项目与联系方式待正式资料补充</dd></dl>`;
    }
  }

  // Optional synthesized ambience. Sound starts only after an explicit sound tap.
  function toggleSound(){
    state.muted=!state.muted;
    try{
      if(!state.audio){const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)throw new Error('Audio unavailable');const ctx=new Audio();const gain=ctx.createGain();gain.gain.value=0;gain.connect(ctx.destination);
        const buffer=ctx.createBuffer(1,ctx.sampleRate*4,ctx.sampleRate);const values=buffer.getChannelData(0);let brown=0;for(let i=0;i<values.length;i++){brown=(brown+(.02*(Math.random()*2-1)))/1.02;values[i]=brown*3.5;}
        const noise=ctx.createBufferSource();noise.buffer=buffer;noise.loop=true;const filter=ctx.createBiquadFilter();filter.type='lowpass';filter.frequency.value=390;noise.connect(filter);filter.connect(gain);noise.start();state.audio={ctx,gain};}
      if(!state.muted)state.audio.ctx.resume();state.audio.gain.gain.setTargetAtTime(state.muted?0:.075,state.audio.ctx.currentTime,.4);
    }catch{state.muted=true;}
    $('ambient').setAttribute('aria-pressed',String(!state.muted));$('ambient').setAttribute('aria-label',state.muted?'开启环境声':'关闭环境声');$('sound-label').textContent=state.muted?'声音关':'声音开';
  }
  $('ambient').addEventListener('click',toggleSound);
  document.addEventListener('visibilitychange',()=>{if(document.hidden){if(state.audio)state.audio.ctx.suspend();cancelAnimationFrame(state.frame);state.frame=0;}else{if(state.audio&&!state.muted)state.audio.ctx.resume();state.last=performance.now();state.filmLast=performance.now();if(!state.frame)state.frame=requestAnimationFrame(tick);}});

  function tick(now){
    const dt=Math.min((now-(state.last||now))/1000,.05);state.last=now;
    if(state.flight&&now-state.flight.start>=state.flight.duration){state.flight=null;if(state.mode==='returning'){setMode('shooting');positionMarkers();if(state.returnFocus)markerMap.get(state.returnFocus).focus({preventScroll:true});state.returnFocus=null;}}
    const rate=1-Math.exp(-dt*3.8);state.light=lerp(state.light,state.lightTarget,rate);state.depthView=lerp(state.depthView,state.depthTarget,rate);
    engine3d?.update(now,dt,{light:state.light,mode:state.mode,pointer:state.pointer,depthView:state.depthView,depthAmount:state.depthAmount});
    if(state.mode==='shooting')positionMarkers();
    if(state.mode!=='idle'){const frames=Math.floor((now-state.started)/1000*24);const s=Math.floor(frames/24);$('timecode').textContent=`${String(Math.floor(s/3600)).padStart(2,'0')}:${String(Math.floor(s/60)%60).padStart(2,'0')}:${String(s%60).padStart(2,'0')}:${String(frames%24).padStart(2,'0')}`;}
    if(state.active==='film'&&state.mode==='room'&&state.filmPlaying){state.filmElapsed+=(now-state.filmLast)/1000;state.filmLast=now;const t=state.filmElapsed%20;if($('film-clock')){$('film-clock').textContent='00:'+String(Math.floor(t)).padStart(2,'0');$('film-progress').style.width=(t/20*100)+'%';}}
    state.frame=requestAnimationFrame(tick);
  }
  $('action').disabled=true;$('action').querySelector('small').textContent='场景准备中';
  resize();
  engine3d=new Scene3D(scene,{reducedMotion,onReady:()=>{$('photo-fallback').style.opacity='0';$('action').disabled=false;$('action').querySelector('small').textContent='ACTION';positionMarkers();const initial=location.hash.slice(1);if(byId[initial])visit(initial,{historyMode:'none',instant:true});},onError:e=>{console.error('3D scene:',e);$('action').querySelector('small').textContent='加载失败，请刷新';announce('三维场景暂未加载，请刷新页面。');},onVisit:id=>visit(id),onHover:id=>id?showCallout(byId[id]):hideCallout()});
  state.frame=requestAnimationFrame(tick);
})();
