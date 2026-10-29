// Hotel Praia do Coqueiro: a obra num scroll.
// A prancha em nanquim mostra seis etapas da obra (o próprio GLB por lente de 2°). O scroll mergulha na prancha 01,
// o terreno real entra por trás do desenho, o scroll vira o calendário e o hotel sobe; no fim, caminhada até o apto 10.
// Técnica baseada em "Flat to 3D / 04 Build Time-Lapse" (c) 2026 Samnang Aing, MIT — ver js/LICENSE-flat-to-3d.txt.
//   ?v=12.5  pula para uma posição do scroll (em alturas de tela)    ?still  sem animação de abertura
//   ?offline a página espera window.__render(v) para cada quadro (screenshots e vídeo)
import * as THREE from 'three';
import { buildWorld, buildAt, STAGES, MONTHS, V } from './world.js';
import { makeInk, aim, toK, lerpK } from './ink.js';

const Q = new URLSearchParams(location.search);
const STILL = Q.has('still') || Q.has('offline'), OFFLINE = Q.has('offline');
const PHONE = Math.min(innerWidth, innerHeight) <= 700;
const DPR = Math.min(+(Q.get('dpr') || devicePixelRatio || 1), PHONE ? 2 : 1.5);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const sm = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const C = (h) => new THREE.Color(h);
const $ = (s) => document.querySelector(s);
const loadbar = $('#loadbar');
const prog = (p) => { loadbar.style.width = Math.round(p * 100) + '%'; };

// ---------------------------------------------------------------- renderer
const canvas = $('#gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance', preserveDrawingBuffer: OFFLINE });
renderer.setPixelRatio(DPR);
renderer.setSize(innerWidth, innerHeight, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.shadowMap.autoUpdate = false;

// ---------------------------------------------------------------- céu (adaptado do 04): degradê, brilho do sol e poucas nuvens
const SUN_AM = V(0.45, 0.78, -0.43).normalize(), SUN_PM = V(-0.5, 0.25, 0.83).normalize();
const SKY = { am: { zen: C('#3f78b8'), hor: C('#dfe3e0'), glow: C('#ffe2b0') }, pm: { zen: C('#4c79ad'), hor: C('#f0d9b8'), glow: C('#ffb066') } };
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { uSun: { value: SUN_AM.clone() }, uZen: { value: SKY.am.zen.clone() }, uHor: { value: SKY.am.hor.clone() }, uGlow: { value: SKY.am.glow.clone() }, uGround: { value: C('#8d8063') }, uEnv: { value: 0 } },
  vertexShader: 'varying vec3 vD; void main(){ vD = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
  fragmentShader: `uniform vec3 uSun, uZen, uHor, uGlow, uGround; uniform float uEnv; varying vec3 vD;
    float h2(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5); }
    void main(){ vec3 d = normalize(vD); float h = d.y;
      vec3 c = mix(uHor, uZen, pow(smoothstep(-.02, .5, h), .55));
      vec2 q = d.xz / max(d.y + .08, .03) * 1.3 + vec2(3.1, 7.4);
      float n = 0., a = .55; mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
      for (int i = 0; i < 5; i++) { vec2 f = fract(q), ip = floor(q); f = f * f * (3. - 2. * f);
        n += a * mix(mix(h2(ip), h2(ip + vec2(1, 0)), f.x), mix(h2(ip + vec2(0, 1)), h2(ip + vec2(1, 1)), f.x), f.y); q = m * q; a *= .5; }
      float cl = smoothstep(.6, .84, n) * smoothstep(.02, .1, h) * (1. - smoothstep(.3, .65, h)) * (1. - uEnv);
      c = mix(c, mix(uHor * 1.05, vec3(1.), .55) * (.9 + .12 * smoothstep(.6, .9, n)), cl * .8);
      float s = max(dot(d, uSun), 0.);
      c += uGlow * (pow(s, 6.) * .35 + pow(s, 80.) * .9) * smoothstep(-.1, .15, h);
      if (uEnv > .5) c = mix(uGround, c, smoothstep(-.06, .02, h));
      gl_FragColor = vec4(c, 1.); }`,
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), skyMat);
sky.scale.setScalar(3000); sky.renderOrder = -1; sky.frustumCulled = false;

