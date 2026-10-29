// O mundo: o GLB do hotel agrupado por etapa de obra, materiais por cor hex, coqueiros e o entorno.
// A geometria do hotel é sempre a de referencia/modelo/hotel.glb; aqui só se trocam materiais e se agrupam peças.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const V = (x, y, z) => new THREE.Vector3(x, y, z);
const lin = (h) => new THREE.Color(h); // THREE.Color já converte hex sRGB para linear

// etapas: 0 existente, 1 gabarito, 2 fundações, 3 estrutura, 4 paredes, 5 telhados, 6 paisagismo, 7 inauguração
export const STAGES = [
  [-9, -9], [-9, -8], [0.3, 2.8], [2.8, 5.8], [5.8, 8.8], [8.8, 11.0], [11.0, 13.4], [13.4, 14.0],
];
export const MONTHS = 14;

// -------------------------------------------------------------------------------------------- ruído GLSL
const NOISE = `
  float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
  float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
  float fbm(vec2 p){ float s = 0., a = .5; mat2 m = mat2(1.6, 1.2, -1.2, 1.6); for (int i = 0; i < 5; i++){ s += a * vn(p); p = m * p; a *= .5; } return s; }
`;

// -------------------------------------------------------------------------------------------- remendos de shader
// Cada material do hotel recebe: corte de obra (descarta o que ainda não foi construído) + textura triplanar ou procedural.
function patch(mat, o) {
  const U = o.U; // uniforms próprios do grupo (uCut, uAxis, uBand)
  const kind = o.kind;
  mat.customProgramCacheKey = () => 'hc-' + kind + (U ? '-cut' : '');
  mat.onBeforeCompile = (s) => {
    Object.assign(s.uniforms, o.uniforms || {});
    if (U) Object.assign(s.uniforms, U);
    s.vertexShader = s.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWP; varying vec3 vWN;')
      .replace('#include <project_vertex>', '#include <project_vertex>\nvWP = (modelMatrix * vec4(transformed, 1.)).xyz; vWN = normalize(mat3(modelMatrix) * objectNormal);');
    let head = 'varying vec3 vWP; varying vec3 vWN;\n' + NOISE;
    if (U) head += 'uniform float uCut, uBand; uniform vec3 uAxis;\n';
    head += o.head || '';
    s.fragmentShader = s.fragmentShader.replace('#include <common>', '#include <common>\n' + head);
    if (U) s.fragmentShader = s.fragmentShader.replace('void main() {', 'void main() {\n  float cutD = uCut - dot(vWP, uAxis); if (cutD < 0.) discard;');
    if (o.color) s.fragmentShader = s.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n' + o.color);
    if (o.normal) s.fragmentShader = s.fragmentShader.replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\n' + o.normal);
    if (o.rough) s.fragmentShader = s.fragmentShader.replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n' + o.rough);
    if (U) s.fragmentShader = s.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance += vec3(1.0, .55, .18) * uBand * exp(-cutD * 9.);');
  };
}
function depthPatch(U) {
  const m = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  m.customProgramCacheKey = () => 'hc-depth-cut';
  m.onBeforeCompile = (s) => {
    Object.assign(s.uniforms, U);
    s.vertexShader = s.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWP;')
      .replace('#include <project_vertex>', '#include <project_vertex>\nvWP = (modelMatrix * vec4(transformed, 1.)).xyz;');
    s.fragmentShader = s.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vWP; uniform float uCut; uniform vec3 uAxis;')
      .replace('void main() {', 'void main() {\n  if (uCut - dot(vWP, uAxis) < 0.) discard;');
  };
  return m;
}

const TRI = `
  vec3 triTex(sampler2D t, float sc){
    vec3 b = pow(abs(vWN), vec3(4.)); b /= (b.x + b.y + b.z);
    return texture2D(t, vec2(vWP.z, vWP.y * .35) * sc).rgb * b.x + texture2D(t, vWP.xz * sc).rgb * b.y + texture2D(t, vec2(vWP.x, vWP.y * .35) * sc).rgb * b.z;
  }`;
const TRI_PLASTER = `
  vec3 triTex(sampler2D t, float sc){
    vec3 b = pow(abs(vWN), vec3(4.)); b /= (b.x + b.y + b.z);
    return texture2D(t, vWP.zy * sc).rgb * b.x + texture2D(t, vWP.xz * sc).rgb * b.y + texture2D(t, vWP.xy * sc).rgb * b.z;
  }`;

