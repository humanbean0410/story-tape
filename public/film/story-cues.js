import { SCRIPT } from './script-book.js?v=20261013-score-r4';

// Keep each exchange in one composition; object/action beats motivate camera changes.
export const DIRECTION={
  casa:[[0,'master'],[1,'window'],[4,'bench','paper'],[12,'window'],[13,'bench'],[17,'door','door']],
  station:[[0,'master'],[1,'axis'],[4,'reverse','paper'],[12,'passing','arrival'],[17,'seats'],[19,'seat-detail']],
  interior:[[0,'master'],[1,'two-shot'],[4,'man','cup'],[9,'detail'],[10,'two-shot'],[16,'detail'],[21,'window']],
  diner:[[0,'master','phone'],[1,'table'],[4,'two-shot'],[11,'jukebox','jukebox'],[12,'two-shot'],[18,'table','paper'],[22,'master']],
  alley:[[0,'master','steps'],[1,'two-shot'],[4,'close'],[9,'flowers','paper'],[10,'profile'],[18,'street']],
  courtyard:[[0,'master'],[2,'pine'],[4,'path','steps'],[9,'door','wood-door'],[10,'corridor','paper'],[14,'lantern'],[15,'corridor'],[19,'window']]
};
const action=who=>['动作','结尾'].includes(who);
export function buildTimeline(id){
  const scene=SCRIPT.scenes.find(s=>s.id===id);let time=0,shot='master';
  return scene.lines.map(([who,text],index)=>{const cue=DIRECTION[id].find(c=>c[0]===index);if(cue)shot=cue[1];const duration=cue?.[2]==='arrival'?14500:action(who)?Math.min(9000,4500+text.length*35):Math.max(3000,Math.min(11000,1800+text.length*165));const beat={index,start:time,end:time+duration,who,text,shot,sound:cue?.[2],dialogue:!action(who)};time+=duration+350;return beat;});
}
export class StoryPlayback{
  constructor({shot,sound,subtitle,ended}){Object.assign(this,{shot,sound,subtitle,ended});this.manual=false;this.stop();}
  start(id,now){this.id=id;this.timeline=buildTimeline(id);this.elapsed=-4200;this.last=now;this.index=-1;this.finished=false;this.manual=false;this.active=true;this.lastShot=null;this.subtitle(null);}
  stop(){this.active=false;this.subtitle?.(null);}
  follow(){this.manual=false;if(this.current)this.shot(this.current.shot);}
  update(now,paused=false){
    if(!this.active)return;const dt=Math.max(0,Math.min(250,now-this.last));this.last=now;if(paused)return;this.elapsed+=dt;
    const beat=this.timeline.find(b=>this.elapsed>=b.start&&this.elapsed<b.end);
    if(!beat){this.subtitle(null);if(!this.finished&&this.elapsed>=this.timeline.at(-1).end){this.finished=true;this.ended(this.id);}return;}
    if(beat.index===this.index)return;this.index=beat.index;this.current=beat;
    if(beat.shot!==this.lastShot){this.lastShot=beat.shot;if(!this.manual)this.shot(beat.shot);}
    if(beat.sound)this.sound(beat.sound);this.subtitle(beat.dialogue?beat:null);
  }
}
