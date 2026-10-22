'use client';
import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Play, Pause, Square, Film, MoveRight, Download, Plus, Upload, Camera, Undo2, Trash2, ChevronUp, ChevronDown, Sparkles, CircleHelp, Check, RefreshCw } from 'lucide-react';
import { SCENES } from '@/lib/scene-catalog';
import { PrevisProjectSchema, makePrevisProject, makePrevisScene, makePrevisShot, movementOffsets, MOVEMENT_LABELS, previsSequence, type PlaybackScope, scenePlanMarkdown, previsId, type PrevisProject, type PrevisScene, type PrevisShot } from '@/lib/previs-model';
import { importMedia, loadMedia } from '@/lib/previs-media';
import { PrevisAudio } from '@/lib/previs-audio';
import StudioOnboarding, { STUDIO_STEPS, type StudioStep } from './studio-onboarding';
import ModelOptionsPanel from './model-options-panel';
import type { ModelOption } from '@/lib/model-options';
const KEY = 'story-tape:previs:v2';
const clone = <T,>(v: T): T => JSON.parse(JSON.stringify(v));
const download = (value: Blob | string, name: string) => { const url = typeof value === 'string' ? value : URL.createObjectURL(value); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); if (typeof value !== 'string')
    setTimeout(() => URL.revokeObjectURL(url), 5000); };
