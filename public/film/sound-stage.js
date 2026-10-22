import { SceneScore } from './scene-score.js?v=20261013-score-r4';
// Environmental Foley, the supplied tape opening, and the six selected scores.
export class SoundStage{
  constructor(){this.muted=false;this.sceneId='tape';this.nodes=[];this.trainToken=0;this.trainCueUntil=0;}
  async unlock(){
    this.ctx??=new (window.AudioContext||window.webkitAudioContext)();await this.ctx.resume();
    if(!this.master){this.master=this.ctx.createGain();this.master.gain.value=this.muted?0:.24;const limiter=this.ctx.createDynamicsCompressor();limiter.threshold.value=-18;limiter.ratio.value=3;this.master.connect(limiter).connect(this.ctx.destination);this.setScene(this.sceneId,true);if(this.motorWanted)this.setTapeMotor(true,this.motorVisible);}
    if(!this.score){this.musicBus=this.bus(1.65);this.score=new SceneScore(this.ctx,this.musicBus);this.preloadMusic(this.preloadScoreId||'casa');}
    if(this.pendingMusic){const id=this.pendingMusic;this.pendingMusic=null;this.playMusic(id);}
    this.loadTapeClip();
  }
  preloadMusic(id){this.preloadScoreId=id;return this.score?.preload(id).catch(error=>{console.warn('Scene music preload:',error);return null;})||Promise.resolve(null);}
  playMusic(id){if(!this.score){this.pendingMusic=id;return Promise.resolve(false);}this.pendingMusic=null;this.restoreMusic();return this.score.play(id,{delay:id==='alley'?1.4:.25});}
  stopMusic(fade=.7){this.pendingMusic=null;this.score?.stop(fade);}
  restoreMusic(){if(!this.musicBus||!this.ctx)return;const gain=this.musicBus.gain,now=this.ctx.currentTime;if(gain.cancelAndHoldAtTime)gain.cancelAndHoldAtTime(now);else gain.cancelScheduledValues(now);gain.setTargetAtTime(1.65,now,.35);}
  duckMusic(duration){if(!this.musicBus||!this.ctx)return;const gain=this.musicBus.gain,now=this.ctx.currentTime;if(gain.cancelAndHoldAtTime)gain.cancelAndHoldAtTime(now);else gain.cancelScheduledValues(now);gain.setTargetAtTime(.36,now,.16);gain.setTargetAtTime(1.65,now+duration,1.1);}
  loadTapeClip(){if(!this.clipPromise&&this.ctx)this.clipPromise=fetch('assets/tape-insert-7-16.mp3').then(r=>{if(!r.ok)throw new Error('Tape audio unavailable');return r.arrayBuffer();}).then(b=>this.ctx.decodeAudioData(b)).then(buffer=>this.tapeClip=buffer).catch(error=>{console.warn(error);return null;});return this.clipPromise||Promise.resolve(null);}
  async playTapeOpening(offset=0){
    if(!this.master)return null;await this.loadTapeClip();if(!this.tapeClip)return null;this.stopTapeOpening();
    const source=this.ctx.createBufferSource(),bus=this.bus(2.1),start=this.ctx.currentTime+.025;source.buffer=this.tapeClip;source.connect(bus);source.start(start,offset);this.openingClip={source,bus,start};source.onended=()=>{bus.disconnect();if(this.openingClip?.source===source)this.openingClip=null;};return start;
  }
  stopTapeOpening(){if(!this.openingClip)return;const {source,bus}=this.openingClip;this.openingClip=null;bus.gain.setTargetAtTime(0,this.ctx.currentTime,.04);setTimeout(()=>{try{source.stop();}catch{}bus.disconnect();},180);}
  toggle(){this.muted=!this.muted;if(this.master)this.master.gain.setTargetAtTime(this.muted?0:.24,this.ctx.currentTime,.14);else this.unlock().catch(()=>{});return this.muted;}
  bus(gain=1){const b=this.ctx.createGain();b.gain.value=gain;b.connect(this.master);return b;}
  setTapeMotor(playing,visible=false){
    this.motorWanted=playing;this.motorVisible=visible;if(!this.master||this.openingClip)return;
    if(playing&&!this.motor){const bus=this.bus(0),n=this.ctx.createBufferSource(),f=this.ctx.createBiquadFilter();const seconds=8,buffer=this.ctx.createBuffer(1,this.ctx.sampleRate*seconds,this.ctx.sampleRate),v=buffer.getChannelData(0);let filtered=0;
      for(let i=0;i<v.length;i++){const t=i/this.ctx.sampleRate;filtered=.82*filtered+.18*(Math.random()*2-1);const flutter=1+.09*Math.sin(t*Math.PI*2*.31);v[i]=filtered*.24+.065*Math.sin(t*Math.PI*2*116*flutter)+.02*Math.sin(t*Math.PI*2*232*flutter);}
      const seam=640;for(let i=0;i<seam;i++){const k=i/(seam-1);v[v.length-seam+i]=v[v.length-seam+i]*(1-k)+v[i]*k;}v[v.length-1]=v[0];n.buffer=buffer;n.loop=true;f.type='lowpass';f.frequency.value=1150;n.connect(f).connect(bus);n.start();this.motor={bus,node:n};}
    if(this.motor)this.motor.bus.gain.setTargetAtTime(playing?(visible?.65:.12):0,this.ctx.currentTime,.25);
    if(!playing&&this.motor){const old=this.motor;this.motor=null;setTimeout(()=>{try{old.node.stop();}catch{}old.bus.disconnect();},1300);}
  }
  noise(seconds=4){const b=this.ctx.createBuffer(1,Math.ceil(this.ctx.sampleRate*seconds),this.ctx.sampleRate),v=b.getChannelData(0);let x=0;for(let i=0;i<v.length;i++){x=(x+Math.random()*.2-.1)/1.035;v[i]=x;}return b;}
  bed(bus,{freq=350,gain=.05,type='lowpass',q=.5}={}){const n=this.ctx.createBufferSource(),f=this.ctx.createBiquadFilter(),g=this.ctx.createGain();n.buffer=this.noise();n.loop=true;f.type=type;f.frequency.value=freq;f.Q.value=q;g.gain.value=gain;n.connect(f).connect(g).connect(bus);n.start();return n;}
  setScene(id,force=false){
    if(this.sceneId===id&&this.ambient&&!force)return;if(this.sceneId!==id)this.stopMusic(.7);this.sceneId=id;if(!this.master)return;
    const now=this.ctx.currentTime,old=this.ambient,oldNodes=this.nodes;this.ambient=this.bus(0);this.ambient.gain.setTargetAtTime(1,now,.7);this.nodes=[];
    if(old){old.gain.setTargetAtTime(0,now,.55);setTimeout(()=>{oldNodes.forEach(n=>{try{n.stop();}catch{}});old.disconnect();},4000);}
    const settings={tape:[1200,.027],casa:[360,.035],station:[720,.064],interior:[260,.022],diner:[650,.03],alley:[250,.047],courtyard:[480,.023]};
    const [freq,gain]=settings[id]||settings.casa;this.nodes.push(this.bed(this.ambient,{freq,gain}));
    if(id==='diner')this.nodes.push(this.bed(this.ambient,{freq:1800,gain:.018,type:'bandpass'}));
    if(id==='alley')this.nodes.push(this.bed(this.ambient,{freq:1600,gain:.024,type:'highpass'}));
    if(id==='courtyard')this.nodes.push(this.bed(this.ambient,{freq:2300,gain:.009,type:'bandpass',q:.3}));
  }
  tone(freq,at,duration,gain=.1,type='sine',bus=this.ambient,pan=0){
    if(!this.ctx||!bus)return;const o=this.ctx.createOscillator(),g=this.ctx.createGain(),p=this.ctx.createStereoPanner(),f=this.ctx.createBiquadFilter();o.type=type;o.frequency.value=freq;f.type='lowpass';f.frequency.value=1400;p.pan.value=pan;g.gain.setValueAtTime(.0001,at);g.gain.exponentialRampToValueAtTime(gain,at+.018);g.gain.exponentialRampToValueAtTime(.0001,at+duration);o.connect(f).connect(g).connect(p).connect(bus);o.start(at);o.stop(at+duration+.04);
  }
  tick(){
    // No periodic pitched ambience. Foley and train warnings are script events.
    this.score?.tick();
  }
  foley(kind){
    if(!this.master)return;const t=this.ctx.currentTime,b=this.bus(),n=this.ctx.createBufferSource(),f=this.ctx.createBiquadFilter(),g=this.ctx.createGain();const specs={paper:[1700,.075,.45],cup:[2200,.04,.12],steps:[220,.12,.28],door:[450,.11,.45],'wood-door':[280,.095,1.0],slate:[1400,.19,.08],phone:[180,.07,.38],jukebox:[480,.06,.28],drop:[1100,.013,.11]},[freq,gain,duration]=specs[kind]||specs.paper;
    n.buffer=this.noise(duration+.1);f.type='bandpass';f.frequency.value=freq;f.Q.value=.55;g.gain.setValueAtTime(.001,t);g.gain.linearRampToValueAtTime(gain,t+.025);g.gain.exponentialRampToValueAtTime(.0001,t+duration);n.connect(f).connect(g).connect(b);n.start();n.stop(t+duration+.05);
    if(kind==='phone')this.tone(145,t,.35,.12,'triangle',b,.25);if(kind==='steps')this.tone(70,t+.35,.12,.03,'triangle',b,-.2);setTimeout(()=>b.disconnect(),2200);
  }
  mechanism(kind='click'){
    if(!this.ctx||!this.master)return;const t=this.ctx.currentTime,b=this.bus();this.tone(kind==='motor'?72:140,t,kind==='motor'?2.8:.09,kind==='motor'?.055:.13,'triangle',b);const n=this.ctx.createBufferSource(),f=this.ctx.createBiquadFilter(),g=this.ctx.createGain();n.buffer=this.noise(.24);f.type='bandpass';f.frequency.value=kind==='close'?1700:900;g.gain.setValueAtTime(.12,t);g.gain.exponentialRampToValueAtTime(.0001,t+.13);n.connect(f).connect(g).connect(b);n.start();n.stop(t+.22);setTimeout(()=>b.disconnect(),3200);
  }
  trainCue(delay=2.2){
    if(!this.master||this.sceneId!=='station'||this.ctx.currentTime<this.trainCueUntil)return false;const t=this.ctx.currentTime,token=++this.trainToken,bus=this.bus();this.trainCueUntil=t+delay+11;this.duckMusic(delay+10.6);this.tone(523.25,t,.8,.16,'sine',bus);
    const start=t+delay,n=this.ctx.createBufferSource(),f=this.ctx.createBiquadFilter(),g=this.ctx.createGain(),pan=this.ctx.createStereoPanner();n.buffer=this.noise(6);n.loop=true;f.type='bandpass';f.frequency.value=750;f.Q.value=.4;g.gain.setValueAtTime(.0001,start);g.gain.exponentialRampToValueAtTime(.63,start+2.2);g.gain.setValueAtTime(.63,start+4.9);g.gain.exponentialRampToValueAtTime(.0001,start+10);pan.pan.setValueAtTime(-.85,start);pan.pan.linearRampToValueAtTime(.85,start+9);n.connect(f).connect(g).connect(pan).connect(bus);n.start(start);n.stop(start+10.2);
    this.tone(52,start,10,.16,'triangle',bus);for(let i=0;i<28;i++)this.tone(80+i%3*14,start+i*.29,.06,.035,'triangle',bus,i/14-1);
    this.trainBus?.gain.setTargetAtTime(0,t,.1);this.trainBus=bus;n.onended=()=>{bus.disconnect();if(this.trainToken===token)this.trainBus=null;};return true;
  }
  stopTrain(){if(this.trainBus&&this.ctx)this.trainBus.gain.setTargetAtTime(0,this.ctx.currentTime,.2);this.trainToken++;this.trainCueUntil=0;this.restoreMusic();}
}