// -------------------------------------------------------------------------------------------- materiais
export function makeMaterials(T, env) {
  const M = {};
  const std = (c, r = 0.85, extra = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: 0, envMap: env, envMapIntensity: 0.6, ...extra });
  M.make = (kind, hex, U) => {
    let m;
    if (kind === 'plaster') {
      m = std(hex, 0.92);
      patch(m, { kind, U, uniforms: { uTex: { value: T.plaster }, uTexR: { value: T.plasterR } }, head: 'uniform sampler2D uTex, uTexR;' + TRI_PLASTER,
        color: 'vec3 tx = triTex(uTex, .45); diffuseColor.rgb *= mix(vec3(1.), tx / vec3(.691, .659, .613), .55); diffuseColor.rgb *= .94 + .1 * fbm(vWP.xz * .4 + vWP.y * .3);',
        rough: 'roughnessFactor = .78 + .22 * triTex(uTexR, .45).r;' });
    } else if (kind === 'wood') {
      m = std(hex, 0.62);
      patch(m, { kind, U, uniforms: { uTex: { value: T.oak } }, head: 'uniform sampler2D uTex;' + TRI,
        color: 'vec3 tx = triTex(uTex, .55); diffuseColor.rgb *= mix(vec3(1.), tx / vec3(.565, .475, .385), .85);' });
    } else if (kind === 'cement') {
      m = std('#b9b5ad', 0.55);
      patch(m, { kind, U, color: 'float n = fbm(vWP.xz * .9) * .6 + fbm(vWP.xz * 6.) * .4; diffuseColor.rgb *= .78 + .34 * n;' });
    } else if (kind === 'stone') {
      m = std(hex, 0.8);
      patch(m, { kind, U, color: 'float n = fbm(vWP.xz * 2.5); diffuseColor.rgb *= .82 + .3 * n;' });
    } else if (kind === 'thatch') {
      m = std('#ffffff', 1.0);
      patch(m, { kind, U, uniforms: { uA: { value: lin('#6e5837') }, uB: { value: lin('#cdb383') } }, head: 'uniform vec3 uA, uB;',
        color: `vec3 n = normalize(vWN); vec3 t = normalize(cross(n, vec3(0., 1., 0.)) + vec3(1e-4)); vec3 sl = cross(t, n);
          float u = dot(vWP, t), v = dot(vWP, sl);
          float fib = fbm(vec2(u * 38., v * 1.4)) * .7 + vn(vec2(u * 140., v * 3.)) * .3;
          float row = fract(v * 3.1 + vn(vec2(u * 2.5, 0.)) * .35);
          vec3 c = mix(uA, uB, smoothstep(.25, .78, fib));
          c *= mix(1., .55, smoothstep(.8, .99, row));
          c *= .82 + .3 * fbm(vWP.xz * .35);
          diffuseColor.rgb = c;`,
        normal: 'if ((vec4(normal, 0.) * viewMatrix).y < 0.) normal = -normal;' });
    } else if (kind === 'sand') {
      m = std('#ffffff', 0.97);
      patch(m, { kind, U, uniforms: { uS: { value: lin('#dcc59c') }, uG: { value: lin('#6d7f3c') }, uD: { value: lin('#a89064') }, uOut: { value: 0 } }, head: 'uniform vec3 uS, uG, uD; uniform float uOut;',
        color: `float big = fbm(vWP.xz * .045 + 3.1), mid = fbm(vWP.xz * .5), fine = vn(vWP.xz * 18.);
          vec3 c = uS * (.86 + .2 * mid) * (.93 + .14 * fine);
          float far = smoothstep(4., 14., max(max(-vWP.x, vWP.x - 53.), max(-vWP.z, vWP.z - 23.)));
          float veg = smoothstep(.47, .62, big + .25 * mid) * uOut * far;
          c = mix(c, uD * (.8 + .3 * mid), smoothstep(.35, .5, big) * .35 * uOut * far);
          c = mix(c, uG * (.7 + .5 * mid) * (.85 + .3 * fine), veg);
          float beach = smoothstep(-120., -150., vWP.z);
          c = mix(c, uS * 1.08 * (.92 + .1 * fine), beach * uOut);
          diffuseColor.rgb = c;` });
    } else if (kind === 'grass') {
      m = std('#ffffff', 0.95);
      patch(m, { kind, U, uniforms: { uA: { value: lin('#4f7d2c') }, uB: { value: lin('#86a64a') } }, head: 'uniform vec3 uA, uB;',
        color: `float n = fbm(vWP.xz * .6), f = vn(vWP.xz * 40.), g = vn(vWP.xz * 9.);
          diffuseColor.rgb = mix(uA, uB, smoothstep(.3, .75, n * .7 + g * .3)) * (.8 + .35 * f);` });
    } else if (kind === 'water') {
      m = new THREE.MeshPhysicalMaterial({ color: '#2cb6bf', roughness: 0.04, metalness: 0, envMap: env, envMapIntensity: 1.25, clearcoat: 0.4, clearcoatRoughness: 0.05 });
      patch(m, { kind, U, uniforms: { uTime: T.time }, head: 'uniform float uTime;',
        color: 'float w = fbm(vWP.xz * 1.8 + uTime * .05); diffuseColor.rgb *= .85 + .3 * w; float edge = smoothstep(.0, 1.2, fbm(vWP.xz * .7)); diffuseColor.rgb = mix(diffuseColor.rgb, vec3(.55, .85, .86), .12 * edge);',
        normal: `vec2 q = vWP.xz * 2.2; float e = .06; float h0 = fbm(q + uTime * .15), hx = fbm(q + vec2(e, 0.) + uTime * .15), hz = fbm(q + vec2(0., e) + uTime * .15);
          vec3 nW = normalize(vec3(-(hx - h0) / e * .07, 1., -(hz - h0) / e * .07)); normal = normalize((viewMatrix * vec4(nW, 0.)).xyz);` });
    } else if (kind === 'glass') {
      m = new THREE.MeshPhysicalMaterial({ color: '#cfe6ec', roughness: 0.05, metalness: 0, transparent: true, opacity: 0.28, envMap: env, envMapIntensity: 1.2, depthWrite: false, side: THREE.DoubleSide });
      patch(m, { kind, U });
    } else if (kind === 'glow') {
      m = new THREE.MeshStandardMaterial({ color: '#fff1d6', emissive: '#ffbf73', emissiveIntensity: 0.4, roughness: 0.6 });
      patch(m, { kind, U });
      M.glows = M.glows || []; M.glows.push(m);
    } else if (kind === 'leaf') {
      m = std(hex, 0.8);
      patch(m, { kind, U, color: 'diffuseColor.rgb *= .75 + .45 * fbm(vWP.xz * 3. + vWP.y * 2.);' });
    } else if (kind === 'line') {
      m = std('#7b5e3a', 0.9);
      patch(m, { kind, U });
    } else {
      m = std(hex, kind === 'fabric' ? 0.95 : 0.75);
      patch(m, { kind: 'flat', U });
    }
    return m;
  };
  return M;
}

