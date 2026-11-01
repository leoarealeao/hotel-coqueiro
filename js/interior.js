// Peças feitas por código onde não há modelo pronto no estilo: almofadas do banco da recepção.
// (A cozinha, a sala, o quarto 1 e as portas do apto 10 viraram modelos em assets/models, feitos por blender/*.py.)
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

export function buildInterior(world, env) {
  const G = new THREE.Group();
  const U = () => ({ uCut: { value: 1e4 }, uAxis: { value: new THREE.Vector3(0, 1, 0) }, uBand: { value: 0 } });
  const mk = (kind, hex) => world.M.make(kind, hex, U());
  const M = { linen: mk('fabric', '#ece6da') };
  const box = (w, h, d, x, y, z, m, rr = 0) => {
    const g = rr ? new RoundedBoxGeometry(w, h, d, 3, rr) : new THREE.BoxGeometry(w, h, d);
    const o = new THREE.Mesh(g, m); o.position.set(x, y + h / 2, z); o.castShadow = o.receiveShadow = true; G.add(o); return o;
  };

  // ---- almofadas de linho no banco de madeira da recepção (chinese_sofa): assento e encosto. [x do centro, y do assento, z, sentido (+1 = frente para +x), escala]
  [[22.05, 0.1, 17.5, 1, 1]].forEach(([x, y, z, f, k]) => {
    const L = 1.95 * k, sy = y + 0.44 * k;
    box(0.55 * k, 0.1, L, x + f * 0.06 * k, sy, z, M.linen, 0.04);
    [-1, 1].forEach((sg) => { const c = box(0.14, 0.4 * k, L / 2 - 0.04, x - f * 0.26 * k, sy + 0.08, z + sg * L / 4, M.linen, 0.06); c.rotation.z = f * 0.18; });
  });

  G.traverse((o) => { if (o.isMesh) o.userData = { prop: true }; });
  return G;
}
