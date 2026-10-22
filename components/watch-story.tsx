'use client';
import {useEffect,useRef,useState} from 'react';
import type {Story} from '../lib/story-model';
export default function WatchStory({token}:{token:string}) {
  const frame=useRef<HTMLIFrameElement>(null);
  const [data,setData]=useState<Story|null>(null),[error,setError]=useState(''),[loaded,setLoaded]=useState(false),[ended,setEnded]=useState(false),[feedback,setFeedback]=useState(false),[note,setNote]=useState(''),[busy,setBusy]=useState(false),[choice,setChoice]=useState(''),[feedbackError,setFeedbackError]=useState('');
  const session=useRef('');const publicationTime=useRef<number|undefined>(undefined);
  useEffect(()=>{
    try{const key='story-tape:session:'+token;session.current=sessionStorage.getItem(key)||crypto.randomUUID();sessionStorage.setItem(key,session.current);}catch{session.current=crypto.randomUUID();}
    const abort=new AbortController();
    fetch('/api/public/'+encodeURIComponent(token),{cache:'no-store',signal:abort.signal}).then(async r=>{const value=await r.json() as {data:Story;message?:string;publishedAt?:number};if(!r.ok)throw new Error(value.message||'这盘磁带已经收回，或链接无法访问。');publicationTime.current=value.publishedAt;setData(value.data);document.title=value.data.title+' · 故事磁带';}).catch(e=>{if(e.name!=='AbortError')setError(e.message);});
    const message=(event:MessageEvent)=>{
      if(event.origin!==location.origin||event.source!==frame.current?.contentWindow||event.data?.type!=='story-tape:event')return;
      const name=event.data.event;
      if(name==='loaded')setLoaded(true);
      if(name==='error')setError('故事暂时未能加载，请刷新重试。');
      if(name==='complete')setEnded(true);
      if(['start','chapter','complete'].includes(name))fetch(`/api/public/${encodeURIComponent(token)}/events`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event:name,...(name==='chapter'?{chapterId:event.data.chapterId}:{}),sessionId:session.current,publishedAt:publicationTime.current}),keepalive:true}).catch(()=>{});
    };
    addEventListener('message',message);return()=>{abort.abort();removeEventListener('message',message);};
  },[token]);
  async function sendFeedback(){
    if(!choice||busy)return;setBusy(true);setFeedbackError('');
    try{const r=await fetch(`/api/public/${encodeURIComponent(token)}/feedback`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:session.current,choice,note,publishedAt:publicationTime.current})});const value=await r.json() as {message?:string};if(!r.ok)throw new Error(value.message||'暂时未能送出');setFeedback(true);}catch(e){setFeedbackError((e as Error).message);}finally{setBusy(false);}
  }
  return <main style={{position:'fixed',inset:0,background:'#111512',color:'#f3ece0',fontFamily:'system-ui,sans-serif'}}>
    {data&&!error&&<iframe ref={frame} title={data.title} src={`/film/?publication=${encodeURIComponent(token)}`} allow="autoplay; fullscreen" style={{border:0,width:'100%',height:'100%'}}/>}
    {!loaded&&!error&&<div style={{position:'absolute',inset:0,display:'grid',placeItems:'center',background:'#111512',pointerEvents:'none'}}><div style={{textAlign:'center',padding:24}}><span style={{fontSize:10,letterSpacing:4,color:'#b5baa9'}}>STORY TAPE</span><h1 style={{fontFamily:'Georgia,serif',fontSize:36,fontWeight:400,margin:'20px 0'}}>{data?.title||'一盘故事磁带'}</h1><p style={{fontSize:13,color:'#b5baa9'}}>场景正在就位…</p></div></div>}
    {error&&<div role="alert" style={{position:'absolute',inset:0,display:'grid',placeItems:'center',background:'#111512'}}><div style={{maxWidth:400,padding:24,textAlign:'center'}}><p>{error}</p><button onClick={()=>location.reload()} style={{background:'none',color:'#f3ece0',border:'1px solid #737a6b',padding:'10px 18px',cursor:'pointer'}}>再试一次</button> <a href="/" style={{color:'#bbc3b4',marginLeft:12}}>故事磁带</a></div></div>}
    {ended&&data?.feedback&&!error&&<aside aria-label="观看反馈" style={{position:'absolute',right:16,bottom:74,width:'min(350px,calc(100vw - 32px))',background:'#eee7da',color:'#26342e',padding:20,boxShadow:'0 8px 40px #0006'}}>
      <button aria-label="收起反馈" onClick={()=>setEnded(false)} style={{position:'absolute',right:10,top:8,border:0,background:'none',fontSize:20,color:'#26342e',cursor:'pointer'}}>×</button>
      {feedback?<p style={{margin:0,lineHeight:1.8}}>你的回应，已经留在这盘磁带里。谢谢。</p>:<><p style={{margin:'0 0 12px',fontFamily:'Georgia,serif'}}>看完以后，你觉得怎样？</p><div style={{display:'flex',gap:6,flexWrap:'wrap'}}>{[['moved','有被打动'],['clear','表达很清楚'],['confused','有点没看懂']].map(([id,label])=><button key={id} onClick={()=>setChoice(id)} aria-pressed={choice===id} style={{border:'1px solid #a9b1a2',padding:'7px 9px',background:choice===id?'#304c3c':'transparent',color:choice===id?'#f4eee3':'#304c3c',cursor:'pointer',fontSize:12}}>{label}</button>)}</div><textarea aria-label="留一句话，可不填" placeholder="留一句话，也可以不填。" maxLength={500} value={note} onChange={e=>setNote(e.target.value)} style={{width:'100%',boxSizing:'border-box',marginTop:12,minHeight:62,background:'transparent',color:'#26342e',border:'1px solid #a9b1a2',padding:8,fontSize:13}}/><button onClick={sendFeedback} disabled={!choice||busy} style={{padding:'8px 14px',marginTop:8,border:0,background:'#304c3c',color:'#eee7da',cursor:'pointer',opacity:(!choice||busy)?.45:1}}>{busy?'正在送出…':'留给作者'}</button>{feedbackError&&<p role="alert" style={{fontSize:12,color:'#8b4037',lineHeight:1.7}}>{feedbackError}</p>}<p style={{fontSize:10,color:'#707a70',lineHeight:1.7,marginBottom:0}}>匿名反馈。只记录去重播放会话、章节到达和反馈；不记录 IP 或账户资料。</p></>}
    </aside>}
  </main>;
}
