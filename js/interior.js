// Peças feitas por código onde não há modelo pronto no estilo: cama do quarto e batentes do apto 10 (a bancada da cozinha virou assets/models/cozinha, feita por blender/cozinha.py).
// Coordenadas do GLB (apto 10 = módulo x 36–42,75 do bloco A, piso em y 3,0).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const Y0 = 3.0;
function stripes() {
  const c = document.createElement('canvas'); c.width = 256; c.height = 8; const g = c.getContext('2d');
  g.fillStyle = '#e9e4da'; g.fillRect(0, 0, 256, 8);
  [[18, 26, '#55687a'], [34, 38, '#55687a'], [60, 64, '#9aa7b1'], [190, 194, '#9aa7b1'], [216, 220, '#55687a'], [228, 236, '#55687a']].forEach(([a, b, col]) => { g.fillStyle = col; g.fillRect(a, 0, b - a, 8); });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

export function buildInterior(world, env) {
  const G = new THREE.Group();
  const U = () => ({ uCut: { value: 1e4 }, uAxis: { value: new THREE.Vector3(0, 1, 0) }, uBand: { value: 0 } });
  const mk = (kind, hex) => world.M.make(kind, hex, U());
  const std = (o) => new THREE.MeshStandardMaterial({ metalness: 0, envMap: env, envMapIntensity: 0.6, ...o });
  const M = {
    oak: mk('wood', '#b98a5a'), dark: mk('wood', '#5a3a24'), frame: mk('wood', '#4a2e1c'),
    black: std({ color: '#141414', roughness: 0.4 }),
    linen: mk('fabric', '#ece6da'), white: mk('fabric', '#f5f2eb'), sheet: mk('fabric', '#f1ede4'), accent: mk('fabric', '#8a9aa6'),
    throw: std({ map: stripes(), roughness: 0.95 }),
    shade: std({ color: '#f3e9d6', emissive: '#ffcf8f', emissiveIntensity: 0.9, roughness: 0.8 }), cer: std({ color: '#d9cbb4', roughness: 0.5 }),
  };
  const box = (w, h, d, x, y, z, m, rr = 0) => {
    const g = rr ? new RoundedBoxGeometry(w, h, d, 3, rr) : new THREE.BoxGeometry(w, h, d);
    const o = new THREE.Mesh(g, m); o.position.set(x, y + h / 2, z); o.castShadow = o.receiveShadow = true; G.add(o); return o;
  };
  const cyl = (r, h, x, y, z, m, r2 = r, seg = 24) => { const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r2, h, seg), m); o.position.set(x, y + h / 2, z); o.castShadow = o.receiveShadow = true; G.add(o); return o; };

  // ---- quarto 1: cama de casal com cabeceira em painel de madeira e criados flutuantes (cabeceira na parede x = 36,06)
  {
    const xw = 36.06, zc = 6.9, L = 2.0, Wd = 1.6;
    box(0.035, 1.05, 2.9, xw + 0.018, Y0 + 0.32, zc, M.oak);                                                     // painel
    for (let i = 0; i < 14; i++) box(0.012, 1.05, 0.006, xw + 0.04, Y0 + 0.32, zc - 1.45 + (i + 0.5) * 2.9 / 14, M.dark); // juntas do painel
    box(L, 0.26, Wd, xw + 0.04 + L / 2, Y0 + 0.04, zc, M.dark, 0.02);                                            // base
    box(L - 0.04, 0.22, Wd - 0.04, xw + 0.05 + L / 2, Y0 + 0.3, zc, M.white, 0.06);                              // colchão
    box(1.45, 0.07, Wd + 0.1, xw + 0.6 + 1.45 / 2, Y0 + 0.5, zc, M.linen, 0.035);                                // edredom
    [-1, 1].forEach((sg) => box(1.45, 0.3, 0.03, xw + 0.6 + 1.45 / 2, Y0 + 0.25, zc + sg * (Wd / 2 + 0.05), M.linen, 0.012)); // caimento
    box(0.03, 0.3, Wd + 0.1, xw + 2.06, Y0 + 0.25, zc, M.linen, 0.012);
    box(0.4, 0.075, Wd + 0.12, xw + 1.62, Y0 + 0.535, zc, M.throw, 0.03);                                         // manta listrada
    [-0.38, 0.38].forEach((dz) => { const p = box(0.42, 0.16, 0.66, xw + 0.33, Y0 + 0.52, zc + dz, M.white, 0.07); p.rotation.z = -0.35; p.scale.set(1, 1, 1); });
    const c = box(0.36, 0.14, 0.42, xw + 0.55, Y0 + 0.53, zc, M.accent, 0.06); c.rotation.z = -0.25;
    [5.75, 8.05].forEach((z) => {
      box(0.4, 0.05, 0.42, xw + 0.24, Y0 + 0.52, z, M.oak, 0.01);                                                // criado flutuante
      box(0.38, 0.12, 0.4, xw + 0.24, Y0 + 0.4, z, M.oak, 0.01);
      cyl(0.06, 0.18, xw + 0.24, Y0 + 0.57, z, M.cer, 0.075);                                                    // abajur de cerâmica
      cyl(0.1, 0.13, xw + 0.24, Y0 + 0.75, z, M.shade, 0.13);
    });
    box(0.9, 0.012, 1.4, xw + 2.55, Y0, zc, std({ color: '#b9a37c', roughness: 1 }), 0.005);                     // tapete de sisal
  }

  // ---- almofadas de linho no banco de madeira da recepção (chinese_sofa): assento e encosto. [x do centro, y do assento, z, sentido (+1 = frente para +x), escala]
  [[22.05, 0.1, 17.5, 1, 1]].forEach(([x, y, z, f, k]) => {
    const L = 1.95 * k, sy = y + 0.44 * k;
    box(0.55 * k, 0.1, L, x + f * 0.06 * k, sy, z, M.linen, 0.04);
    [-1, 1].forEach((sg) => { const c = box(0.14, 0.4 * k, L / 2 - 0.04, x - f * 0.26 * k, sy + 0.08, z + sg * L / 4, M.linen, 0.06); c.rotation.z = f * 0.18; });
  });

  // ---- batentes e maçanetas nas portas do apto 10
  const DOORS = [['x', 39.375, 3.1, 3.9], ['x', 39.375, 5.15, 5.95], ['z', 2.8, 39.6, 40.4], ['x', 42.75, 2.95, 3.85]];
  DOORS.forEach(([ax, p, a, b]) => {
    const t = 0.17, h = 2.1, j = 0.06;
    const put = (w, hh, d, u, y, v) => (ax === 'x' ? box(d, hh, w, p, y, u, M.frame) : box(w, hh, d, u, y, p, M.frame));
    put(j, h + j, t, a - j / 2, Y0, 0); G.children[G.children.length - 1].position[ax === 'x' ? 'z' : 'x'] = a - j / 2;
    put(j, h + j, t, b + j / 2, Y0, 0); G.children[G.children.length - 1].position[ax === 'x' ? 'z' : 'x'] = b + j / 2;
    put(b - a + 2 * j, j, t, (a + b) / 2, Y0 + h, 0); G.children[G.children.length - 1].position[ax === 'x' ? 'z' : 'x'] = (a + b) / 2;
    [-1, 1].forEach((sg) => {
      const u = b - 0.08, o = sg * 0.045;
      const k = ax === 'x' ? box(0.02, 0.02, 0.12, p + o, Y0 + 1.0, u - 0.05, M.black) : box(0.12, 0.02, 0.02, u - 0.05, Y0 + 1.0, p + o, M.black);
      k.castShadow = false;
    });
  });
  G.traverse((o) => { if (o.isMesh) o.userData = { prop: true }; });
  return G;
}
