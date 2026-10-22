// Shared opening/return timing keeps camera, environment and aperture together.
export const DOLLY_MS=4800, LIGHT_MS=1300, RETURN_MS=3200, SHOT_MS=1800;
export const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
export const CROP_MS=850;
export function opening(progress){return{crop:ease(progress*DOLLY_MS/CROP_MS),lens:ease(progress),background:ease((progress-.35)/.5),gear:ease((progress-.22)/.56)};}
export function retreat(progress,from){const t=ease(progress);return{crop:from.crop*(1-t),background:from.background*(1-ease((progress-.15)/.65)),gear:from.gear*(1-ease((progress-.05)/.7)),focal:from.focal+(from.toFocal-from.focal)*t};}
export function workFocal(fov,aspect){return 36/(2*Math.tan(fov*Math.PI/360)*aspect);}
