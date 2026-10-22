import * as THREE from 'three';

// Original scene treatment inspired by the idea of an unhurried date.
export const FILM={title:'老派约会之必要',note:'借你一段路 · 原创独白本',logline:'第一次约会，从午后走到夜晚。等车、休息、吃饭，回家时又多走了一段。',source:'https://www.youtube.com/watch?v=u14rrcxENDw'};
export const SETS={
  casa:{number:'01',name:'街角店铺',place:'EXT. 街角 · 午后',beat:'赴约 / 先把时间留出来',story:'约定写在一张纸条上。提早到的人在橱窗前等候，门终于打开。约会从一个真实的地方开始。',blocking:'招牌建立地点，橱窗藏住等候者，长椅作为下一次见面的伏笔。',light:.88,shots:[
    {id:'master',name:'店铺建立镜头',size:'全景',angle:'左前 35° · 平视',focal:35,pos:[-6.1,3.5,10.1],target:[-.15,2.55,.9],shallow:false},
    {id:'window',name:'橱窗内外',size:'中景',angle:'正面 · 平视',focal:50,anchor:'ai-product',offset:[-.35,.05,5.5],targetOffset:[0,.3,0]},
    {id:'bench',name:'长椅与门前',size:'近景',angle:'左侧 30° · 低机位',focal:50,anchor:'research',offset:[-2.71,.6,4.7],targetOffset:[.3,.2,0]},
    {id:'sign',name:'店铺招牌',size:'特写',angle:'左前 15° · 仰拍',focal:85,anchor:'prologue',offset:[-2.55,-.3,9.5],shallow:true},
    {id:'door',name:'侧门入口',size:'中景',angle:'左侧 45° · 平视',focal:35,anchor:'about',offset:[-3.5,.15,3.5],shallow:false}
  ]},
  station:{number:'02',name:'山间站台',place:'EXT. 长谷寺站 · 午后',beat:'等待 / 不催促的抵达',story:'列车经过，短暂挡住视线。远处的身影出现时，等待也变成约会的一部分。他们决定慢一点走。',blocking:'建立站台方向，长椅留出人物站位，过站镜头用长列车制造遮挡，樱花作为时间感。',light:.28,shots:[
    {id:'master',name:'站台建立镜头',size:'全景',angle:'正面 · 平视',focal:35,pos:[-.25,2.2,11.8],target:[0,1.9,-1.0],shallow:false},
    {id:'seats',name:'候车长椅',size:'中景',angle:'左侧 35° · 平视',focal:50,pos:[-5.0,1.65,5.8],target:[-1,1.2,-.45]},
    {id:'low',name:'站台边缘',size:'中景',angle:'右前 30° · 低机位',focal:35,pos:[4.0,.9,6.4],target:[-.1,1.1,-.65],shallow:false},
    {id:'passing',name:'列车过站',size:'全景',angle:'右前 35° · 平视',focal:28,pos:[6.3,2.3,11.5],target:[-.6,1.45,1.1],shallow:false,effect:'auto-train'},
    {id:'blossom',name:'窗外樱花',size:'近景',angle:'正面 · 微仰',focal:85,pos:[1.0,2.8,6.8],target:[2,3.85,-8],shallow:true,effect:'wind'},
    {id:'high',name:'站台空间',size:'全景',angle:'右侧 30° · 俯拍',focal:35,pos:[7.2,5.7,11.1],target:[0,1.25,-.3],shallow:false},
    {id:'axis',name:'沿站台望去',size:'纵深全景',angle:'右侧轴向 · 平视',focal:50,pos:[10.2,1.8,6.1],target:[-3.5,1.55,-.1],shallow:false},
    {id:'reverse',name:'候车位的反向镜头',size:'中景',angle:'左侧轴向 · 平视',focal:50,pos:[-8.6,1.65,1.55],target:[2.5,1.35,-.5],shallow:false},
    {id:'crossing',name:'道口与铁轨',size:'中景',angle:'斜向 45° · 低机位',focal:35,pos:[8.7,1.35,8.4],target:[8.1,1.1,2.8],shallow:false},
    {id:'seat-detail',name:'长椅的等待',size:'近景',angle:'右侧 · 微俯',focal:85,pos:[3.8,1.95,5.9],target:[.7,1.07,-.3],shallow:true}
  ]},
  interior:{number:'03',name:'黄昏窗边',place:'INT. 窗边长椅 · 黄昏',beat:'靠近 / 把话慢慢说完',story:'在一间旧屋里，他们并肩坐下。窗外的绿影晃动，沉默不再需要被填满。一句话说到一半，两个人都笑了。',blocking:'窗边两个空座位、两杯茶与翻开的书保留休息的痕迹。机位保持在同一侧轴线，斜入的黄昏光穿过百叶。',light:1,shots:[
    {id:'master',name:'黄昏窗边全景',size:'全景',angle:'正面 · 平视',focal:35,pos:[0,1.85,8.1],target:[0,1.4,-1.25],shallow:false},
    {id:'two-shot',name:'并肩的两个座位',size:'中景',angle:'正面 · 平视',focal:50,pos:[0,1.75,6.0],target:[0,1.65,-1.4],shallow:false},
    {id:'man',name:'左侧座位与茶杯',size:'近景',angle:'右侧 25° · 平视',focal:85,pos:[1.5,1.65,3.1],target:[-.63,1.12,-1.995],shallow:true},
    {id:'woman',name:'右侧座位与窗光',size:'近景',angle:'左侧 25° · 平视',focal:85,pos:[-1.3,1.65,3.1],target:[.68,1.12,-1.995],shallow:true},
    {id:'detail',name:'翻开的书与软垫',size:'特写',angle:'左前 30° · 微俯',focal:85,pos:[-1.8,2.3,2.3],target:[-.12,.99,-1.27],shallow:true},
    {id:'window',name:'百叶窗与灯光',size:'中景',angle:'左侧 30° · 平视',focal:50,anchor:'window',offset:[-3.75,.25,6.5],shallow:false}
  ]},
  diner:{number:'04',name:'复古餐馆',place:'INT. 餐馆 · 入夜',beat:'对坐 / 把手机翻过去',story:'红桌面上只有两杯热饮和一部扣下的手机。他们交换各自喜欢的音乐，点唱机亮起来。这一次，注意力没有离开对面的人。',blocking:'双人全景建立桌面轴线，左右近景保持视线相接，手机与杯子的插入镜头连接人物反应。',light:1,shots:[
    {id:'master',name:'餐馆建立镜头',size:'全景',angle:'正面 · 平视',focal:35,pos:[0,2.1,8.5],target:[0,1.65,-1],shallow:false},
    {id:'two-shot',name:'两杯热饮',size:'中景',angle:'正面 · 平视',focal:50,pos:[0,1.9,6.5],target:[0,1.55,-.7],shallow:false},
    {id:'man',name:'左侧餐位',size:'近景',angle:'右侧 · 平视',focal:85,anchor:'man',offset:[3.4,.05,3.5],shallow:true},
    {id:'woman',name:'右侧餐位',size:'近景',angle:'左侧 · 平视',focal:85,anchor:'woman',offset:[-3.4,.05,3.5],shallow:true},
    {id:'table',name:'杯子与扣下的手机',size:'特写',angle:'左前 · 俯拍',focal:85,anchor:'table',offset:[-1.3,2.5,3.9],shallow:true},
    {id:'jukebox',name:'点唱机亮起',size:'近景',angle:'正面 · 平视',focal:50,anchor:'jukebox',offset:[0,.1,4.3],shallow:false}
  ]},
  alley:{number:'05',name:'蓝调夜巷',place:'EXT. 旧街长椅 · 深夜',beat:'依偎 / 再多坐一会儿',story:'回程经过一盏旧街灯。他们在长椅上停下，一件外套盖住两个人的膝头。街道很空，谁都没有急着说再见。',blocking:'街巷远景保留蓝色夜幕与暖灯下的空长椅，花束与折好的外套留下赴约的回声。',light:1,shots:[
    {id:'master',name:'夜巷与一盏灯',size:'远景',angle:'右前 · 平视',focal:35,pos:[1.8,2.35,9.1],target:[.25,1.65,-2.7],shallow:false},
    {id:'two-shot',name:'街灯下的空长椅',size:'中景',angle:'右前 · 平视',focal:50,anchor:'couple',offset:[2,.35,7.0],shallow:false},
    {id:'close',name:'长椅与折好的外套',size:'近景',angle:'右侧 · 平视',focal:85,anchor:'couple',offset:[3.4,.05,5.8],shallow:true},
    {id:'profile',name:'长椅侧面',size:'中景',angle:'右侧 50° · 低机位',focal:50,anchor:'couple',offset:[4.5,-.25,4.0],shallow:false},
    {id:'flowers',name:'花束还在',size:'特写',angle:'右前 · 微俯',focal:85,anchor:'flowers',offset:[2.2,1.2,4.4],shallow:true},
    {id:'street',name:'不急着结束的夜',size:'全景',angle:'正面 · 平视',focal:28,pos:[0,2.1,9.8],target:[0,2.1,-8],shallow:false}
  ]},
  courtyard:{number:'06',name:'松下庭院',place:'EXT./INT. 中式庭院与回廊 · 秋日黄昏',beat:'散步 / 顺路看个院子',story:'晚饭前顺路看看一个旧院子。他们沿石径穿过半开的木门，在回廊歇一会儿，小票上画着不太准确的路线。',blocking:'没有人物模型。门洞、廊柱与窗棂形成真实前景，空茶盏和信纸承接两人的位置；机位沿石径到廊下，不穿过墙体。',light:.82,shots:[
    {id:'master',name:'旧墙与斜松',size:'全景',angle:'门外 · 平视',focal:35,pos:[0,2.4,10.8],target:[0,1.65,-3],shallow:false},
    {id:'path',name:'沿石径走近',size:'纵深中景',angle:'正面 · 平视',focal:50,pos:[.5,1.7,4.8],target:[0,1.7,-6.3],shallow:false},
    {id:'corridor',name:'廊下看院子',size:'中景',angle:'右侧 · 平视',focal:50,pos:[3.8,1.65,2],target:[-.6,1.7,-4.4],shallow:false},
    {id:'pine',name:'松枝与旧白墙',size:'近景',angle:'左侧 · 微仰',focal:85,pos:[-3.7,1.5,2.8],target:[-1.4,2.5,-3.6],shallow:true},
    {id:'door',name:'铜环与半开的门',size:'近景',angle:'门外 · 微俯',focal:85,pos:[-1.8,2,0],target:[-.45,1.6,-6.3],shallow:true},
    {id:'lantern',name:'纸灯笼与红穗',size:'近景',angle:'廊下 · 微仰',focal:50,pos:[3.6,2.7,4.5],target:[3.91,2.78,.24],shallow:true},
    {id:'window',name:'从木窗内望出去',size:'中景',angle:'回廊内 · 平视',focal:35,pos:[5.8,1.65,.7],target:[-.65,1.9,-3.85],shallow:false}
  ]}
};
export const SET_ORDER=['casa','station','interior','courtyard','diner','alley'];
for(const [index,id] of SET_ORDER.entries())SETS[id].number=String(index+1).padStart(2,'0');
export function getShot(set,id){return SETS[set].shots.find(s=>s.id===id)||SETS[set].shots[0];}
export function shotFrame(engine,id){
  if(!id?.startsWith('shot:'))return null;
  const shot=getShot(engine.kind,id.slice(5));
  let target=shot.target?new THREE.Vector3(...shot.target):(engine.anchors[shot.anchor]?.clone()||new THREE.Vector3(0,1.4,-1));
  if(shot.targetOffset)target.add(new THREE.Vector3(...shot.targetOffset));
  const pos=shot.pos?new THREE.Vector3(...shot.pos):target.clone().add(new THREE.Vector3(...shot.offset));
  return{pos,target};
}
export function fitViewport(engine){
  const width=innerWidth,height=innerHeight;engine.mobile=width<=600;
  if(engine.cinematic){const aspect=engine.frameAspect??2.39,amount=engine.cinemaAmount??1,endW=Math.min(width,height*aspect),endH=endW/aspect,w=width+(endW-width)*amount,h=height+(endH-height)*amount;engine.rect=[(width-w)/2,(height-h)/2,w,h];}
  else engine.rect=[0,0,width,height];
  if(engine.viewWidth!==width||engine.viewHeight!==height){engine.renderer.setSize(width,height,false);engine.viewWidth=width;engine.viewHeight=height;}engine.camera.aspect=engine.rect[2]/engine.rect[3];
}
