import {readFileSync} from 'node:fs';
const vendor=new URL('../dist/vendor/',import.meta.url),moduleURL=new URL('three.module.js',vendor).href;
const dataURL=source=>'data:text/javascript;base64,'+Buffer.from(source).toString('base64');
const utilities=dataURL(readFileSync(new URL('BufferGeometryUtils.js',vendor),'utf8').replace("from 'three'",`from '${moduleURL}'`));
const loader=dataURL(readFileSync(new URL('GLTFLoader.js',vendor),'utf8').replace("from 'three'",`from '${moduleURL}'`).replace("from './BufferGeometryUtils.js'",`from '${utilities}'`));
const {GLTFLoader}=await import(loader);
// Keep the real hierarchy, quantized geometry and transforms; avoid browser-only texture decoding.
export async function loadGeometry(file){
  const original=readFileSync(file),jsonLength=original.readUInt32LE(12),document=JSON.parse(original.subarray(20,20+jsonLength).toString());
  for(const mesh of document.meshes)for(const primitive of mesh.primitives)delete primitive.material;
  document.materials=[];document.textures=[];document.images=[];
  const bytes=Buffer.from(JSON.stringify(document)),padded=Buffer.alloc(Math.ceil(bytes.length/4)*4,32);bytes.copy(padded);
  const binary=original.subarray(20+jsonLength),buffer=Buffer.alloc(20+padded.length+binary.length);
  buffer.writeUInt32LE(0x46546c67);buffer.writeUInt32LE(2,4);buffer.writeUInt32LE(buffer.length,8);buffer.writeUInt32LE(padded.length,12);buffer.writeUInt32LE(0x4e4f534a,16);padded.copy(buffer,20);binary.copy(buffer,20+padded.length);
  const result=await new GLTFLoader().parseAsync(buffer.buffer.slice(buffer.byteOffset,buffer.byteOffset+buffer.byteLength),'');
  result.scene.updateMatrixWorld(true);return result.scene;
}
