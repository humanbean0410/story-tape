import { z } from 'zod';
import type { PrevisProject, PrevisScene } from './previs-model';
export const MODEL_SERVICES = [
 {id:'openai',name:'OpenAI',label:'理解参考 · 提出镜头方案',tasks:['reference','shots'],docs:'https://developers.openai.com/api/reference/responses/overview',secretName:'OPENAI_API_KEY'},
 {id:'meshy',name:'Meshy',label:'生成单个三维道具',tasks:['asset'],docs:'https://docs.meshy.ai/en/api/multi-image-to-3d',secretName:'MESHY_API_KEY'},
 {id:'runway',name:'Runway',label:'生成视觉演绎候选',tasks:['look'],docs:'https://docs.dev.runwayml.com/api/',secretName:'RUNWAY_API_KEY'},
] as const;
export const MODEL_TASKS = [
 {id:'reference',title:'理解参考',detail:'整理图片中的构件、光线与需要补充的信息。',output:'参考分析与场景草案'},
 {id:'shots',title:'镜头建议',detail:'围绕当前场景意图，准备景别、机位与节奏建议。',output:'镜头方案候选'},
 {id:'asset',title:'补充道具',detail:'为当前场景准备一个独立道具的生成任务。',output:'单个三维资产候选'},
 {id:'look',title:'视觉演绎',detail:'以场景画面作为参考，准备风格或运动候选。',output:'视觉候选片段'},
] as const;
export const ModelOptionSchema=z.object({provider:z.enum(['openai','meshy','runway']),task:z.enum(['reference','shots','asset','look']),instruction:z.string().max(1200).default(''),style:z.enum(['realistic','simple','cinematic']).default('cinematic'),preserveCamera:z.boolean().default(true)}).superRefine((value,ctx)=>{const service=MODEL_SERVICES.find(s=>s.id===value.provider)!;if(!service.tasks.some(t=>t===value.task))ctx.addIssue({code:'custom',message:'这个服务不支持所选任务'});});
export type ModelOption=z.infer<typeof ModelOptionSchema>;
export const ModelStatusListSchema=z.array(z.object({provider:z.enum(['openai','meshy','runway']),credentialConfigured:z.boolean(),status:z.enum(['not_connected','configuration_pending'])}));
export type ModelStatus=z.infer<typeof ModelStatusListSchema>[number];
export function modelStatuses(env:Record<string,unknown>):ModelStatus[]{return MODEL_SERVICES.map(service=>{const configured=typeof env[service.secretName]==='string'&&!!(env[service.secretName] as string).trim();return {provider:service.id,credentialConfigured:configured,status:configured?'configuration_pending':'not_connected'};});}
export function prepareModelTask(option:ModelOption,project:PrevisProject,scene:PrevisScene){
 const parsed=ModelOptionSchema.parse(option),task=MODEL_TASKS.find(t=>t.id===parsed.task)!;
 const references=scene.references.filter(r=>r.accepted).map(r=>({name:r.name,role:r.role,note:r.note,width:r.width,height:r.height}));
 const prompt=['项目：'+project.title,'目标：'+project.goal,'场景：'+scene.title,'拍摄意图：'+scene.brief,'需要保留：'+scene.mustKeep,'待确认：'+scene.unknowns,'任务：'+task.title,'补充要求：'+parsed.instruction,'视觉方向：'+({realistic:'真实材质与比例',simple:'简洁、便于前期预演',cinematic:'电影构图与光线'}[parsed.style]),parsed.preserveCamera?'保留现有机位与镜头参数；需要变更时，单独说明原因。':'可以提出不同机位，但保留当前空间关系。',parsed.task==='asset'?'仅生成一个独立物体，不生成整个场景。':'请区分观察到的信息、推断和设计建议；不要把缺失尺寸当成测量结果。','输出：'+task.output].join('\n');
 return {version:1,status:'prepared',provider:parsed.provider,task:parsed.task,options:parsed,prompt,input:{projectTitle:project.title,scene:scene.title,brief:scene.brief,mustKeep:scene.mustKeep,unknowns:scene.unknowns,references,shots:scene.shots},output:task.output,notice:'这是一份待调用的任务说明。未执行模型请求，也不包含素材原文件或密钥。'};
}
