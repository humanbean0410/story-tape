// One story document drives the same real 3D sets used by the original film.
const params = new URLSearchParams(location.search);
export const preview = params.has('studioPreview');
export const publication = params.get('publication');
export const productMode = preview || !!publication;
let initialResolve;
const firstStory = new Promise(resolve => initialResolve = resolve);
const validScenes = new Set(['casa','station','interior','courtyard','diner','alley']);
function valid(data) {
  return data?.schemaVersion === 1 && typeof data.title === 'string' && Array.isArray(data.chapters) && data.chapters.length > 0 && data.chapters.length <= 6 && data.chapters.every(chapter => validScenes.has(chapter.scene) && Array.isArray(chapter.beats) && chapter.beats.length > 0 && chapter.beats.every(beat => typeof beat.text === 'string' && Number.isFinite(beat.seconds) && beat.seconds >= 2 && beat.seconds <= 30));
}
export function notify(event, chapterId) {
  if (parent !== window) parent.postMessage({type:'story-tape:event',event,chapterId},location.origin);
}
if (preview) {
  addEventListener('message', event => {
    if (event.origin !== location.origin || event.source !== parent || event.data?.type !== 'story-tape:load' || !valid(event.data.story)) return;
    initialResolve(event.data.story);
  });
  const ready = () => parent.postMessage({type:'story-tape:ready'},location.origin);
  ready();
  const repeat = setInterval(ready,500);
  firstStory.then(() => clearInterval(repeat));
  setTimeout(() => {clearInterval(repeat);initialResolve(null);},20000);
}
export let PROJECT = null;
if (preview) PROJECT = await firstStory;
else if (publication) {
  const response = await fetch(`/api/public/${encodeURIComponent(publication)}`,{cache:'no-store'});
  if (!response.ok) throw new Error('这盘磁带已经收回，或链接无法访问。');
  const payload = await response.json();
  if (!valid(payload.data)) throw new Error('故事内容无法读取。');
  PROJECT = payload.data;
}
if (productMode && !PROJECT) throw new Error('没有收到故事内容。请关闭预览后重试。');
export let chapterIndex = 0;
export const chapter = () => PROJECT?.chapters[chapterIndex];
export const setChapter = index => {chapterIndex = index;};
export const assetUrl = id => `/api/assets/${encodeURIComponent(id)}${publication?`?publication=${encodeURIComponent(publication)}`:''}`;
export function projectTimeline() {
  let start = 0, arrival = false;
  return chapter().beats.map((beat,index) => {
    const duration = beat.seconds*1000;
    const sound = chapter().scene === 'station' && beat.shot === 'passing' && !arrival ? 'arrival' : undefined;
    if (sound) arrival = true;
    const result = {index,start,end:start+duration,who:beat.speaker,text:beat.text,shot:beat.shot,sound,dialogue:!['动作','结尾'].includes(beat.speaker)};
    start += duration + 350;
    return result;
  });
}