type Frame = {
    url: string;
    shot: PrevisShot;
    scene: string;
    label: string;
    width: number;
    height: number;
};
type RuntimeState = {
    status: string;
    canResume?: boolean;
    sceneId?: string;
    shotId?: string;
    elapsed?: number;
    sceneElapsed?: number;
    totalElapsed?: number;
};
export default function PrevisStudio() {
    const [project, setProject] = useState<PrevisProject | null>(null), [sceneId, setSceneId] = useState(''), [shotId, setShotId] = useState(''), [step, setStep] = useState<StudioStep>('plan');
    const [ready, setReady] = useState(false), [status, setStatus] = useState('正在连接预演布景…'), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false), [runtime, setRuntime] = useState<RuntimeState>({ status: 'loading' }), [frames, setFrames] = useState<Frame[]>([]), [urls, setUrls] = useState<Record<string, string>>({}), [reload, setReload] = useState(0), [canRecord, setCanRecord] = useState(false), [wideView, setWideView] = useState(false), [videoOutput, setVideoOutput] = useState<string | null>(null);
    const [playScope,setPlayScope]=useState<PlaybackScope>('scene'),[scrub,setScrub]=useState(0);
    const [guide,setGuide]=useState(false),[modelPanel,setModelPanel]=useState(false),[modelTask,setModelTask]=useState<ModelOption['task']>('reference'),[usageGoal,setUsageGoal]=useState<'plan'|'frame'|'film'>('frame'),[stageError,setStageError]=useState(false),[saveState,setSaveState]=useState<'saving'|'saved'|'invalid'|'error'>('saving');
    const iframe = useRef<HTMLIFrameElement>(null), input = useRef<HTMLInputElement>(null), jsonInput = useRef<HTMLInputElement>(null), audio = useRef<PrevisAudio | null>(null), projectRef = useRef(project), history = useRef<PrevisProject[]>([]), captureRef = useRef<{
        shot: PrevisShot;
        scene: string;
        label: string;
    } | null>(null), recordingRef = useRef(false), storageKey = useRef(KEY);
    const scene = project?.scenes.find(s => s.id === sceneId) || project?.scenes[0];
    const shot = scene?.shots.find(s => s.id === shotId) || scene?.shots[0];
    const playing = runtime.status === 'playing';
    const paused = runtime.status === 'paused' && !!runtime.canResume;
    const loading = runtime.status === 'loading';
    useEffect(() => { projectRef.current = project; }, [project]);
    const send = (message: object) => iframe.current?.contentWindow?.postMessage(message, location.origin);
    const show = (s: PrevisScene, sh: PrevisShot) => {setScrub(0);send({ type: 'previs:shot', scene: s.scene, sceneId: s.id, shot: sh });};
    function commit(next: PrevisProject) { if (project) {
        history.current.push(clone(project));
        if (history.current.length > 30)
            history.current.shift();
    } setProject(next); }
    const patchScene = (value: Partial<PrevisScene>) => project && scene && commit({ ...project, scenes: project.scenes.map(s => s.id === scene.id ? { ...s, ...value } : s) });
    const patchShot = (value: Partial<PrevisShot>) => scene && shot && patchScene({ shots: scene.shots.map(s => s.id === shot.id ? { ...s, ...value } : s) });
    useEffect(() => { const chosen = new URLSearchParams(location.search).get('scene'); const valid = SCENES.some(s => s.id === chosen); storageKey.current = valid ? `${KEY}:case:${chosen}` : KEY; let p: PrevisProject; try {
        const raw = localStorage.getItem(storageKey.current);
        p = raw ? PrevisProjectSchema.parse(JSON.parse(raw)) : makePrevisProject(valid ? chosen as PrevisScene['scene'] : 'interior');
    }
    catch {
        p = makePrevisProject();
        setNotice('旧方案无法读取，已新建本地方案。');
    } try{setGuide(!localStorage.getItem('story-tape:guide:v1')||new URLSearchParams(location.search).has('guide'));const goal=localStorage.getItem('story-tape:usage-goal');if(goal==='plan'||goal==='frame'||goal==='film')setUsageGoal(goal);}catch{setGuide(true);} setProject(p); setSceneId(p.scenes[0].id); setShotId(p.scenes[0].shots[0].id); audio.current = new PrevisAudio(); setCanRecord(typeof MediaRecorder !== 'undefined' && ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'].some(t => MediaRecorder.isTypeSupported(t))); return () => audio.current?.dispose(); }, []);
    useEffect(() => { if(!project)return;if(!PrevisProjectSchema.safeParse(project).success){setSaveState('invalid');return;}setSaveState('saving');const timer = setTimeout(() => { try {
        localStorage.setItem(storageKey.current, JSON.stringify(project));setSaveState('saved');
    }
    catch {
        setSaveState('error');setNotice('本地保存空间不足，请导出 JSON 备份。');
    } }, 250); return () => clearTimeout(timer); }, [project]);
    useEffect(() => { if (!scene || !shot || !ready || playing || recordingRef.current)
        return; const timer = setTimeout(() => show(scene, shot), 180); return () => clearTimeout(timer); }, [scene?.id, shot, ready, reload]);
    useEffect(() => {
        const handler = (e: MessageEvent) => {
            if (e.origin !== location.origin || e.source !== iframe.current?.contentWindow)
                return;
            const m = e.data;
            if (m.type === 'previs:ready') { setStageError(false);
                setReady(true);
                if (m.handshake) {
                    const p = projectRef.current;
                    const s = p?.scenes.find(s => s.id === sceneId) || p?.scenes[0];
                    if (s)
                        show(s, s.shots.find(sh => sh.id === shotId) || s.shots[0]);
                }
                else
                    setStatus('布景已就位 · 修改镜头参数即可比较');
            }
            if (m.type === 'previs:state') {
                setRuntime(m);
                setScrub(Math.max(0, Math.min(1, Number(m.elapsed||0)/(projectRef.current?.scenes.find(s=>s.id===m.sceneId)?.shots.find(sh=>sh.id===m.shotId)?.seconds||1))));
                if ((m.status === 'playing' || m.status === 'done') && m.sceneId && m.shotId) {
                    setSceneId(m.sceneId);
                    setShotId(m.shotId);
                }
                setStatus(m.status === 'loading' ? '布景正在加载，声音与时间线暂停…' : m.status === 'playing' ? `预演 ${Number(m.totalElapsed || 0).toFixed(1)}s · 当前镜头 ${Number(m.elapsed || 0).toFixed(1)}s` : m.status === 'done' ? '预演结束 · 可修改镜头再比较' : '布景已就位');
                const s = projectRef.current?.scenes.find(s => s.id === m.sceneId);
                audio.current?.sync(s, m.sceneElapsed || 0, m.status === 'playing');
            }
            if (m.type === 'previs:frame' && captureRef.current) {
                const f = { ...captureRef.current, url: m.dataUrl, width: m.width, height: m.height };
                setFrames(list => [...list.slice(-3), f]);
                download(m.dataUrl, `${f.label}-${f.shot.name}.png`);
                captureRef.current = null;
                setBusy(false);
                setNotice('真实效果帧已生成，可在交付页对比参数或保存文件。');
            }
            if (m.type === 'previs:video') {
                const url = URL.createObjectURL(m.blob);
                setVideoOutput(old => { if (old)
                    URL.revokeObjectURL(old); return url; });
                download(m.blob, '动态分镜.webm');
                recordingRef.current = false;
                setBusy(false);
                setNotice('动态分镜已生成，可在交付页播放或保存文件。');
            }
            if (m.type === 'previs:error') { setStageError(true);
                setNotice(m.message);
                setBusy(false);
                recordingRef.current = false;
                audio.current?.stop();
                setRuntime({ status: 'paused' });
                setStatus('预演失败，可重载后重试。');
            }
        };
        addEventListener('message', handler);
        return () => removeEventListener('message', handler);
    }, [sceneId, shotId]);
    useEffect(() => { let disposed = false; const created: string[] = []; if (!scene)
        return; Promise.all(scene.references.map(async (r) => { try {
        const b = await loadMedia(r.id);
        if (!b)
            return null;
        const url = URL.createObjectURL(b);
        created.push(url);
        return [r.id, url] as const;
    }
    catch {
        return null;
    } })).then(rows => { if (!disposed)
        setUrls(Object.fromEntries(rows.filter(r => r !== null))); }); return () => { disposed = true; created.forEach(url => URL.revokeObjectURL(url)); }; }, [scene?.references]);
    async function addFiles(files: FileList | null) { if (!files || !scene)
        return; setBusy(true); try {
        const refs = [...scene.references];
        for (const file of Array.from(files)) {
            if (refs.length >= 30)
                throw Error('每个场景最多 30 份参考。');
            if (refs.some(r => r.name === file.name))
                setNotice('存在同名素材，请确认是否重复。');
            refs.push(await importMedia(file));
        }
        patchScene({ references: refs });
        setNotice('素材已存入本浏览器，标注用途后加入方案。图片不会自动替换三维布景。');
    }
    catch (e) {
        setNotice((e as Error).message);
    }
    finally {
        setBusy(false);
        if (input.current)
            input.current.value = '';
    } }
    async function importJSON(file: File | undefined) { if (!file)
        return; try {
        if (file.size > 1024 * 1024)
            throw Error('工程 JSON 超过 1 MiB。');
        const p = PrevisProjectSchema.parse(JSON.parse(await file.text()));
        commit(p);
        setSceneId(p.scenes[0].id);
        setShotId(p.scenes[0].shots[0].id);
        setNotice('工程已导入。JSON 不含素材文件，跨浏览器使用时请重新导入声音并绑定。');
    }
    catch {
        setNotice('工程格式不正确，请使用这个工作台导出的 JSON。');
    } if (jsonInput.current)
        jsonInput.current.value = ''; }
    async function play(scope:PlaybackScope = playScope, record = false) { if (!project || !scene || !ready)
        return; setPlayScope(scope);setWideView(false); const scenes = scope==='project' ? project.scenes : [scene], items = previsSequence(project,scene.id,shot!.id,scope); if (record && items.reduce((n, i) => n + i.shot.seconds, 0) > 180) {
        setNotice('单次动态分镜导出不超过 180 秒，请减少镜头或导出本场。');
        return;
    } setBusy(true); try {
        await audio.current?.prepare(scenes);
        recordingRef.current = record;
        send({ type: record ? 'previs:record' : 'previs:play', items, requestId: previsId() });
        if (!record)
            setBusy(false);
    }
    catch (e) {
        setBusy(false);
        setNotice((e as Error).message);
    } }
    function stop() { send({ type: 'previs:stop' }); audio.current?.stop(); recordingRef.current = false; setBusy(false); }
    function seek(progress:number){if(!scene||!shot||!ready)return;audio.current?.stop();setWideView(false);setScrub(progress);send({type:'previs:seek',scene:scene.scene,sceneId:scene.id,shot,progress});}
    function changeMovement(movement:PrevisShot['movement']){if(!shot)return;setScrub(0);patchShot({movement,endOffset:movement==='custom'?shot.endOffset:movementOffsets(movement,shot.startOffset)});}
    function addGentleMotion(){if(!scene)return;const first=scene.shots[0];patchScene({shots:scene.shots.map(s=>s.id===first.id?{...s,movement:'push',endOffset:movementOffsets('push',s.startOffset)}:s)});setShotId(first.id);setStep('shots');setNotice('首镜头已设为推进，可拖动进度查看起止构图。');}

    function capture() { if (wideView) {
        setNotice('请回到电影视角再保存效果帧。');
        return;
    } if (!scene || !shot || !ready)
        return; setBusy(true); captureRef.current = { shot: clone(shot), scene: scene.title, label: `方案${String.fromCharCode(65 + frames.length % 4)}` }; send({ type: 'previs:capture', requestId: previsId() }); }
    function exportPlan(format: 'json' | 'md') { const parsed = PrevisProjectSchema.safeParse(project); if (!parsed.success) {
        setNotice('请补全项目、场景和镜头名称，并检查参数后导出。');
        return;
    } download(new Blob([format === 'json' ? JSON.stringify(parsed.data, null, 2) : scenePlanMarkdown(parsed.data)], { type: format === 'json' ? 'application/json' : 'text/markdown;charset=utf-8' }), format === 'json' ? '场景预演工程-v2.json' : '场景方案与分镜表.md'); }
    function moveShot(dir: number) { if (!scene || !shot)
        return; const list = [...scene.shots], i = list.findIndex(s => s.id === shot.id), j = i + dir; if (j < 0 || j >= list.length)
        return; [list[i], list[j]] = [list[j], list[i]]; patchScene({ shots: list }); }
    function closeGuide(){setGuide(false);try{localStorage.setItem('story-tape:guide:v1','seen');}catch{}}
    function startGuide(mode:'guided'|'director',target:StudioStep,goal:'plan'|'frame'|'film'){if(project&&mode!==project.mode)commit({...project,mode});setUsageGoal(goal);setStep(target);try{localStorage.setItem('story-tape:usage-goal',goal);}catch{}closeGuide();}
    function openModels(task:ModelOption['task']='reference'){stop();setModelTask(task);setModelPanel(true);}
    function replaceSet(id:PrevisScene['scene']){if(!project||!scene||id===scene.scene)return;stop();const template=makePrevisScene(id);patchScene({scene:id,title:template.title,shots:template.shots});setShotId(template.shots[0].id);setWideView(false);}
    const number = (key: 'focal' | 'aperture' | 'light' | 'seconds', min: number, max: number, label: string, stepValue = 1) => <label>{label}<div className="pv-range"><input aria-label={label} type="range" min={min} max={max} step={stepValue} value={shot![key]} onChange={e => patchShot({ [key]: Number(e.target.value) })}/><input aria-label={`${label}数值`} type="number" min={min} max={max} step={stepValue} value={shot![key]} onChange={e => patchShot({ [key]: Math.max(min, Math.min(max, Number(e.target.value) || min)) })}/></div></label>;
    const vector = (key: 'startOffset' | 'endOffset' | 'targetOffset', label: string) => <fieldset><legend>{label}</legend><div className="pv-vector">{['右移 X', '升高 Y', '后退 Z'].map((label, i) => <label key={label}>{label}<input type="number" aria-label={`${key}${label}`} min={-12} max={12} step={.1} value={shot![key][i]} onChange={e => { const next = [...shot![key]] as [
        number,
        number,
        number
    ]; next[i] = Math.max(-12, Math.min(12, Number(e.target.value) || 0)); patchShot({ [key]: next }); }}/></label>)}</div></fieldset>;
    if (!project || !scene || !shot)
        return <main className="pv-loading">正在恢复本地场景方案…</main>;
    const meta = SCENES.find(s => s.id === scene.scene)!;
    const stepIndex=STUDIO_STEPS.findIndex(s=>s.id===step),activeStep=STUDIO_STEPS[stepIndex];
    const sceneDuration=scene.shots.reduce((n,s)=>n+s.seconds,0);
    const sequence=previsSequence(project,scene.id,shot.id,playScope),sequenceDuration=sequence.reduce((n,i)=>n+i.shot.seconds,0);
    const progress=playing||paused||runtime.status==='done'?Math.min(1,(runtime.totalElapsed||0)/Math.max(1,sequenceDuration)):0;
    const allFixed=scene.shots.every(s=>s.movement==='hold'||s.startOffset.every((n,i)=>n===s.endOffset[i]));
    const total = project.scenes.reduce((n, s) => n + s.shots.reduce((v, sh) => v + sh.seconds, 0), 0);
    return <main className="pv-page"><header className="pv-nav"><a href="/" className="pv-brand">故事磁带<small>STORY TAPE / STUDIO</small></a><div className="pv-project-heading"><input aria-label="项目名称" value={project.title} maxLength={100} onChange={e=>commit({...project,title:e.target.value})}/><span role="status"><i className={saveState}/>{saveState==='saved'?'本机已保存':saveState==='saving'?'保存中…':saveState==='invalid'?'有未填完整项':'保存失败'} · {project.scenes.length} 场 · {total}s</span></div><nav><a href="/capabilities">场景示例</a><button aria-label="模型 API 选项" className="pv-model-trigger" onClick={()=>openModels(step==='shots'?'shots':'reference')}><Sparkles size={14}/>模型 API<span>选项</span></button><button aria-label="使用引导" className="pv-guide-trigger" onClick={()=>{stop();setGuide(true);}}><CircleHelp size={15}/><span>使用引导</span></button></nav></header>
 <nav className="pv-workflow" aria-label="创作步骤">{STUDIO_STEPS.map((item,i)=><button className={step===item.id?'active':''} aria-current={step===item.id?'step':undefined} onClick={()=>setStep(item.id)} key={item.id}><span className="pv-step-number">{String(i+1).padStart(2,'0')}</span><strong>{item.title}</strong><small>{i===1||i===3?'可选':''}</small></button>)}<span className="pv-goal-label">目标 / {usageGoal==='plan'?'场景方案':usageGoal==='frame'?'效果帧':'动态分镜'}</span></nav>
 <div className="pv-workspace"><aside className="pv-scenes"><p className="pv-eyebrow">你的场景 <span>{project.scenes.length}</span></p>{project.scenes.map((s, i) => <button className={s.id === scene.id ? 'selected' : ''} key={s.id} onClick={() => { stop(); setSceneId(s.id); setShotId(s.shots[0].id); }}><img src={SCENES.find(x => x.id === s.scene)!.image} alt=""/><span>0{i + 1}<strong>{s.title}</strong><small>{s.shots.length} 镜头 · {s.review === 'approved' ? '已确认' : '待审核'}</small></span></button>)}<label className="pv-add-scene"><Plus size={14}/>加入场景<select aria-label="加入场景" value="" disabled={project.scenes.length >= 6} onChange={e => { const s = makePrevisScene(e.target.value as PrevisScene['scene']); commit({ ...project, scenes: [...project.scenes, s] }); setSceneId(s.id); setShotId(s.shots[0].id); }}><option value="">选择现有布景…</option>{SCENES.map(s => <option value={s.id} key={s.id}>{s.name}</option>)}</select></label><p>选择一个布景开始试拍。上传的图片用于参考，不会替换三维布景。</p><a href="/capabilities">浏览场景示例 <ArrowRight size={12}/></a></aside>
 <section className="pv-main"><div className="pv-toolbar"><span><i/>实时布景 <b>/</b> {meta.place}</span><select aria-label="控制深度" value={project.mode} onChange={e => commit({ ...project, mode: e.target.value as PrevisProject['mode'] })}><option value="guided">简洁模式</option><option value="director">专业模式</option></select><button disabled={!history.current.length || busy || playing} onClick={() => { const p = history.current.pop(); if (p)
        setProject(p); }}><Undo2 size={14}/>撤销</button></div>
 <div className={`pv-viewport ${wideView?'is-wide':''}`}><iframe ref={iframe} key={reload} src="/film/previs.html" title="真实三维场景预演" allow="autoplay; fullscreen" onLoad={() => show(scene, shot)}/>{(loading||stageError) && <div className="pv-viewport-loading"><span className="spin">◌</span><p>{status}</p>{stageError&&<button onClick={()=>{setStageError(false);setReady(false);setRuntime({status:'loading'});setReload(n=>n+1);}}><RefreshCw size={13}/>重新加载</button>}</div>}<div className="pv-viewport-label"><span>{playing&&<i className="pv-rec-dot"/>}{playing?'预演中':wideView?'空间视图':'镜头预览'} <b>/</b> {meta.name}</span><span>{shot.focal}mm · {shot.aspect}:1 · f/{shot.aperture}</span></div><div className="pv-frame-caption"><span>{String(scene.shots.findIndex(s=>s.id===shot.id)+1).padStart(2,'0')}</span><strong>{shot.name}</strong><small>{MOVEMENT_LABELS[shot.movement]} · {shot.seconds}s</small></div></div>
 <div className="pv-transport">
 <div className="pv-playback-group"><button className="pv-play-primary" aria-label={playing?'暂停预演':paused?'继续预演':'开始预演'} disabled={!ready || busy || loading} onClick={() => playing?send({type:'previs:pause'}):paused?send({type:'previs:resume'}):void play()}>{playing?<Pause size={16}/>:<Play size={16}/>}</button><select aria-label="播放范围" disabled={playing||paused||busy||loading} value={playScope} onChange={e=>setPlayScope(e.target.value as PlaybackScope)}><option value="shot">当前镜头</option><option value="scene">本场连播</option><option value="project">全项目连播</option></select><button aria-label="停止预演" title="停止预演" disabled={!playing&&!paused&&!busy} onClick={stop}><Square size={13}/></button></div>
 <span className="pv-timecode">{(playing||paused||runtime.status==='done'?runtime.totalElapsed||0:0).toFixed(1)} <small>/ {sequenceDuration}s</small></span>
 <div className="pv-preview-tools"><button disabled={!ready||busy||loading||playing} onClick={capture} title="保存当前构图为 PNG"><Camera size={14}/>存效果帧</button><button disabled={!ready||busy||loading||playing} className={wideView?'active':''} onClick={()=>{stop();if(wideView){show(scene,shot);setWideView(false);}else{send({type:'previs:wide'});setWideView(true);}}}>{wideView?'返回镜头':'空间视图'}</button></div>
 </div>
 <div className="pv-sequence-progress" role="progressbar" aria-label="播放总进度" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress*100)}><i style={{width:`${progress*100}%`}}/></div>
 <div className="pv-playback-hint"><span role="status">{playing||loading||stageError||runtime.status==='done'?status:paused?'已暂停 · 可继续播放':playScope==='shot'?`只预演当前镜头的${MOVEMENT_LABELS[shot.movement]} · ${shot.seconds}s`:playScope==='scene'?`按顺序播放本场 ${scene.shots.length} 个镜头 · ${sceneDuration}s`:`按场次顺序播放 ${project.scenes.length} 场 · ${total}s`}</span>{allFixed&&!playing&&<button disabled={busy||loading} onClick={addGentleMotion}><MoveRight size={12}/>首镜头试试推进</button>}</div>
 <div className="pv-timeline-heading"><div><Film size={14}/><strong>镜头序列</strong><span>{scene.shots.length} 个镜头 · {sceneDuration}s</span></div><button onClick={()=>setStep('shots')}>编辑镜头 <ArrowRight size={12}/></button></div>
 <div className="pv-timeline">{scene.shots.map((s,i)=><button aria-label={`选择镜头 ${i+1} ${s.name}`} aria-pressed={shot.id===s.id} className={`${shot.id===s.id?'selected':''} ${runtime.shotId===s.id&&playing?'playing':''}`} key={s.id} style={{flexGrow:s.seconds}} onClick={()=>{stop();setWideView(false);setShotId(s.id);show(scene,s);setStep('shots');}}><small><span>{String(i+1).padStart(2,'0')}</span>{s.seconds}s</small><strong>{s.name}</strong><span>{s.focal} mm <b>·</b> {MOVEMENT_LABELS[s.movement]}</span><i className="pv-shot-progress" style={{width:`${runtime.shotId===s.id&&playing?scrub*100:0}%`}}/></button>)}<button className="pv-plus-shot" disabled={scene.shots.length>=12||playing||busy} onClick={()=>{const next=makePrevisShot(scene.scene);patchScene({shots:[...scene.shots,next]});setShotId(next.id);setStep('shots');}} aria-label="添加镜头"><Plus size={18}/></button></div>
 <details className="pv-boundary"><summary>预演说明</summary><p>机位使用布景单位，尺寸未经实景测量；移动镜头时请留意墙体与道具。灯光与景深为预演效果，不代表实拍照度。</p></details>
 </section><aside className="pv-inspector"><header className="pv-inspector-heading"><p>0{stepIndex+1} / {activeStep.title}</p><span>{activeStep.description}</span></header><fieldset disabled={busy||playing}>
 {step === 'plan' && <div className="pv-fields"><h2>从一个场景开始。</h2><label>选择布景<select aria-label="当前场景布景" value={scene.scene} onChange={e=>replaceSet(e.target.value as PrevisScene['scene'])}>{SCENES.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><small>更换布景会使用对应的默认镜头，参考与声音会保留。可以撤销。</small></label><label>项目任务<textarea value={project.goal} maxLength={1200} onChange={e => commit({ ...project, goal: e.target.value })}/></label><label>场景名称<input value={scene.title} maxLength={80} onChange={e => patchScene({ title: e.target.value })}/></label><label>场景意图<textarea value={scene.brief} maxLength={1200} onChange={e => patchScene({ brief: e.target.value })}/></label><details className="pv-details"><summary>保留约束与交付要求</summary><div className="pv-detail-fields"><label>必须保留<textarea value={scene.mustKeep} maxLength={800} onChange={e => patchScene({ mustKeep: e.target.value })}/></label><label>仍需确认<textarea value={scene.unknowns} maxLength={800} onChange={e => patchScene({ unknowns: e.target.value })}/></label><label>需要什么表达方式？<select value={scene.medium} onChange={e => patchScene({ medium: e.target.value as PrevisScene['medium'] })}><option value="3d">多机位 / 遮挡 / 运镜 → 3D 预演</option><option value="image">只讨论视觉方向 → 效果图</option><option value="video">表演 / 风格候选 → 视频参考</option></select></label>{scene.medium !== '3d' && <p className="pv-help">已记录交付意图。效果帧与动态分镜将使用当前三维布景。</p>}</div></details><div className="pv-row"><button disabled={project.scenes[0].id === scene.id} onClick={() => { const next = [...project.scenes], i = next.findIndex(s => s.id === scene.id); [next[i - 1], next[i]] = [next[i], next[i - 1]]; commit({ ...project, scenes: next }); }}><ArrowLeft size={13}/>场次提前</button><button disabled={project.scenes.at(-1)?.id === scene.id} onClick={() => { const next = [...project.scenes], i = next.findIndex(s => s.id === scene.id); [next[i + 1], next[i]] = [next[i], next[i + 1]]; commit({ ...project, scenes: next }); }}>场次后移<ArrowRight size={13}/></button></div><label>作者审核<select value={scene.review} onChange={e => patchScene({ review: e.target.value as PrevisScene['review'] })}><option value="draft">草案</option><option value="review">待讨论</option><option value="approved">我已确认</option></select></label><button disabled={project.scenes.length === 1} className="pv-danger" onClick={() => { stop(); const next = project.scenes.filter(s => s.id !== scene.id); commit({ ...project, scenes: next }); setSceneId(next[0].id); setShotId(next[0].shots[0].id); }}><Trash2 size={13}/>移除此场</button></div>}
 {step==='assets'&&<div className="pv-fields"><h2>哪些细节值得保留？</h2><p className="pv-help">加入参考，再标注它提供的是空间、材质、光线还是气氛。也可以直接进入镜头设计。</p><button className="pv-ai-context" onClick={()=>openModels('reference')}><Sparkles size={14}/><span>参考理解</span><small>模型选项</small><ArrowRight size={12}/></button><button className="pv-upload" disabled={busy} onClick={() => input.current?.click()}><Upload size={14}/>加入参考素材</button><p className="pv-help">图片与音频 每份最多20 MiB，保存在本机；图片作为参考，不会替换三维布景。</p>
 {scene.references.map(r => <div className="pv-reference" key={r.id}>{urls[r.id] && r.type.startsWith('image/') && <img src={urls[r.id]} alt={r.name}/>}<strong>{r.name}</strong><small>{r.width ? `${r.width} × ${r.height}` : `${r.seconds?.toFixed(1)}s`} · {urls[r.id] ? '文件已保存' : '需重新导入文件'}</small><select aria-label={`${r.name}用途`} value={r.role} onChange={e => patchScene({ references: scene.references.map(x => x.id === r.id ? { ...x, role: e.target.value as typeof r.role } : x) })}>{[['space', '空间结构'], ['material', '材质'], ['light', '光线'], ['mood', '视觉氛围'], ['sound', '音乐 / 音效'], ['voice', '对白 / 旁白']].map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select><textarea aria-label={`${r.name}参考说明`} value={r.note} maxLength={500} placeholder="保留什么？哪部分只是风格参考？" onChange={e => patchScene({ references: scene.references.map(x => x.id === r.id ? { ...x, note: e.target.value } : x) })}/><label className="pv-checkbox"><input type="checkbox" checked={r.accepted} onChange={e => patchScene({ references: scene.references.map(x => x.id === r.id ? { ...x, accepted: e.target.checked } : x) })}/>采用这份参考</label></div>)}</div>}
 {step === 'shots' && <div className="pv-fields"><div className="pv-shot-heading"><span>SHOT {String(scene.shots.findIndex(s=>s.id===shot.id)+1).padStart(2,'0')}</span><h2>{shot.name}</h2></div><div className="pv-motion-editor"><div className="pv-control-caption"><strong>运镜</strong><span>{MOVEMENT_LABELS[shot.movement]} / {shot.seconds}s</span></div><div className="pv-motion-options" role="group" aria-label="运镜方式">{(['hold','push','pull','truck','custom'] as const).map(m=><button key={m} className={shot.movement===m?'active':''} aria-pressed={shot.movement===m} onClick={()=>changeMovement(m)}>{MOVEMENT_LABELS[m]}</button>)}</div><div className="pv-motion-preview"><button disabled={!ready||loading||busy} onClick={()=>seek(0)}>起幅</button><input aria-label="当前镜头运镜进度" type="range" min={0} max={1} step={.01} value={scrub} disabled={!ready||loading||busy} onChange={e=>seek(Number(e.target.value))}/><button disabled={!ready||loading||busy} onClick={()=>seek(1)}>落幅</button></div><p>{shot.movement==='hold'?'固定镜头保持构图，连播时按顺序切到下一机位。':'拖动进度检查沿途构图，播放时按设定时长完成运动。'}</p></div><button className="pv-ai-context" onClick={()=>openModels('shots')}><Sparkles size={14}/><span>准备镜头建议</span><small>模型选项</small><ArrowRight size={12}/></button><details className="pv-details pv-shot-notes"><summary>镜头名称与拍摄意图</summary><div className="pv-detail-fields"><label>镜头名称<input value={shot.name} maxLength={80} onChange={e => patchShot({ name: e.target.value })}/></label><label>拍摄意图<textarea value={shot.intent} maxLength={500} onChange={e => patchShot({ intent: e.target.value })}/></label></div></details><label>机位预设<select value={shot.preset} onChange={e => { const next = makePrevisShot(scene.scene, e.target.value); patchShot({ ...next, id: shot.id, intent: shot.intent, text: shot.text, seconds: shot.seconds }); }}>{meta.shots.map(s => <option key={s.id} value={s.id}>{s.name} / {s.size} / {s.angle}</option>)}</select></label>{number('focal', 18, 135, '焦距 · mm')}{number('seconds', 2, 30, '镜头时长 · s', .5)}<label>画幅<select value={shot.aspect} onChange={e => patchShot({ aspect: e.target.value as PrevisShot['aspect'] })}>{[['2.39', '2.39:1 宽银幕'], ['1.85', '1.85:1'], ['1.7778', '16:9'], ['1', '1:1'], ['0.5625', '9:16']].map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>{number('light', 0, 1, '布景灯光预设强度', .05)}<p className="pv-help">调整已有光线预设，观察同一机位的变化。</p>
 <details className="pv-details" open={project.mode==='director'}><summary>精细机位与对焦</summary><div className="pv-detail-fields">{number('aperture', 1.4, 16, '光圈 · f/', .1)}<label>对焦距离 · 布景单位<input type="number" min={.1} max={80} step={.1} placeholder="自动：对准目标" value={shot.focus ?? ''} onChange={e => patchShot({ focus: e.target.value === '' ? null : Math.max(.1, Math.min(80, Number(e.target.value))) })}/></label>{vector('startOffset', '起始机位偏移')}{shot.movement !== 'hold' && vector('endOffset', '结束机位偏移')}{vector('targetOffset', '观看目标偏移')}<label>速度曲线<select value={shot.easing} onChange={e => patchShot({ easing: e.target.value as PrevisShot['easing'] })}><option value="smooth">缓入缓出</option><option value="linear">匀速</option></select></label></div></details>
 {scene.scene === 'station' && <label>列车预警时点 · s<input aria-label="列车预警时点" type="number" min={0} max={30} step={.5} value={shot.trainAt ?? ''} placeholder="留空：不触发" onChange={e => patchShot({ trainAt: e.target.value === '' ? null : Math.max(0, Math.min(30, Number(e.target.value))) })}/><small>提示声响一次；2.3 秒后列车过站约 10 秒。请给镜头留足时长。</small></label>}<label>动态分镜字幕<textarea value={shot.text} maxLength={600} onChange={e => patchShot({ text: e.target.value })} placeholder="台词 / 旁白。可以留空。"/></label><div className="pv-row"><button disabled={scene.shots[0].id === shot.id} onClick={() => moveShot(-1)}><ChevronUp size={13}/>提前</button><button disabled={scene.shots.at(-1)?.id === shot.id} onClick={() => moveShot(1)}><ChevronDown size={13}/>后移</button><button disabled={scene.shots.length === 1} onClick={() => { const next = scene.shots.filter(s => s.id !== shot.id); patchScene({ shots: next }); setShotId(next[0].id); }}><Trash2 size={13}/>删除</button></div></div>}
 {step === 'audio' && <div className="pv-fields"><h2>声音跟着事件走</h2><p className="pv-help">音乐、环境、旁白和音效分别安排。本场时间从 0 秒开始；没有把选定的原作歌曲默认放进新项目。</p><button className="pv-upload" disabled={busy} onClick={() => input.current?.click()}><Upload size={14}/>加入本地声音</button><label>将素材加入声音轨<select value="" disabled={scene.tracks.length >= 8} onChange={e => { const r = scene.references.find(r => r.id === e.target.value)!; patchScene({ tracks: [...scene.tracks, { id: previsId(), referenceId: r.id, layer: r.role === 'voice' ? 'voice' : 'music', start: 0, in: 0, out: Math.min(3600, r.seconds || 10), gain: .5, fade: .5, loop: false }] }); }}><option value="">选择已导入音频…</option>{scene.references.filter(r => r.type.startsWith('audio/')).map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select></label>{scene.tracks.map(t => { const r = scene.references.find(r => r.id === t.referenceId); const patch = (values: Partial<typeof t>) => patchScene({ tracks: scene.tracks.map(x => x.id === t.id ? { ...x, ...values } : x) }); return <div className="pv-track" key={t.id}><strong>{r?.name || '需重新绑定的音频'}</strong><select aria-label="声音分层" value={t.layer} onChange={e => patch({ layer: e.target.value as typeof t.layer })}>{[['music', '配乐'], ['ambience', '环境声'], ['voice', '对白 / 旁白'], ['effect', '事件音效']].map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select>{urls[t.referenceId] && <audio controls src={urls[t.referenceId]} preload="metadata"/>}<div className="pv-vector">{[['start', '时间线开始'], ['in', '素材入点'], ['out', '素材出点']].map(([key, label]) => <label key={key}>{label} · s<input type="number" min={key === 'out' ? .01 : 0} max={key === 'start' ? 3600 : r?.seconds || 3600} step={.1} value={t[key as 'start' | 'in' | 'out']} onChange={e => { const n = Math.max(0, Math.min(key === 'start' ? 3600 : r?.seconds || 3600, Number(e.target.value) || 0)); patch({ [key]: key === 'in' ? Math.min(n, t.out - .01) : key === 'out' ? Math.max(n, t.in + .01) : n }); }}/></label>)}</div><label>音量<input type="range" min={0} max={1} step={.05} value={t.gain} onChange={e => patch({ gain: Number(e.target.value) })}/></label><label>淡入淡出 · s<input type="number" min={0} max={10} step={.1} value={t.fade} onChange={e => patch({ fade: Math.max(0, Math.min(10, Number(e.target.value) || 0)) })}/></label><label className="pv-checkbox"><input type="checkbox" checked={t.loop} onChange={e => patch({ loop: e.target.checked })}/>循环选定区间</label><button onClick={() => patchScene({ tracks: scene.tracks.filter(x => x.id !== t.id) })}>移除声音轨</button></div>; })}<p className="pv-help">本地文件保存在浏览器数据库；跨设备工程需携带原素材。3D 布景附带低音量环境底声，列车声仅由镜头事件触发。</p></div>}
 {step === 'output' && <div className="pv-fields"><h2>导出你的拍摄方案</h2><button className={`pv-export ${usageGoal==='plan'?'is-primary':''}`} onClick={() => exportPlan('md')}><Download size={14}/>场景方案与镜头表</button><button className={`pv-export ${usageGoal==='frame'?'is-primary':''}`} disabled={!ready || busy || loading || playing} onClick={capture}><Camera size={14}/>当前效果帧 PNG</button><button className={`pv-export ${usageGoal==='film'?'is-primary':''}`} disabled={!canRecord || !ready || busy || loading || playing} onClick={() => void play('scene', true)}><Play size={14}/>本场动态分镜 WebM</button><button className="pv-export" disabled={!canRecord || !ready || busy || loading || playing} onClick={() => void play('project', true)}><Play size={14}/>全方案动态分镜 WebM</button>{videoOutput && <div className="pv-video"><video controls src={videoOutput} preload="metadata"/><a href={videoOutput} download="动态分镜.webm">保存生成的 WebM 文件 ↓</a></div>}<p className="pv-help">导出 24fps 浏览器预演，含镜头字幕 / 声音，每次 ≤180s。用首镜头画幅，其他画幅留黑边。实际流畅度受设备影响；加载期间暂停录制。{!canRecord ? '此浏览器不支持 WebM，请使用支持 MediaRecorder 的浏览器。' : ''}</p><button className="pv-export" onClick={() => exportPlan('json')}><Download size={14}/>完整工程 JSON</button><button className="pv-export" onClick={() => jsonInput.current?.click()}><Upload size={14}/>导入工程 JSON</button><p className="pv-help">工程保留所有镜头参数与素材说明；不含原文件，也不会自动恢复到其他设备。工程和素材保存在本机，不会上传或公开。</p><h3>效果帧比较</h3><p className="pv-help">修改一个参数，再存一帧。这里保留最近四张与拍摄参数，本次打开有效。</p>{frames.map((f, i) => <div className="pv-frame" key={i}><img src={f.url} alt={f.label}/><strong>{f.label} · {f.scene}</strong><a href={f.url} download={`${f.label}-${f.shot.name}.png`}>保存 PNG ↓</a><small>{f.shot.focal}mm / {f.shot.aspect} / f{f.shot.aperture} / 灯光 {f.shot.light} / {f.width}×{f.height}</small><button onClick={() => { if (scene.title !== f.scene) {
        setNotice('请切回该场景再恢复镜头参数。');
        return;
    } patchShot({ ...f.shot, id: shot.id }); }}>恢复此组镜头参数</button></div>)}</div>}
 </fieldset><footer className="pv-step-actions"><button disabled={stepIndex===0} onClick={()=>setStep(STUDIO_STEPS[stepIndex-1].id)}><ArrowLeft size={13}/>上一步</button>{stepIndex<4?<button className="pv-primary" onClick={()=>setStep(STUDIO_STEPS[stepIndex+1].id)}>{STUDIO_STEPS[stepIndex+1].title}<ArrowRight size={14}/></button>:<span><Check size={13}/>按需导出</span>}</footer></aside></div><input ref={input} type="file" multiple accept="image/jpeg,image/png,image/webp,audio/*" hidden onChange={e => void addFiles(e.target.files)}/><input ref={jsonInput} type="file" accept=".json,application/json" hidden onChange={e => void importJSON(e.target.files?.[0])}/>{notice && <div className="pv-notice" role="status"><span>{notice}</span><button onClick={() => setNotice('')} aria-label="收起提示">×</button></div>}
 {guide&&<StudioOnboarding mode={project.mode} currentGoal={usageGoal} onClose={closeGuide} onStart={startGuide}/>} {modelPanel&&<ModelOptionsPanel project={project} scene={scene} initialTask={modelTask} onClose={()=>setModelPanel(false)}/>} </main>;
}