// -------------------------------------------------------------------------------------------- classificação das peças do GLB
// por índice de material (Material_N) e posição: etapa, tipo de material, modo de crescimento, classe no nanquim
// classes do nanquim: 0 construção, 1 grama, 2 água, 3 palha, 4 vidro, 5 areia, 6 folhagem
function classify(k, bb, hex) {
  const y0 = bb.min.y, y1 = bb.max.y;
  const C = (stage, kind, mode = 'y', ink = 0) => ({ stage, kind, mode, ink });
  if (k === 70) return C(0, 'sand', 'none', 5);
  if (k === 1 || k === 2) return C(0, 'sand', 'none', 5);
  if (k === 3) return C(6, 'grass', 'x', 1);
  if (k === 0 || k === 4) return C(2, 'plaster');
  if (k === 5) return y1 < 0.12 ? C(6, 'flat', 'x') : C(3, 'plaster');
  if (k === 6) return C(6, 'stone', 'x');
  if (k >= 7 && k <= 14) return C(7, 'flat', 'x');
  if (k === 15) return C(3, 'wood');
  if (k === 16) return C(5, 'wood');
  if (k === 17) return C(2, 'wood');
  if (k === 18) return y0 < 0.5 ? C(2, 'cement') : C(3, 'cement');
  if (k === 19) return C(3, 'plaster');
  if (k === 20) return C(4, 'plaster');
  if (k === 21) return C(4, 'wood');
  if (k === 22) return C(4, 'glass', 'y', 4);
  if (k === 23) return C(4, 'wood');
  if (k === 24 || k === 25) return C(6, 'keep');
  if (k >= 26 && k <= 38) return C(6, 'flat');
  if (k === 39) return C(5, 'thatch', 'y', 3);
  if (k === 40) return C(2, 'stone');
  if (k === 41) return C(3, 'wood');
  if (k === 42) return C(6, 'plaster');
  if (k === 60) return y0 > 3 ? null : C(6, 'leaf', 'y', 6);
  if (k === 57 || k === 65) return C(6, 'leaf', 'y', 6);
  if (k === 63) return C(6, 'glow');
  if (k === 66) return C(6, 'stone', 'x');
  if (k === 67) return C(6, 'water', 'x', 2);
  if (k === 69) return null;
  if ([45, 46, 47, 56, 61].includes(k)) return C(6, 'fabric');
  return C(6, 'flat');
}

