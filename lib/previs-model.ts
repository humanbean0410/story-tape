import { z } from 'zod';
import { SCENES } from './scene-catalog';
import { SceneId } from './story-model';

const Vec = z.tuple([z.number().min(-12).max(12), z.number().min(-12).max(12), z.number().min(-12).max(12)]);
export const PrevisShotSchema = z.object({
  id:z.string().min(1).max(80), name:z.string().min(1).max(80), preset:z.string().max(40),
  intent:z.string().max(500).default(''), text:z.string().max(600).default(''),
  seconds:z.number().min(2).max(30), focal:z.number().min(18).max(135),
  aperture:z.number().min(1.4).max(16), focus:z.number().min(.1).max(80).nullable().default(null),
  aspect:z.enum(['2.39','1.85','1.7778','1','0.5625']), light:z.number().min(0).max(1),
  startOffset:Vec, endOffset:Vec, targetOffset:Vec,
  movement:z.enum(['hold','push','pull','truck','custom']), easing:z.enum(['linear','smooth']),
  trainAt:z.number().min(0).max(30).nullable().default(null),
});
export const ReferenceSchema=z.object({id:z.string().max(80),name:z.string().max(200),
  role:z.enum(['space','material','light','mood','sound','voice']),
  type:z.string().max(100),width:z.number().optional(),height:z.number().optional(),seconds:z.number().optional(),
  note:z.string().max(500).default(''),accepted:z.boolean().default(true)});
export const AudioTrackSchema=z.object({id:z.string().max(80),referenceId:z.string().max(80),
  layer:z.enum(['music','ambience','voice','effect']),start:z.number().min(0).max(3600),
  in:z.number().min(0).max(3600),out:z.number().min(.01).max(3600),
  gain:z.number().min(0).max(1),fade:z.number().min(0).max(10),loop:z.boolean(),
}).refine(t=>t.out>t.in,{message:'音频出点需大于入点'});
export const PrevisSceneSchema=z.object({id:z.string().min(1).max(80),scene:SceneId,title:z.string().min(1).max(80),
  brief:z.string().max(1200),mustKeep:z.string().max(800),unknowns:z.string().max(800),
  medium:z.enum(['3d','image','video']),review:z.enum(['draft','review','approved']),
  references:z.array(ReferenceSchema).max(30),tracks:z.array(AudioTrackSchema).max(8),
  shots:z.array(PrevisShotSchema).min(1).max(12)}).superRefine((scene,ctx)=>{
   const available=SCENES.find(s=>s.id===scene.scene)!.shots;
   scene.shots.forEach((shot,i)=>{if(!available.some(s=>s.id===shot.preset))ctx.addIssue({code:'custom',path:['shots',i,'preset'],message:'机位不属于该布景'});});
   if(new Set(scene.shots.map(s=>s.id)).size!==scene.shots.length)ctx.addIssue({code:'custom',path:['shots'],message:'镜头ID重复'});
 });
export const PrevisProjectSchema=z.object({version:z.literal(2),title:z.string().min(1).max(100),
  goal:z.string().max(1200),mode:z.enum(['guided','director']),scenes:z.array(PrevisSceneSchema).min(1).max(6)});