const pmrem = new THREE.PMREMGenerator(renderer);
const envScene = new THREE.Scene(); envScene.add(new THREE.Mesh(new THREE.SphereGeometry(40, 48, 24), skyMat));
let envRT = null;
function bakeEnv() {
  skyMat.uniforms.uEnv.value = 1;
  const rt = pmrem.fromScene(envScene, 0.02);
  skyMat.uniforms.uEnv.value = 0;
  if (envRT) envRT.dispose();
  envRT = rt; return rt.texture;
}
const ENV = bakeEnv();

// ---------------------------------------------------------------- texturas CC0 e o mundo
const tl = new THREE.TextureLoader();
const tex = async (u, srgb) => { const t = await tl.loadAsync(u); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4; if (srgb) t.colorSpace = THREE.SRGBColorSpace; return t; };
const [plaster, plasterR, oak] = await Promise.all([
  tex('assets/textures/plastered_wall_diff_1k.jpg', true), tex('assets/textures/plastered_wall_rough_1k.jpg', false), tex('assets/textures/white_oak_veneer_diff_1k.jpg', true),
]);
prog(0.1);
const T = { plaster, plasterR, oak, time: { value: 0 } };
const world = await buildWorld({ url: 'referencia/modelo/hotel.glb', T, env: ENV, phone: PHONE, onProgress: (p) => prog(0.1 + p * 0.75) });
prog(0.88);
const scene = new THREE.Scene();
scene.add(world.root, sky);
scene.fog = new THREE.Fog(SKY.am.hor.clone(), 200, 1500);

