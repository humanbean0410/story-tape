import type { Story, Chapter, Beat } from './story-model';
export const makeId = (prefix = 'part') => `${prefix}-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`}`;
const beat = (text: string, shot = 'master', seconds = 10): Beat => ({id:makeId('beat'), speaker:'独白', text,shot,seconds});
const chapter = (scene:Chapter['scene'],title:string,texts:[string,string?][]):Chapter => ({id:makeId('chapter'),scene,title,note:'',sound:'ambience',audioAssetId:null,photoAssetId:null,beats:texts.map(([text,shot])=>beat(text,shot))});
export const TEMPLATES = [
 {id:'journey',title:'旅行中的一段路',description:'从出发到停留，记下旅途中真正留意到的事。',scenes:['casa','station','courtyard'],label:'旅行 / 记忆'},
 {id:'letter',title:'留给一个人的话',description:'把一封没写完的信，放在三个有温度的地方。',scenes:['casa','interior','alley'],label:'关系 / 私人短篇'},
 {id:'book',title:'围绕一本书',description:'从读到的一句话开始，谈谈自己的生活。',scenes:['interior','courtyard','diner'],label:'阅读 / 随想'},
 {id:'blank',title:'空白磁带',description:'从一个场景、一句话开始，按你的想法组织。',scenes:['casa'],label:'自由创作'},
] as const;
export function createStory(template='journey'):Story {
 const common={schemaVersion:1 as const,subtitle:'',author:'',dedication:'',template,opening:true,feedback:true};
 if(template==='letter') return {...common,title:'留给一个人的话',chapters:[
 chapter('casa','我们见面的地方',[['这家店还在。我经过的时候，还是会朝里面看一眼。'],['那天你比我先到，坐在门边，说路上没怎么堵。','bench'],['我其实提前了半小时，只是绕到旁边走了一圈。','door'],['那时有一些话没说。今天想慢慢补上。','window']]),
 chapter('interior','坐一会儿',[['后来我们坐在窗边，聊了很久。'],['我记得你说，最近总觉得事情做不完。','two-shot'],['我当时急着给建议。现在想想，先听你说完就好了。','detail'],['如果你愿意，我们可以找一天，再坐一会儿。','window']]),
 chapter('alley','下次见',[['走到路口时，你问我接下来怎么回去。'],['我说顺路，其实要多走两站。','profile'],['不是什么大事，我就是想再和你说几句话。','close'],['写到这里，我还是想问：下个周末，你有空吗？','street']]) ]};
 if(template==='book') return {...common,title:'读完这本书以后',chapters:[
 chapter('interior','从一页开始',[['书读完了，我没有马上找下一本。'],['有一页折了角，想拿给朋友看看。','detail'],['以前我觉得，读书是为了得到一个答案。','two-shot'],['现在更在意的是：这个问题，为什么刚好让我停下来？','window']]),
 chapter('courtyard','带着问题走一段',[['带着那个问题出门，路边的东西看起来有点不一样。'],['这面墙修过很多次，还能算原来的墙吗？','pine'],['如果一个人换了工作、住处和想法，我们为什么还说他没变？','path'],['可能有些事情，得找一个了解自己的人一起想。','corridor']]),
 chapter('diner','聊聊你的看法',[['吃饭时，我把那一页拿出来。'],['我们没有同意对方，但说得挺开心。','two-shot'],['我发现自己以前读得太快，有些不理解的地方直接翻过去了。','table'],['下次重读的时候，我想把今天的讨论写在旁边。','jukebox']]) ]};
 if(template==='blank') return {...common,title:'未命名的磁带',chapters:[chapter('casa','第一章',[['在这里，写下故事的第一句话。']])]};
 return {...common,title:'旅行中的一段路',chapters:[
 chapter('casa','出发之前',[['出门前，我给行程留了一段空白。'],['以前总想多去几个地方。这次想看看，少安排一点会怎样。','sign'],['在街角买了杯喝的，坐了十分钟。','bench'],['第一张照片没拍到景点，是这家店的门。','door']]),
 chapter('station','等下一班车',[['下一班车还有一会儿。'],['我收起地图，在长椅上看人来人往。','seats'],['列车经过时，旁边的人把说到一半的话停了下来。','passing'],['我后来忘了他们在聊什么，却记得这个小停顿。','blossom']]),
 chapter('courtyard','走进去看看',[['离开车站以后，拐进了一条原本没打算走的路。'],['门没有关，里面有人在给植物浇水。','door'],['我问可不可以看看。他点点头，又接着做手上的事。','path'],['这段路没在计划里，却成了我最想记住的一段。','pine']]) ]};
}
