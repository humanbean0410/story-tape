import type { PrevisScene } from './previs-model';
import { loadMedia } from './previs-media';
declare global {interface Window {__previsAudioStream?:MediaStream}}
export class PrevisAudio {
 ctx:AudioContext|null=null; destination:MediaStreamAudioDestinationNode|null=null;
 buffers=new Map<string,AudioBuffer>();nodes:AudioBufferSourceNode[]=[];
 active='';base=0;muted=false;master:GainNode|null=null;
 async prepare(scenes:PrevisScene[]){
  this.ctx??=new AudioContext();await this.ctx.resume();
  if(!this.master){this.master=this.ctx.createGain();this.master.gain.value=.65;this.master.connect(this.ctx.destination);this.destination=this.ctx.createMediaStreamDestination();this.master.connect(this.destination);window.__previsAudioStream=this.destination.stream;}
  for(const scene of scenes)for(const track of scene.tracks){if(this.buffers.has(track.referenceId))continue;const b=await loadMedia(track.referenceId);if(!b)throw Error('声音素材未在本浏览器找到，请重新导入原文件。');this.buffers.set(track.referenceId,await this.ctx.decodeAudioData(await b.arrayBuffer()));}
 }
 sync(scene:PrevisScene|undefined,elapsed:number,playing:boolean){
  if(!this.ctx||!scene)return;if(!playing){this.stop();return;}
  if(this.active===scene.id&&Math.abs((this.ctx.currentTime-this.base)-elapsed)<.5)return;
  this.stop();this.active=scene.id;const now=this.ctx.currentTime;this.base=now-elapsed;
  for(const track of scene.tracks){const buffer=this.buffers.get(track.referenceId);if(!buffer)continue;
   const inPoint=Math.min(track.in,buffer.duration),out=Math.min(track.out,buffer.duration),span=out-inPoint;
   if(span<=0)continue;const already=Math.max(0,elapsed-track.start);if(!track.loop&&already>=span)continue;
   const delay=Math.max(0,track.start-elapsed),at=now+delay;
   const node=this.ctx.createBufferSource(),gain=this.ctx.createGain();node.buffer=buffer;node.loop=track.loop;node.loopStart=inPoint;node.loopEnd=out;node.connect(gain).connect(this.master!);
   const offset=inPoint+(track.loop?already%span:already),remaining=span-already;
   const fade=Math.min(track.fade,span/2);
   const level=track.gain;
   if(already<fade&&fade>0){gain.gain.setValueAtTime(level*already/fade,at);gain.gain.linearRampToValueAtTime(level,at+fade-already);}else gain.gain.setValueAtTime(level,at);
   if(!track.loop){const tail=at+remaining;if(fade>0){gain.gain.setValueAtTime(level,Math.max(at,tail-fade));gain.gain.linearRampToValueAtTime(0,tail);}node.start(at,offset,Math.max(.01,remaining));}else node.start(at,offset);
   this.nodes.push(node);node.onended=()=>gain.disconnect();
  }
 }
 stop(){this.nodes.forEach(n=>{try{n.stop();n.disconnect();}catch{}});this.nodes=[];this.active='';}
 dispose(){this.stop();this.ctx?.close();delete window.__previsAudioStream;this.ctx=null;this.buffers.clear();}
}