export type PrevisShot=z.infer<typeof PrevisShotSchema>;
export type PrevisScene=z.infer<typeof PrevisSceneSchema>;
export type PrevisProject=z.infer<typeof PrevisProjectSchema>;
export type PrevisReference=z.infer<typeof ReferenceSchema>;
export type PrevisTrack=z.infer<typeof AudioTrackSchema>;
export const previsId=()=>crypto.randomUUID();
export function makePrevisShot(scene:PrevisScene['scene'],preset='master'):PrevisShot {
  const s=SCENES.find(x=>x.id===scene)!;const p=s.shots.find(x=>x.id===preset)||s.shots[0];
  return{id:previsId(),name:p.name,preset:p.id,intent:'这个镜头需要让观众看见什么？',text:'',seconds:6,
    focal:p.focal,aperture:8,focus:null,aspect:'2.39',light:scene==='station'?.28:scene==='courtyard'?.82:1,
    startOffset:[0,0,0],endOffset:[0,0,0],targetOffset:[0,0,0],movement:'hold',easing:'smooth',trainAt:null};
}
export function makePrevisScene(scene:PrevisScene['scene']='interior'):PrevisScene {
  const s=SCENES.find(x=>x.id===scene)!;
  const presets:Record<PrevisScene['scene'],string[]>= {casa:['master','window','bench'],station:['master','passing','seat-detail'],interior:['master','two-shot','detail'],courtyard:['master','path','window'],diner:['master','two-shot','table'],alley:['master','two-shot','flowers']};
  const shots=presets[scene].map(p=>makePrevisShot(scene,p));
  shots[0].movement='push';shots[0].endOffset=[0,0,-.85];shots[0].intent='缓慢靠近，建立这一场的空间关系。';
  if(scene==='station'){shots[1].trainAt=1;shots[1].seconds=15;shots[1].intent='列车遮挡后重新看见空站台；进站提示只在这一事件前响一次。';}
  return{id:previsId(),scene,title:s.name,brief:scene==='interior'?'两个人在黄昏的窗边休息、聊天。先确认空间，再试靠近与道具镜头。':'确认空间关系，再用镜头顺序表达这一场的拍摄意图。',mustKeep:'保持布景、道具与镜头间空间关系一致；当前以空座位和物件预留人物位置。',unknowns:'实景尺寸未经测量；人物表演、接触动作与最终光照需另行验证。',medium:'3d',review:'draft',references:[],tracks:[],shots};
}
export const makePrevisProject=(scene:PrevisScene['scene']='interior'):PrevisProject=>({version:2,title:'我的场景预演',goal:'用场景方案、效果帧与动态分镜确认空间、构图和节奏。',mode:'director',scenes:[makePrevisScene(scene)]});
export const MOVEMENT_LABELS={hold:'固定',push:'推进',pull:'拉远',truck:'横移',custom:'自定义'} as const;
export type PlaybackScope='shot'|'scene'|'project';
export function movementOffsets(movement:PrevisShot['movement'],start:PrevisShot['startOffset']=[0,0,0]):PrevisShot['endOffset'] {
  const delta=movement==='push'?[0,0,-1.2]:movement==='pull'?[0,0,1.2]:movement==='truck'?[1.2,0,0]:[0,0,0];
  return start.map((n,i)=>Math.max(-12,Math.min(12,n+delta[i]))) as PrevisShot['endOffset'];
}
export function previsSequence(project:PrevisProject,sceneId:string,shotId:string,scope:PlaybackScope){
  return project.scenes.filter(s=>scope==='project'||s.id===sceneId).flatMap(s=>{
    let sceneOffset=0;
    return s.shots.flatMap(shot=>{const item={scene:s.scene,sceneId:s.id,shot,sceneOffset};sceneOffset+=shot.seconds;return scope!=='shot'||shot.id===shotId?[item]:[];});
  });
}
export function scenePlanMarkdown(project:PrevisProject):string {
  const rows=['# '+project.title,'',project.goal,'','交付状态：预演方案；模型尺寸未经实景测量，画面是现有 Blender 布景的浏览器渲染。',''];
  project.scenes.forEach((s,i)=>{rows.push(`## ${i+1}. ${s.title}`,s.brief,'',`表达方式：${s.medium}；审核：${s.review}`,`保留约束：${s.mustKeep}`,`待确认：${s.unknowns}`,'','### 参考素材');s.references.forEach(r=>rows.push(`- ${r.name}｜用途 ${r.role}｜${r.accepted?'采用':'弃用'}｜${r.note}`));rows.push('','### 镜头表','|镜头|拍摄意图|焦距 / 画幅|时长|运动 / 机位偏移|声音事件|','|---|---|---|---|---|---|');s.shots.forEach(sh=>rows.push(`|${sh.name.replaceAll('|','/')}|${sh.intent.replaceAll('|','/').replaceAll('\n',' ')}|${sh.focal}mm / ${sh.aspect}|${sh.seconds}s|${sh.movement} / ${sh.startOffset} → ${sh.endOffset}|${sh.trainAt===null?'—':`列车预警 ${sh.trainAt}s；2.3s 后过站`}|`));rows.push('','### 声音表');s.tracks.forEach(t=>rows.push(`- ${t.layer}｜素材 ${s.references.find(r=>r.id===t.referenceId)?.name||t.referenceId}｜时间线 ${t.start}s｜片段 ${t.in}–${t.out}s｜增益 ${t.gain}｜淡入淡出 ${t.fade}s｜${t.loop?'循环':'一次'}`));rows.push('');});rows.push('JSON 保留全部镜头参数；本地音频/图片文件需另行保管。动态分镜导出为浏览器 WebM 预演，不是最终实拍或 AI 视频。');return rows.join('\n');
}