// -------------------------------------------------------------------------------------------- coqueiro (receita de referencia/blender/cena2.py)
function rng(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
export function palmGeometry(H, seed, detail = 1) {
  const r = rng(seed), U = (a, b) => a + (b - a) * r();
  const inc = U(0.3, 0.9), az0 = U(0, 6.28), hd = V(Math.cos(az0), 0, Math.sin(az0));
  // tronco: anéis, levemente inclinado, base alargada
  const tp = [], tn = [], ti = [], tuv = [];
  const NS = 16, NR = 10;
  for (let k = 0; k <= NS; k++) {
    const t = k / NS, c = hd.clone().multiplyScalar(inc * t * t).add(V(0, H * t, 0));
    const rad = 0.19 * (1 - 0.4 * t) + 0.09 * Math.exp(-9 * t);
    for (let i = 0; i <= NR; i++) {
      const a = (i / NR) * Math.PI * 2;
      tp.push(c.x + Math.cos(a) * rad, c.y, c.z + Math.sin(a) * rad); tn.push(Math.cos(a), 0.15, Math.sin(a)); tuv.push(i / NR, c.y);
    }
  }
  for (let k = 0; k < NS; k++) for (let i = 0; i < NR; i++) {
    const a = k * (NR + 1) + i, b = a + NR + 1; ti.push(a, b, a + 1, a + 1, b, b + 1);
  }
  const trunk = new THREE.BufferGeometry();
  trunk.setAttribute('position', new THREE.Float32BufferAttribute(tp, 3)); trunk.setAttribute('normal', new THREE.Float32BufferAttribute(tn, 3));
  trunk.setAttribute('uv', new THREE.Float32BufferAttribute(tuv, 2)); trunk.setIndex(ti);
  // folhas: nervura + folíolos dos dois lados
  const C = hd.clone().multiplyScalar(inc).add(V(0, H, 0));
  const P = [], N = [], COL = [];
  const Y = V(0, 1, 0);
  const quad = (a, b, c, d, col) => {
    const n = new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(d, a)).normalize();
    if (n.y < 0) n.negate();
    for (const p of [a, b, c, a, c, d]) { P.push(p.x, p.y, p.z); N.push(n.x, n.y, n.z); COL.push(col[0], col[1], col[2]); }
  };
  const NF = detail > 0.7 ? 24 : 16, NL = Math.round(56 * detail), Mseg = detail > 0.7 ? 14 : 8;
  for (let i = 0; i < NF; i++) {
    const u = i / (NF - 1), az = i * 2.39996 + U(-0.25, 0.25);
    const e = (80 - 92 * Math.pow(u, 0.9) + U(-6, 6)) * Math.PI / 180;
    const L = (2.2 + 1.1 * Math.min(1, u * 1.8)) * U(0.88, 1.08) * Math.pow(H / 6.5, 0.3), dr = (0.3 + 0.3 * u) * U(0.8, 1.2);
    const h = V(Math.cos(az), 0, Math.sin(az));
    const dry = u > 0.85 && r() < 0.5; // folhas velhas, mais secas
    const base = dry ? [0.42, 0.36, 0.16] : [0.16 + U(-0.02, 0.03), 0.30 + U(-0.03, 0.04), 0.07];
    const pts = []; for (let j = 0; j <= Mseg; j++) { const s = j / Mseg; pts.push(C.clone().addScaledVector(h, L * s * Math.cos(e)).addScaledVector(Y, L * s * Math.sin(e) - dr * L * Math.pow(s, 2.3))); }
    const at = (s) => { const x = s * Mseg, j = Math.min(Mseg - 1, Math.floor(x)); return [pts[j].clone().lerp(pts[j + 1], x - j), pts[j + 1].clone().sub(pts[j]).normalize()]; };
    for (let j = 0; j < Mseg; j++) {
      const T = pts[j + 1].clone().sub(pts[j]).normalize(); let sd = T.clone().cross(Y); if (sd.length() < 1e-4) sd = h.clone().cross(Y); sd.normalize();
      const w0 = 0.035 * (1 - j / Mseg) + 0.008, w1 = 0.035 * (1 - (j + 1) / Mseg) + 0.008;
      quad(pts[j].clone().addScaledVector(sd, -w0), pts[j].clone().addScaledVector(sd, w0), pts[j + 1].clone().addScaledVector(sd, w1), pts[j + 1].clone().addScaledVector(sd, -w1), [0.45, 0.42, 0.22]);
    }
    for (let q = 0; q < NL; q++) {
      const s = 0.1 + 0.9 * q / (NL - 1); const [p0, T] = at(s);
      let sd = T.clone().cross(Y); if (sd.length() < 1e-4) sd = h.clone().cross(Y); sd.normalize();
      const Nn = sd.clone().cross(T).normalize();
      const ll = (0.95 * Math.pow(Math.sin(Math.PI * (0.06 + 0.9 * s)), 0.7) + 0.12) * L / 3.4;
      for (const sg of [-1, 1]) {
        const d = sd.clone().multiplyScalar(sg * Math.cos(0.6)).addScaledVector(T, Math.sin(0.6)).normalize();
        const k = U(0.6, 1.25), w = 0.065 * (detail > 0.7 ? 1 : 1.6);
        const p1 = p0.clone().addScaledVector(d, ll * 0.5).addScaledVector(Nn, 0.1 * ll).addScaledVector(Y, -0.06 * ll * k);
        const p2 = p0.clone().addScaledVector(d, ll).addScaledVector(Nn, 0.02 * ll).addScaledVector(Y, -0.42 * ll * k);
        const tip = s > 0.8 ? 0.7 : 1, cv = U(0.85, 1.15);
        const c1 = [base[0] * cv, base[1] * cv, base[2] * cv], c2 = [base[0] * cv * 1.25 + 0.05 * tip, base[1] * cv * 1.12, base[2] * cv];
        quad(p0.clone().addScaledVector(T, -w / 2), p0.clone().addScaledVector(T, w / 2), p1.clone().addScaledVector(T, w / 2), p1.clone().addScaledVector(T, -w / 2), c1);
        quad(p1.clone().addScaledVector(T, -w / 2), p1.clone().addScaledVector(T, w / 2), p2.clone().addScaledVector(T, w * 0.12), p2.clone().addScaledVector(T, -w * 0.12), c2);
      }
    }
  }
  const leaves = new THREE.BufferGeometry();
  leaves.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); leaves.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3));
  leaves.setAttribute('color', new THREE.Float32BufferAttribute(COL, 3));
  // cocos
  const nuts = [];
  if (detail > 0.7) for (let i = 0; i < 6; i++) { const a = i * 1.1 + U(0, 0.4); const g = new THREE.SphereGeometry(0.11, 8, 6); g.translate(C.x + Math.cos(a) * 0.2, C.y - 0.25 - U(0, 0.15), C.z + Math.sin(a) * 0.2); nuts.push(g); }
  return { trunk, leaves, nuts: nuts.length ? mergeGeometries(nuts) : null, crown: C };
}

