// Móveis no lugar das peças simples do GLB: recepção (Poly Haven, CC0) e apto 10 (modelados em blender/*.py).
// Carregam em segundo plano depois da abertura; cada peça fica no lugar e na escala real, apoiada no piso.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { buildInterior } from './interior.js';
import { pieceIds } from './world.js';

const DEG = Math.PI / 180;
// [modelo, x, y do piso, z, giro (graus; 0 = frente para +z), largura máxima]
const PROPS = [
  ['chinese_sofa', 22.05, 0.1, 17.5, 90, 2.3],
  ['modern_arm_chair_01', 24.45, 0.1, 16.7, -75, 0.8],
  ['modern_arm_chair_01', 24.45, 0.1, 18.3, -105, 0.8],
  ['potted_plant_04', 27.25, 0.0, 16.15, 0, 0.9],
  ['potted_plant_04', 21.6, 0.1, 21.45, 140, 0.9],
  ['potted_plant_04', 24.35, 0.1, 20.9, 70, 0.9],
  ['potted_plant_02', 39.72, 3.0, 8.45, 0, 0.45],
  // apto 10 (sala e cozinha, x 39,4–42,7 × z 2,9–8,6): modelos próprios, origem no meio da face de trás; sem largura = sem ajuste
  ['geladeira', 42.69, 3.0, 4.43, -90],              // parede da cozinha x = 42,69
  ['cozinha', 42.69, 3.0, 5.65, -90],                // bancada z 4,8–6,5
  ['aereo', 42.69, 3.0, 5.65, -90],
  ['sofa', 42.69, 3.0, 7.6, -90],
  ['quadro_sol', 42.69, 4.45, 7.3, -90],             // quadros: y = centro da moldura
  ['quadro_folhas', 42.69, 4.45, 7.9, -90],
  ['rack', 39.435, 3.0, 7.55, 90],                   // parede dos quartos x = 39,435
  ['tv', 39.435, 3.0, 7.55, 90],
  ['quadro_blocos', 39.435, 4.5, 4.52, 90],          // entre as portas dos quartos
  ['quadro_mare', 41.5, 4.5, 2.86, 0],               // parede do banho z = 2,86
  ['mesa', 40.6, 3.0, 5.75, 0],
  ['cadeira', 40.989, 3.0, 6.139, -135],
  ['cadeira', 40.211, 3.0, 6.139, 135],
  ['cadeira', 40.211, 3.0, 5.361, 45],
  ['cadeira', 40.989, 3.0, 5.361, -45],   // cadeiras nas diagonais, de frente para a mesa
];
// modelos próprios: madeira, inox e tecidos ganham os shaders do site; peça marcada com veio 'v' (extras do Blender) tem o veio na vertical
const OWN = {
  cozinha: 'cozinha/cozinha.glb', aereo: 'cozinha/aereo.glb', geladeira: 'cozinha/geladeira.glb',
  sofa: 'sala/sofa.glb', mesa: 'sala/mesa.glb', cadeira: 'sala/cadeira.glb', rack: 'sala/rack.glb', tv: 'sala/tv.glb',
  quadro_sol: 'sala/quadro_sol.glb', quadro_folhas: 'sala/quadro_folhas.glb', quadro_mare: 'sala/quadro_mare.glb', quadro_blocos: 'sala/quadro_blocos.glb',
};
const SWAP = {
  cz_madeira: ['wood', '#b98a5a'], md_escura: ['wood', '#5a3a24'], cz_inox: ['inox'], cz_cuba: ['inox'],
  tc_linho: ['fabric', '#e6dfd0'], tc_azul: ['fabric', '#7f93a3'], tc_terracota: ['fabric', '#b9714c'], tc_palha: ['fabric', '#c9a873'], pp_branco: ['fabric', '#f3efe6'],
};
// tecido cru: as almofadas da poltrona perdem o couro preto; o estampado floral do daybed vira linho
const LINEN = new THREE.Color('#d8cdb8');
function restyle(n, m) {
  if (m.name === 'modern_arm_chair_01_pillow') { m.map = null; m.color.copy(LINEN); m.roughness = 0.95; m.metalness = 0; }
}

export async function loadProps(world, env, onDone) {
  const group = new THREE.Group(); group.visible = false;
  world.root.add(group); world.props = group;
  group.add(buildInterior(world, env));
  const loader = new GLTFLoader(), cache = new Map(), swapped = new Map();
  const swap = (name) => { if (!swapped.has(name)) swapped.set(name, world.M.make(...SWAP[name])); return swapped.get(name); };
  const get = (n) => { if (!cache.has(n)) cache.set(n, loader.loadAsync(`assets/models/${OWN[n] ?? `${n}/${n}_1k.gltf`}`)); return cache.get(n); };
  await Promise.all(PROPS.map(async ([n, x, y, z, yaw, wMax]) => {
    let g;
    try { g = await get(n); } catch (e) { console.warn('móvel não carregou', n, e); return; }
    const o = g.scene.clone(true);
    o.traverse((m) => {
      if (!m.isMesh) return;
      m.castShadow = m.receiveShadow = true;
      if (SWAP[m.material.name]) { m.material = swap(m.material.name); m.geometry.computeBoundingBox(); pieceIds(m.geometry, m.geometry.boundingBox, m.userData.veio === 'v' ? 1 : undefined); }
      else { m.material = m.material.clone(); m.material.envMap = env; m.material.envMapIntensity = 0.55; restyle(n, m.material); }
      m.userData = { prop: true };
    });
    o.rotation.y = yaw * DEG;
    if (OWN[n]) { o.position.set(x, y, z); group.add(o); return; }
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