const sun = new THREE.DirectionalLight(0xffe9cf, 3.0);
const sunAt = V(27, 0, 11.5);
sun.target.position.copy(sunAt);
sun.castShadow = true; sun.shadow.mapSize.set(PHONE ? 2048 : 4096, PHONE ? 2048 : 4096);
Object.assign(sun.shadow.camera, { left: -46, right: 46, top: 46, bottom: -46, near: 20, far: 300 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
const hemi = new THREE.HemisphereLight(0xcfe0f0, 0x9a8a6a, 0.7);
scene.add(sun, sun.target, hemi);
// luz quente dos interiores que a caminhada visita (apto 10, recepção)
const lamps = [[41.0, 5.3, 6.0, 1.0], [37.7, 5.3, 6.8, 0.8], [24.4, 2.4, 18.8, 1.2]].map(([x, y, z, k]) => {
  const p = new THREE.PointLight(0xffb873, 0, 7, 2); p.position.set(x, y, z); p.userData.k = k; scene.add(p); return p;
});

// ---------------------------------------------------------------- roteiro
// a planta: o GLB visto de cima por lente de 2°, cortado a 1,30 m; o mar fica em cima
const KP = (r) => (r.w >= r.h
  ? { T: V(26.5, 0, 11.5), az: 90, el: 89.6, h: Math.max(23 * 0.58, 53 * 0.55 / (r.w / r.h)), fov: 2 }
  : { T: V(26.5, 0, 11.0), az: 180, el: 89.6, h: Math.max(53 * 0.54, 23 * 0.6 / (r.w / r.h)), fov: 2 }); // celular: a planta em pé, mar à esquerda
const K1 = { T: V(26.5, 0.5, 11.5), az: -142, el: 30, h: PHONE ? 30 : 15.5, fov: 2 }; // axonométrica do lote, tela cheia
const Z = { tilt: [0.3, 1.3], rewind: [1.3, 1.85], pour: [1.85, 2.55], lens: [2.35, 3.2], build: [3.2, 10.0], walk: 10.0, end: [20.7, 21.6], total: 21.8 };
const INK_STAGE = ['', 'Terreno vazio', 'Fundações', 'Estrutura', 'Paredes', 'Telhados de palha', 'Paisagismo e piscina', 'Paisagismo e piscina'];
const KEYS = [
  // a obra: do alto, depois no meio do pátio enquanto as paredes sobem, depois os telhados
  [3.2, -1, 9, 5, 27, 2, 13.5, 50],
  [4.4, 5, 16, -10, 28, 0, 12, 50],
  [5.5, 21.5, 1.75, 13.0, 40, 2.4, 12.6, 56],
  [6.6, 32.5, 1.75, 13.4, 44, 3.4, 8.2, 58],
  [7.5, 40.5, 1.8, 13.2, 30, 3.6, 18.8, 58],
  [8.7, 60, 15, 27, 33, 2, 11, 50],
  [9.4, 14, 9, 31, 26, 1, 12, 52],
  // caminhada (câmeras de referencia/modelo/cameras.json + passagens)
  [10.0, 11, 1.65, 13.4, 28, 1.6, 13.2, 52],                 // estacionamento
  [10.9, 11.5, 1.75, 8.3, 27, 2.9, 17.3, 58],                // vista_da_recepcao
  [11.8, 19.4, 1.65, 16.3, 26, 1.35, 19.8, 62],              // dentro da recepção
  [12.6, 19.5, 1.6, 13, 40, 1.5, 13, 55],                    // entrada_patio
  [13.6, 27.5, 1.6, 13.6, 48, 1.6, 12.8, 55],                // piscina
  [14.4, 35.5, 1.7, 15.2, 39.5, 4, 9, 55],                   // olhando_varanda
  [15.0, 43.5, 1.65, 11.4, 43.5, 3.0, 6.5, 60],              // pé da escada
  [15.6, 43.5, 4.62, 5.7, 43.5, 4.6, 2.4, 62],               // topo da escada
  [16.0, 43.5, 4.62, 3.45, 40, 4.45, 3.4, 62],               // patamar, porta do apto 10
  [16.4, 41.7, 4.6, 3.45, 41.0, 4.3, 9.5, 66],               // entra pela sala
  [16.8, 41.0, 4.6, 7.9, 41.6, 4.2, 12, 66],
  [17.1, 40.9, 4.68, 9.6, 44, 4.1, 12.6, 65],                // sai para a varanda
  [17.5, 37.3, 4.8, 9.95, 46, 3.3, 13.6, 65],                // varanda_apto
  [17.9, 40.9, 4.62, 9.3, 41.2, 4.2, 4, 68],
  [18.3, 40.2, 4.52, 3.1, 41.3, 4.12, 10.2, 70],             // sala
  [18.7, 40.4, 4.55, 5.55, 37, 4.2, 5.6, 70],
  [19.1, 39.1, 4.57, 5.25, 36.7, 3.77, 8.5, 70],             // quarto
  [19.5, 37.7, 4.6, 8.1, 37.7, 4.4, 12, 68],
  [19.85, 37.7, 4.75, 10.6, 40, 3, 13.5, 62],
  [20.2, 41, 5.1, 13.2, 38, 2, 13, 62],
  [20.7, 50.3, 10.5, 13, 30, 1, 13, 62],                     // final_do_fundo
  [21.8, 52.5, 13, 13, 30, 1, 13, 62],
];
const pathP = new THREE.CatmullRomCurve3(KEYS.map((k) => V(k[1], k[2], k[3])), false, 'centripetal');
const pathL = new THREE.CatmullRomCurve3(KEYS.map((k) => V(k[4], k[5], k[6])), false, 'centripetal');
const wideFov = (f) => (innerWidth < innerHeight ? 2 * Math.atan(Math.tan(f * Math.PI / 360) * 1.45) * 180 / Math.PI : f);
function pathAt(v) {
  v = clamp(v, KEYS[0][0], KEYS[KEYS.length - 1][0]);
  let i = 0; while (i < KEYS.length - 2 && v > KEYS[i + 1][0]) i++;
  const f = (v - KEYS[i][0]) / (KEYS[i + 1][0] - KEYS[i][0]);
  const fe = lerp(f, ease(f), 0.3);
  const u = (i + fe) / (KEYS.length - 1);
  return { P: pathP.getPoint(u), L: pathL.getPoint(u), fov: wideFov(lerp(KEYS[i][7], KEYS[i + 1][7], fe)) };
}
const KA = (() => { const w = pathAt(Z.build[0]); return toK(w.P, w.L, w.fov); })();
const monthAt = (v) => clamp((v - Z.build[0]) / (Z.build[1] - Z.build[0]), 0, 1) * MONTHS;

// ---------------------------------------------------------------- nanquim
const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 5000);
const ink = makeInk(renderer, scene, cam, { samples: PHONE ? 0 : 4 });
let W = innerWidth, H = innerHeight;
ink.setSize(W, H, DPR);
const HIDE = [sky, world.bg, world.blades];

// ---------------------------------------------------------------- a prancha
const sheet = $('#sheet');
const pframe = $('#pframe');
let REST = null;
const measure = () => { const r = pframe.getBoundingClientRect(); REST = { x: r.left, y: r.top, w: r.width, h: r.height }; };
measure();
// rótulos da planta (numeração de referencia/plantas/planta_numerada.png)
const LABELS = [
  ...[[24.375, 1, 8], [32.625, 2, 9], [39.375, 3, 10], [47.625, 4, 11]].map(([x, a, b]) => [x, 4.95, `<b>${a}<small>+${b}</small></b><span>2 quartos · ~50 m²</span>`, '']),
  [24.375, 19.55, '<b>Recepção</b><span>aberta · em cima o 12</span>', 's'],
  ...[[32.625, 5, 13], [39.375, 6, 14], [47.625, 7, 15]].map(([x, a, b]) => [x, 19.55, `<b>${a}<small>+${b}</small></b><span>1 quarto · ~35 m²</span>`, '']),
  [36.75, 13, '<b>Piscina</b><span>15 × 2 m</span>', 's'],
  [8, 7.5, '<b>Estacionamento</b><span>6 vagas</span>', 's'],
  [26.5, -2.2, PHONE ? '<b>&larr; mar</b>' : '<b>&uarr; mar a ~200 m</b>', 's'],
];
const plabels = $('#plabels');
plabels.innerHTML = LABELS.map(([, , h, c]) => `<div class="lb ${c}">${h}</div>`).join('');
const lbEls = [...plabels.children], _v = new THREE.Vector3();

// cronograma
const ROWS = [['Fundações', 2], ['Estrutura', 3], ['Paredes', 4], ['Telhados de palha', 5], ['Paisagismo e piscina', 6], ['Inauguração', 7]];
$('#calrows').innerHTML = ROWS.map(([n, s]) => { const [a, b] = STAGES[s]; return `<div class="row"><span>${n}</span><div class="trk"><div class="plan" style="left:${a / MONTHS * 100}%;width:${(b - a) / MONTHS * 100}%"><div class="done"></div></div></div></div>`; }).join('') + '<div class="now" id="calnow"></div>';
const dones = [...document.querySelectorAll('#cal .done')], calnow = $('#calnow'), calm = $('#calm'), cal = $('#cal');
const stageName = (m) => (m < 0.3 ? 'Terreno vazio' : ROWS.reduce((n, [nm, s]) => (m >= STAGES[s][0] ? nm : n), 'Fundações'));
const pad = (n) => String(n).padStart(2, '0');
const chip = $('#chip'), hint = $('#hint'), cap = $('#cap'), says = [...document.querySelectorAll('.say')], scrim = $('#scrim'), endEl = $('#end');
const CAPS = [
  [10.0, 10.9, 'Estacionamento', '6 vagas · areia compactada'],
  [10.9, 12.25, 'Recepção', 'aberta, sob o apto 12'],
  [12.25, 13.2, 'Pátio', 'gramado entre coqueiros'],
  [13.2, 14.2, 'Piscina', 'reta · 15 × 2 m'],
  [14.2, 15.0, 'Bloco A', 'apartamentos de 2 quartos'],
  [15.0, 16.1, 'Escada', 'entrada dos aptos de cima'],
  [16.1, 17.75, 'Apto 10', 'varanda para a piscina'],
  [17.75, 18.6, 'Apto 10', 'sala e cozinha'],
  [18.6, 19.6, 'Apto 10', 'quarto'],
];

// ---------------------------------------------------------------- luz por mês
let shadowKey = '', envKey = '';
function lightFor(month) {
  const pm = sm(5, 13.5, month);
  const dir = SUN_AM.clone().lerp(SUN_PM, pm).normalize();
  sun.position.copy(sunAt).addScaledVector(dir, 150);
  sun.color.set(0xfff0dc).lerp(C('#ffc58a'), pm); sun.intensity = lerp(2.7, 3.3, pm);
  hemi.intensity = lerp(0.75, 0.68, pm);
  hemi.color.set(0xcfe0f0).lerp(C('#c9d6e6'), pm);
  skyMat.uniforms.uSun.value.copy(dir);
  skyMat.uniforms.uZen.value.copy(SKY.am.zen).lerp(SKY.pm.zen, pm);
  skyMat.uniforms.uHor.value.copy(SKY.am.hor).lerp(SKY.pm.hor, pm);
  skyMat.uniforms.uGlow.value.copy(SKY.am.glow).lerp(SKY.pm.glow, pm);
  scene.fog.color.copy(skyMat.uniforms.uHor.value);
  const on = sm(13.2, 14, month);
  (world.M.glows || []).forEach((m) => (m.emissiveIntensity = 0.3 + 3.2 * on));
  lamps.forEach((l) => (l.intensity = 6 * l.userData.k * on));
  const k = (Math.round(month * 40) / 40).toFixed(3);
  if (k !== shadowKey) { shadowKey = k; renderer.shadowMap.needsUpdate = true; }
  const ek = (Math.round(pm * 4) / 4).toFixed(2);
  if (ek !== envKey) { envKey = ek; const e = bakeEnv(); scene.traverse((o) => { if (o.material && o.material.envMap) { o.material.envMap = e; } }); }
}

// ---------------------------------------------------------------- aquecimento atrás do loader
buildAt(world, 0); lightFor(0);
aim(cam, KA, { x: 0, y: 0, w: W, h: H }, W, H);
renderer.compile(scene, cam);
for (const m of [0, 14]) { buildAt(world, m); lightFor(m); renderer.shadowMap.needsUpdate = true; aim(cam, KA, { x: 0, y: 0, w: W, h: H }, W, H); ink.real(); }
ink.draw([{ rect: REST, cam: KP(REST), stage: 7, clipY: 1.3 }], HIDE);
prog(1);
await document.fonts.ready;
$('#loader').classList.add('out');
document.body.classList.add('ready');

// ---------------------------------------------------------------- scroll
const track = $('#track');
track.style.height = (Z.total + 1) * 100 + 'vh';
if (Q.has('v')) { history.scrollRestoration = 'manual'; scrollTo(0, +Q.get('v') * innerHeight); }
let sv = scrollY / innerHeight, last = performance.now(), lastKey = '';
const heroT0 = performance.now() + 250;
const reveal = (i, now) => (STILL ? 1 : clamp((now - heroT0) / 1800, 0, 1));

function render(now, forceV) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  const target = forceV ?? clamp(scrollY / innerHeight, 0, Z.total);
  sv = forceV !== undefined || STILL ? target : sv + (target - sv) * (1 - Math.exp(-dt * 5));
  if (Math.abs(target - sv) < 1e-4) sv = target;
  T.time.value = OFFLINE ? sv * 4 : now / 1000;

  const c = sm(Z.tilt[0], Z.tilt[1], sv), rw = sm(Z.rewind[0], Z.rewind[1], sv);
  const pour = sm(Z.pour[0], Z.pour[1], sv), l = sm(Z.lens[0], Z.lens[1], sv);
  const realOnly = sv >= Z.pour[1];
  const month = monthAt(sv);
  let k;
  const kp = KP(REST);
  if (sv < Z.lens[0]) k = c > 0 ? lerpK(kp, K1, ease(c), { e: ease(sm(0.05, 0.9, c)) }) : kp;
  else if (sv < Z.build[0]) k = lerpK(K1, KA, l, { f: sm(0, 0.7, l), e: sm(0.15, 1, l), T: sm(0.1, 1, l), h: sm(0.1, 1, l) });
  else { const w = pathAt(sv); k = toK(w.P, w.L, w.fov); }
  buildAt(world, month); lightFor(month);

  // a planta cresce até a tela cheia enquanto inclina para a axonométrica
  sheet.style.opacity = 1 - sm(Z.tilt[0], Z.tilt[0] + 0.5, sv);
  sheet.style.visibility = sv > Z.tilt[0] + 0.55 ? 'hidden' : 'visible';
  const ce = ease(c);
  const rectL = { x: lerp(REST.x, 0, ce), y: lerp(REST.y, 0, ce), w: lerp(REST.w, W, ce), h: lerp(REST.h, H, ce) };
  const clipY = lerp(1.3, 80, sm(0.08, 0.6, c));
  const inkStage = Math.max(1, 7 - Math.floor(rw * 6.999));

  // textos
  const diving = sv > Z.tilt[0];
  hint.classList.toggle('on', !diving && reveal(0, now) >= 1);
  let chipTxt = '';
  if (sv > Z.build[0] - 0.4 && sv < Z.walk - 0.15) chipTxt = `Mês ${pad(Math.floor(month))} &nbsp;·&nbsp; <i>${stageName(month)}</i>`;
  else if (sv > Z.rewind[0] && sv < Z.build[0] - 0.4) chipTxt = `Etapa ${pad(Math.min(6, inkStage))} &nbsp;·&nbsp; <i>${INK_STAGE[inkStage]}</i>`;
  else if (sv > Z.tilt[0] + 0.3 && sv <= Z.rewind[0]) chipTxt = 'O hotel pronto &nbsp;·&nbsp; <i>agora, do zero</i>';
  if (chip.dataset.t !== chipTxt) { chip.innerHTML = chipTxt; chip.dataset.t = chipTxt; }
  chip.classList.toggle('on', !!chipTxt);
  cal.style.opacity = sm(Z.build[0] - 0.3, Z.build[0], sv) * (1 - sm(Z.walk - 0.2, Z.walk + 0.1, sv));
  calm.textContent = pad(Math.floor(month));
  calnow.style.left = `calc(138px + (100% - 138px) * ${month / MONTHS})`;
  if (PHONE) calnow.style.left = `calc(112px + (100% - 112px) * ${month / MONTHS})`;
  ROWS.forEach(([, st], i) => { const [a, b] = STAGES[st]; dones[i].style.transform = `scaleX(${clamp((month - a) / (b - a), 0, 1)})`; });
  let sayOn = false;
  let sayA = 0;
  says.forEach((e) => { const a = +e.dataset.a, b = +e.dataset.b, o = sm(a, a + 0.3, sv) * (1 - sm(b - 0.3, b, sv)); e.style.opacity = o; e.style.transform = `translateY(calc(-50% + ${(1 - o) * 14}px))`; sayOn = sayOn || o > 0.02; sayA = Math.max(sayA, o); });
  scrim.style.opacity = sayA;
  const cc = CAPS.find((x) => sv >= x[0] && sv < x[1]);
  const ct = cc ? cc[2] + '|' + cc[3] : '';
  if (cap.dataset.t !== ct) { cap.dataset.t = ct; if (cc) { cap.children[0].textContent = cc[2]; cap.children[1].textContent = cc[3]; } }
  cap.classList.toggle('on', !!cc && !sayOn);
  endEl.style.opacity = sm(Z.end[0], Z.end[0] + 0.4, sv);

  // desenho e terreno
  const rev = reveal(0, now);
  const key = [W, H, sv.toFixed(4), rev.toFixed(3)].join(',');
  if (key === lastKey) return;
  lastKey = key;
  const D = k.h / Math.tan(k.fov * Math.PI / 360);
  scene.fog.near = D + (k.fov < 10 ? 80 : 60); scene.fog.far = D + (k.fov < 10 ? 1200 : 900);
  if (!realOnly) {
    ink.draw([{ rect: rectL, cam: k, stage: inkStage, clipY, reveal: rev }], HIDE);
  }
  aim(cam, k, rectL, W, H);
  const lo = (1 - sm(Z.tilt[0], Z.tilt[0] + 0.3, sv)) * sm(0.6, 1, rev);
  plabels.style.opacity = lo;
  if (lo > 0) LABELS.forEach(([x, z], i) => { _v.set(x, 0.5, z).project(cam); lbEls[i].style.left = (_v.x + 1) / 2 * W + 'px'; lbEls[i].style.top = (1 - _v.y) / 2 * H + 'px'; });
  sky.position.copy(cam.position);
  if (pour > 0) ink.real();
  ink.show({ rect0: rectL, pour, realOnly, inkOver: 1 - sm(Z.pour[1] - 0.25, Z.pour[1], sv) });
}

function frame(now) { requestAnimationFrame(frame); render(now); }
if (!OFFLINE) requestAnimationFrame(frame);
window.__render = (v) => { lastKey = ''; render(performance.now(), v); return true; };
addEventListener('resize', () => {
  W = innerWidth; H = innerHeight;
  renderer.setSize(W, H, false); ink.setSize(W, H, DPR);
  measure(); lastKey = '';
});
window.__hc = { scene, cam, world, renderer, Z, KEYS };
window.__ready = true;
