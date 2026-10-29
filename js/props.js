// Móveis prontos (Poly Haven, CC0) no lugar das peças simples do GLB: recepção e apto 10, os ambientes da caminhada.
// Carregam em segundo plano depois da abertura; cada peça fica no lugar e na escala real, apoiada no piso.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { buildInterior } from './interior.js';

const DEG = Math.PI / 180;
// [modelo, x, y do piso, z, giro (graus; 0 = frente para +z), largura máxima]
const PROPS = [
  ['chinese_sofa', 22.05, 0.1, 17.5, 90, 2.3],
  ['modern_arm_chair_01', 24.45, 0.1, 16.7, -75, 0.8],
  ['modern_arm_chair_01', 24.45, 0.1, 18.3, -105, 0.8],
  ['potted_plant_04', 27.25, 0.0, 16.15, 0, 0.9],
  ['potted_plant_04', 21.6, 0.1, 21.45, 140, 0.9],
  ['potted_plant_04', 24.35, 0.1, 20.9, 70, 0.9],
  ['chinese_sofa', 42.3, 3.0, 7.6, -90, 1.9],
  ['wooden_table_02', 40.6, 3.0, 5.8, 90, 1.15],
  ['chinese_stool', 40.0, 3.0, 5.8, 90, 0.55],
  ['chinese_stool', 41.2, 3.0, 5.8, -90, 0.55],
  ['potted_plant_02', 39.75, 3.0, 8.25, 0, 0.6],
];
// tecido cru: as almofadas da poltrona perdem o couro preto; o estampado floral do daybed vira linho
const LINEN = new THREE.Color('#d8cdb8');
function restyle(n, m) {
  if (m.name === 'modern_arm_chair_01_pillow') { m.map = null; m.color.copy(LINEN); m.roughness = 0.95; m.metalness = 0; }
}

export async function loadProps(world, env, onDone) {
  const group = new THREE.Group(); group.visible = false;
  world.root.add(group); world.props = group;
  group.add(buildInterior(world, env));
  const loader = new GLTFLoader(), cache = new Map();
  const get = (n) => { if (!cache.has(n)) cache.set(n, loader.loadAsync(`assets/models/${n}/${n}_1k.gltf`)); return cache.get(n); };
  await Promise.all(PROPS.map(async ([n, x, y, z, yaw, wMax]) => {
    let g;
    try { g = await get(n); } catch (e) { console.warn('móvel não carregou', n, e); return; }
    const o = g.scene.clone(true);
    o.traverse((m) => {
      if (!m.isMesh) return;
      m.castShadow = m.receiveShadow = true;
      m.material = m.material.clone(); m.material.envMap = env; m.material.envMapIntensity = 0.55; restyle(n, m.material);
      m.userData = { prop: true };
    });
    o.rotation.y = yaw * DEG;
    o.updateMatrixWorld(true);
    const bb = new THREE.Box3().setFromObject(o), sz = bb.getSize(new THREE.Vector3());
    const s = Math.min(1, wMax / Math.max(sz.x, sz.z));
    o.scale.setScalar(s); o.updateMatrixWorld(true);
    bb.setFromObject(o);
    o.position.set(x - (bb.min.x + bb.max.x) / 2, y - bb.min.y, z - (bb.min.z + bb.max.z) / 2);
    group.add(o);
  }));
  if (onDone) onDone();
  return group;
}