// -------------------------------------------------------------------------------------------- montagem
export async function buildWorld({ url, T, env, phone, onProgress }) {
  const gltf = await new GLTFLoader().loadAsync(url, (e) => onProgress && e.total && onProgress(e.loaded / e.total));
  const M = makeMaterials(T, env);
  const root = new THREE.Group();
  const buckets = new Map(), trunks = [];
  gltf.scene.updateMatrixWorld(true);
  const toRemove = [];
  gltf.scene.traverse((o) => { if (o.isLight) toRemove.push(o); });
  toRemove.forEach((o) => o.parent.remove(o));
  gltf.scene.traverse((o) => {
    if (!o.isMesh) return;
    const assoc = gltf.parser.associations.get(o.material);
    const k = assoc ? assoc.materials : -1;
    const g = o.geometry.clone().applyMatrix4(o.matrixWorld);
    g.computeBoundingBox();
    const bb = g.boundingBox;
    if (k === 69) { trunks.push({ x: (bb.min.x + bb.max.x) / 2, z: (bb.min.z + bb.max.z) / 2, h: bb.max.y }); return; }
    const c = classify(k, bb, o.material.color && o.material.color.getHexString());
    if (!c) return;
    const key = `${k}|${c.stage}|${c.kind}|${c.mode}`;
    if (!buckets.has(key)) buckets.set(key, { k, c, geos: [], mat: o.material });
    // atributos uniformes para fundir
    for (const a of Object.keys(g.attributes)) if (!['position', 'normal', 'uv'].includes(a)) g.deleteAttribute(a);
    if (!g.attributes.uv) g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2));
    if (!g.index) { const n = g.attributes.position.count, idx = new Uint32Array(n); for (let i = 0; i < n; i++) idx[i] = i; g.setIndex(new THREE.BufferAttribute(idx, 1)); }
    if (o.matrixWorld.determinant() < 0) { const ix = g.index.array; for (let i = 0; i < ix.length; i += 3) { const t = ix[i + 1]; ix[i + 1] = ix[i + 2]; ix[i + 2] = t; } }
    buckets.get(key).geos.push(g);
  });
  const groups = [];
  for (const b of buckets.values()) {
    const geo = mergeGeometries(b.geos.map((g) => (g.index.array instanceof Uint32Array ? g : g.setIndex(new THREE.BufferAttribute(new Uint32Array(g.index.array), 1)))));
    if (b.k === 70) geo.translate(0, -0.03, 0);
    geo.computeBoundingBox();
    const bb = geo.boundingBox;
    const ax = b.c.mode === 'x' ? V(1, 0, 0) : V(0, 1, 0);
    const lo = b.c.mode === 'x' ? bb.min.x - 0.05 : bb.min.y - 0.05, hi = b.c.mode === 'x' ? bb.max.x + 0.05 : bb.max.y + 0.05;
    const U = { uCut: { value: 1e4 }, uAxis: { value: ax }, uBand: { value: 0 } };
    const hex = '#' + (b.mat.color ? b.mat.color.getHexString() : 'ffffff');
    let mat;
    if (b.c.kind === 'keep') { mat = b.mat; mat.metalness = 0; mat.roughness = 0.9; mat.envMap = env; mat.envMapIntensity = 0.5; patch(mat, { kind: 'keep', U }); }
    else mat = M.make(b.c.kind, hex, U);
    if (b.c.kind !== 'glass' && b.c.kind !== 'water' && b.k !== 70) { mat.side = THREE.DoubleSide; mat.shadowSide = THREE.DoubleSide; }
    const mesh = new THREE.Mesh(geo, mat);
    const flat = ['sand', 'grass', 'water'].includes(b.c.kind) || b.k === 6 || b.k === 66 || (b.k === 5 && b.c.stage === 6);
    mesh.castShadow = !flat && b.c.kind !== 'glass' && b.c.kind !== 'glow'; mesh.receiveShadow = true;
    if (b.c.kind === 'glass') mesh.renderOrder = 2;
    if (b.c.mode !== 'none') mesh.customDepthMaterial = depthPatch(U);
    mesh.userData = { stage: b.c.stage, ink: b.c.ink, U, lo, hi, mode: b.c.mode, k: b.k, kind: b.c.kind, hotel: true, noink: b.k === 70 };
    root.add(mesh); groups.push(mesh);
  }
  // o chão de fora usa a variação de restinga
  groups.filter((g) => g.userData.k === 70).forEach((g) => { g.material = M.make('sand', '#cdbf9f', g.userData.U); g.material.userData.out = 1; setOut(g.material); });

  // gabarito da obra (só na etapa 1): linha de estacas no perímetro do lote
  {
    const pts = [[0, 0], [53, 0], [53, 23], [2, 23], [2, 15.6], [0, 15.6], [0, 0]];
    const gs = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, z0] = pts[i], [x1, z1] = pts[i + 1]; const L = Math.hypot(x1 - x0, z1 - z0);
      const g = new THREE.BoxGeometry(L + 0.08, 0.06, 0.08); g.rotateY(-Math.atan2(z1 - z0, x1 - x0)); g.translate((x0 + x1) / 2, 0.45, (z0 + z1) / 2); gs.push(g);
      const n = Math.max(1, Math.round(L / 4));
      for (let j = 0; j <= n; j++) { const s = new THREE.BoxGeometry(0.07, 0.6, 0.07); s.translate(x0 + (x1 - x0) * j / n, 0.3, z0 + (z1 - z0) * j / n); gs.push(s); }
    }
    const U = { uCut: { value: 1e4 }, uAxis: { value: V(0, 1, 0) }, uBand: { value: 0 } };
    const m = new THREE.Mesh(mergeGeometries(gs.map((g) => g.toNonIndexed())), M.make('line', '#7b5e3a', U));
    m.castShadow = true; m.receiveShadow = true;
    m.userData = { stage: 1, ink: 0, U, lo: 0, hi: 1, mode: 'gone', hotel: true };
    root.add(m); groups.push(m);
  }

  // coqueiros do terreno: no lugar dos troncos do GLB, com folíolos
  const trunkMat = new THREE.MeshStandardMaterial({ color: '#8a6f4d', roughness: 0.95, metalness: 0 });
  patch(trunkMat, { kind: 'trunk', color: 'float ring = smoothstep(.55, .95, fract(vWP.y * 6.5 + vn(vWP.xz * 9.) * .3)); diffuseColor.rgb *= (.78 + .3 * fbm(vec2(atan(vWN.z, vWN.x) * 3., vWP.y * 4.))) * (1. - .28 * ring);' });
  const leafMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.75, metalness: 0, side: THREE.DoubleSide, envMap: env, envMapIntensity: 0.4 });
  const nutMat = new THREE.MeshStandardMaterial({ color: '#7d6a2c', roughness: 0.7, metalness: 0 });
  const palms = new THREE.Group();
  trunks.forEach((t, i) => {
    const p = palmGeometry(t.h + 1.2, 100 + i, phone ? 0.6 : 1);
    const g = new THREE.Group(); g.position.set(t.x, 0, t.z);
    const a = new THREE.Mesh(p.trunk, trunkMat), b = new THREE.Mesh(p.leaves, leafMat);
    a.castShadow = b.castShadow = true; a.receiveShadow = b.receiveShadow = true;
    a.userData = b.userData = { stage: 0, ink: 6, palm: true };
    g.add(a, b);
    if (p.nuts) { const c = new THREE.Mesh(p.nuts, nutMat); c.castShadow = true; c.userData = { stage: 0, ink: 6, palm: true }; g.add(c); }
    palms.add(g);
  });
  root.add(palms);

  // coqueiral de fundo fora dos muros + restinga baixa
  const bg = new THREE.Group(); bg.userData.bg = true;
  const r = rng(7);
  const vars = [7.5, 9, 10.5].map((h, k) => palmGeometry(h, 900 + k, phone ? 0.35 : 0.5));
  const NP = phone ? 90 : 170;
  const spots = [];
  while (spots.length < NP) {
    const x = -70 + r() * 210, z = -120 + r() * 230;
    if (x > -7 && x < 60 && z > -7 && z < 30) continue;   // o lote e uma folga
    if (x > -16 && x < -7 && z > -40 && z < 60) continue; // a rua de acesso
    if (z < -105) continue;                               // praia
    spots.push([x, z, r() * 6.28, 0.8 + r() * 0.4]);
  }
  vars.forEach((p, k) => {
    const mine = spots.filter((_, i) => i % 3 === k);
    const tr = new THREE.InstancedMesh(p.trunk, trunkMat, mine.length), lf = new THREE.InstancedMesh(p.leaves, leafMat, mine.length);
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion();
    mine.forEach(([x, z, a, s], i) => { q.setFromAxisAngle(V(0, 1, 0), a); m4.compose(V(x, 0, z), q, V(s, s, s)); tr.setMatrixAt(i, m4); lf.setMatrixAt(i, m4); });
    tr.castShadow = lf.castShadow = true;
    bg.add(tr, lf);
  });
  // restinga: moitas baixas, cada uma um tufo de 4 bolotas irregulares
  {
    const parts = [];
    for (let j = 0; j < 4; j++) {
      const sg = new THREE.SphereGeometry(1, 12, 8), a = j * 1.9, rr = j ? 0.75 : 0;
      const pa = sg.attributes.position;
      for (let i = 0; i < pa.count; i++) {
        const x = pa.getX(i), y = pa.getY(i), z = pa.getZ(i);
        const f = 1 + 0.18 * Math.sin(x * 5.1 + j) * Math.sin(z * 4.3 + y * 3.7) + 0.08 * Math.sin(y * 11 + x * 7);
        pa.setXYZ(i, x * f, Math.max(-0.35, y) * f, z * f);
      }
      const k = j ? 0.62 + 0.1 * j : 1; sg.scale(k, k * 0.8, k); sg.translate(Math.cos(a) * rr, -0.1 * j, Math.sin(a) * rr);
      parts.push(sg);
    }
    const g = mergeGeometries(parts); g.computeVertexNormals();
    const NB = phone ? 420 : 900;
    const mat = new THREE.MeshStandardMaterial({ roughness: 0.92, metalness: 0 });
    patch(mat, { kind: 'bush', color: 'float n = fbm(vWP.xz * 5. + vWP.y * 7.); diffuseColor.rgb *= .62 + .6 * n * n + .25 * smoothstep(.2, .9, vWN.y);' });
    const im = new THREE.InstancedMesh(g, mat, NB);
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color();
    const pal = ['#56692b', '#6a7434', '#4a5c29', '#7a7843', '#3f5426', '#617a35'];
    let n = 0;
    while (n < NB) {
      const near = r() < 0.4;
      let x, z;
      if (near) { const side = Math.floor(r() * 4); x = side < 2 ? -3 + r() * 62 : (side === 2 ? -4 - r() * 3 : 55 + r() * 4); z = side === 0 ? -1.2 - r() * 4 : side === 1 ? 24.2 + r() * 4 : -4 + r() * 32; }
      else { x = -70 + r() * 210; z = -110 + r() * 220; }
      if (x > -1.5 && x < 54.5 && z > -1 && z < 24) continue;
      if (x > -16 && x < -6 && z > -40 && z < 60) continue;
      const s = 0.3 + r() * (near ? 0.45 : 0.8);
      q.setFromAxisAngle(V(0, 1, 0), r() * 6.28);
      m4.compose(V(x, s * 0.3, z), q, V(s * (1 + r() * 0.6), s * (0.55 + r() * 0.3), s * (1 + r() * 0.6)));
      im.setMatrixAt(n, m4); im.setColorAt(n, col.set(pal[Math.floor(r() * pal.length)])); n++;
    }
    im.castShadow = true; im.receiveShadow = true;
    bg.add(im);
  }
  // chão distante, praia e mar
  {
    const U = { uCut: { value: 1e4 }, uAxis: { value: V(0, 1, 0) }, uBand: { value: 0 } };
    const gm = M.make('sand', '#cdbf9f', U); setOut(gm);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(5000, 5000).rotateX(-Math.PI / 2).translate(0, -0.08, 0), gm);
    ground.receiveShadow = true; bg.add(ground);
    const sea = new THREE.Mesh(new THREE.PlaneGeometry(6000, 3000).rotateX(-Math.PI / 2).translate(26, -0.02, -150 - 1500),
      new THREE.MeshStandardMaterial({ color: '#2d8ea3', roughness: 0.12, metalness: 0, envMap: env, envMapIntensity: 1.1 }));
    bg.add(sea);
  }
  root.add(bg);

  // grama em folhas no pátio (aparece no paisagismo)
  let blades = null;
  {
    const NB = phone ? 9000 : 32000;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute([-0.012, 0, 0, 0.012, 0, 0, 0.0, 1, 0.004], 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute([0, 0.3, 1, 0, 0.3, 1, 0, 0.3, 1], 3));
    const mat = new THREE.MeshStandardMaterial({ color: '#6f9a3c', roughness: 0.9, metalness: 0, side: THREE.DoubleSide });
    const Ub = { uGrow: { value: 0 } };
    mat.customProgramCacheKey = () => 'hc-blade';
    mat.onBeforeCompile = (s) => {
      Object.assign(s.uniforms, Ub);
      s.vertexShader = s.vertexShader.replace('#include <common>', '#include <common>\nuniform float uGrow; varying float vH;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\n vH = position.y; transformed.y *= uGrow;');
      s.fragmentShader = s.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vH;')
        .replace('#include <map_fragment>', '#include <map_fragment>\n diffuseColor.rgb *= mix(.45, 1.15, vH);');
    };
    const im = new THREE.InstancedMesh(g, mat, NB);
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), col = new THREE.Color();
    let n = 0;
    while (n < NB) {
      const x = 21.1 + r() * 29.8, z = 10.25 + r() * 5.5;
      const px = (x - 36.75) / 8.3, pz = (z - 13) / 1.95; if (px * px * px * px + pz * pz < 1.15) continue; // piscina
      if (x < 27.5 && z < 12.6 && x > 21.5 && z > 11) continue;
      e.set((r() - 0.5) * 0.5, r() * 6.28, (r() - 0.5) * 0.5); q.setFromEuler(e);
      const h = 0.05 + r() * 0.07;
      m4.compose(V(x, 0.0, z), q, V(1 + r(), h, 1)); im.setMatrixAt(n, m4);
      im.setColorAt(n, col.setHSL(0.24 + r() * 0.05, 0.45 + r() * 0.2, 0.32 + r() * 0.16)); n++;
    }
    im.receiveShadow = true; im.frustumCulled = false;
    im.userData = { stage: 6, blades: true, U: Ub };
    root.add(im); blades = im;
  }
  return { root, groups, palms, bg, blades, M, trunks };
}
function setOut(m) {
  const ob = m.onBeforeCompile;
  m.onBeforeCompile = (s, r) => { ob(s, r); s.uniforms.uOut.value = 1; };
  m.customProgramCacheKey = () => 'hc-sand-out';
}

// estado da obra num mês: corte de cada grupo
export function buildAt(world, month) {
  for (const g of world.groups) {
    const d = g.userData, [a, b] = STAGES[d.stage];
    if (d.stage === 0) { g.visible = true; d.U.uCut.value = 1e4; d.U.uBand.value = 0; continue; }
    if (d.mode === 'gone') { g.visible = month < 2.4; continue; }
    const t = Math.max(0, Math.min(1, (month - a) / (b - a)));
    g.visible = t > 0;
    const tt = d.mode === 'x' ? t : t;
    d.U.uCut.value = t >= 1 ? 1e4 : d.lo + (d.hi - d.lo) * tt;
    d.U.uBand.value = t > 0 && t < 1 && d.stage <= 5 ? 0.6 : 0;
  }
  if (world.blades) {
    const t = Math.max(0, Math.min(1, (month - 11.6) / 1.6));
    world.blades.visible = t > 0; world.blades.userData.U.uGrow.value = t;
  }
}
