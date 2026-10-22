'use client';
import { useState } from 'react';
import { ArrowUpRight, ArrowRight } from 'lucide-react';
const SETS = [
  {id:'casa',name:'街角店铺',en:'THE CORNER SHOP',time:'午后 / 外景',mood:'橱窗、长椅，与一场约会的起点。'},
  {id:'station',name:'山间站台',en:'A SMALL STATION',time:'春日 / 外景',mood:'等一班列车，试一段关于等待的镜头。'},
  {id:'interior',name:'黄昏窗边',en:'DUSK BY THE WINDOW',time:'黄昏 / 内景',mood:'窗光慢下来，谈话可以再久一点。'},
  {id:'courtyard',name:'松下庭院',en:'UNDER THE PINE',time:'秋日 / 庭院',mood:'沿着石径走近，让门窗成为画框。'},
  {id:'diner',name:'复古餐馆',en:'TABLE FOR TWO',time:'傍晚 / 内景',mood:'一张餐桌，几种靠近彼此的方式。'},
  {id:'alley',name:'蓝调夜巷',en:'AFTER THE LAST LIGHT',time:'蓝调时刻 / 外景',mood:'把最后一个镜头，留给街角的灯。'},
] as const;
export default function HomeShowcase(){
  const [selected,setSelected]=useState(2),[reference,setReference]=useState(false);const scene=SETS[selected];
  return <section className="st-showcase" id="scenes" aria-label="探索六个拍摄场景">
    <div className="st-screen-heading"><span><i/>场景放映室 <b>/</b> 06 SETS</span><div role="group" aria-label="展示内容"><button aria-pressed={!reference} onClick={()=>setReference(false)}>三维布景</button><button aria-pressed={reference} onClick={()=>setReference(true)}>实景参考</button></div></div>
    <div className={`st-screen ${reference?'is-reference':''}`}>
      <img key={`${scene.id}-${reference}`} src={`/${reference?'references':'scene-thumbs'}/${scene.id}.webp`} alt={`${scene.name} · ${reference?'实景参考照片':'手工搭建的三维布景渲染'}`} fetchPriority="high" width={1100} height={629}/>
      <div className="st-screen-top"><span>{String(selected+1).padStart(2,'0')} / {scene.en}</span><span>{reference?'REFERENCE PHOTOGRAPH':'3D SET / PREVIS STILL'}</span></div>
      <div className="st-screen-bottom" aria-live="polite"><div><span>{scene.time}</span><h2>{scene.name}</h2><p>{scene.mood}</p></div><a href={`/previs?scene=${scene.id}`} aria-label={`用${scene.name}开始试拍`}><span>在这里试拍</span><ArrowUpRight size={24}/></a></div>
    </div>
    <div className="st-scene-strip" role="group" aria-label="选择场景">{SETS.map((s,i)=><button key={s.id} aria-label={`查看${s.name}`} aria-pressed={selected===i} className={selected===i?'selected':''} onClick={()=>setSelected(i)}><img src={`/scene-thumbs/${s.id}.webp`} alt="" loading="lazy" width={160} height={96}/><span><small>{String(i+1).padStart(2,'0')}</small><strong>{s.name}</strong></span><ArrowRight size={13}/></button>)}</div>
    <div className="st-showcase-note"><span>实景提供灵感，三维布景让镜头可以反复尝试。</span><a href="/capabilities">看看场景如何搭建 <ArrowUpRight size={13}/></a></div>
  </section>;
}
