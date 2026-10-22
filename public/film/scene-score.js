import { MUSIC } from './selected-music.js?v=20261013-score-r4';
import { fetchBytes } from './asset-transport.js?v=20261013-monologue';

const hold=(param,now)=>{if(param.cancelAndHoldAtTime)param.cancelAndHoldAtTime(now);else{const value=param.value;param.cancelScheduledValues(now);param.setValueAtTime(value,now);}};

// Short decoded segments keep mobile memory bounded. Their overlap contains the
// same musical samples, so complementary fades preserve a continuous performance.
export class SceneScore{
  constructor(ctx,output,{tracks=MUSIC,load=fetchBytes,onState=()=>{}}={}){
    Object.assign(this,{ctx,output,tracks,load,onState});this.cache=new Map();this.generation=0;this.active=null;
  }
  buffer(id,index){
    const key=`${id}:${index}`;if(this.cache.has(key))return this.cache.get(key);
    const segment=this.tracks[id]?.segments[index];if(!segment)return Promise.reject(new Error('配乐片段不存在'));
    const promise=this.load(segment.url).then(async bytes=>{
      if(bytes.length!==segment.bytes)throw new Error('配乐下载不完整');
      if(globalThis.crypto?.subtle){const digest=await crypto.subtle.digest('SHA-256',bytes);const actual=[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');if(actual!==segment.sha256)throw new Error('配乐下载校验失败');}
      const audio=await this.ctx.decodeAudioData(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
      if(audio.duration<segment.duration-.12)throw new Error('配乐解码不完整');return audio;
    }).catch(error=>{if(this.cache.get(key)===promise)this.cache.delete(key);throw error;});
    this.cache.set(key,promise);while(this.cache.size>3)this.cache.delete(this.cache.keys().next().value);return promise;
  }
  preload(id){return this.tracks[id]?this.buffer(id,0):Promise.resolve(null);}
  async play(id,{fade=1.8,delay=.25}={}){
    this.stop(.7);const token=this.generation,track=this.tracks[id];if(!track)return false;
    try{
      const first=await this.buffer(id,0);if(token!==this.generation)return false;
      const bus=this.ctx.createGain(),start=this.ctx.currentTime+.03+delay;bus.gain.value=0;bus.connect(this.output);bus.gain.setValueAtTime(0,start);bus.gain.linearRampToValueAtTime(1,start+fade);
      const active={id,track,token,bus,start,nodes:new Set(),next:1,pending:false,retryAt:0,cancelled:false};this.active=active;this.schedule(active,0,first);this.onState({id,state:'playing',segment:0});this.tick();return true;
    }catch(error){if(token===this.generation)this.onState({id,state:'error',error:String(error)});console.warn('Scene music:',error);return false;}
  }
  schedule(active,index,buffer){
    if(this.active!==active||active.cancelled)return;
    const segment=active.track.segments[index],planned=active.start+segment.start,now=this.ctx.currentTime,when=Math.max(now+.01,planned),offset=Math.max(0,when-planned),length=Math.min(buffer.duration,segment.duration);
    if(offset>=length)return;
    const source=this.ctx.createBufferSource(),gain=this.ctx.createGain(),overlap=active.track.overlap;
    source.buffer=buffer;source.connect(gain).connect(active.bus);active.nodes.add(source);
    const initial=index===0?1:Math.min(1,offset/overlap);gain.gain.setValueAtTime(initial,when);
    if(index>0&&offset<overlap)gain.gain.linearRampToValueAtTime(1,planned+overlap);
    const end=planned+length,last=index===active.track.segments.length-1,fadeStart=Math.max(when,end-(last?1.8:overlap));gain.gain.setValueAtTime(1,fadeStart);gain.gain.linearRampToValueAtTime(0,end);
    source.start(when,offset);source.stop(end);source.onended=()=>{active.nodes.delete(source);source.disconnect();gain.disconnect();};
  }
  tick(){
    const active=this.active;if(!active||active.cancelled||this.ctx.state==='suspended')return;
    const elapsed=this.ctx.currentTime-active.start;if(elapsed>active.track.duration+.15){this.stop(.5);this.onState({id:active.id,state:'ended'});return;}
    const index=active.next,segment=active.track.segments[index];
    if(!segment||active.pending||this.ctx.currentTime<active.retryAt||segment.start>elapsed+50)return;
    active.pending=true;this.buffer(active.id,index).then(buffer=>{
      if(this.active!==active||active.cancelled)return;this.schedule(active,index,buffer);active.next=index+1;this.onState({id:active.id,state:'scheduled',segment:index});
    }).catch(error=>{if(this.active===active){active.retryAt=this.ctx.currentTime+4;console.warn('Scene music segment:',error);this.onState({id:active.id,state:'error',error:String(error)});}}).finally(()=>active.pending=false);
  }
  stop(fade=.7){
    this.generation++;const active=this.active;this.active=null;if(!active)return;
    active.cancelled=true;const now=this.ctx.currentTime;hold(active.bus.gain,now);active.bus.gain.setTargetAtTime(0,now,Math.max(.01,fade/4));
    for(const node of active.nodes){try{node.stop(now+fade+.05);}catch{}}
    setTimeout(()=>active.bus.disconnect(),(fade+.1)*1000);this.onState({id:active.id,state:'stopped'});
  }
}
