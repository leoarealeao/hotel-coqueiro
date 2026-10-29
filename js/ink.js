// Nanquim sobre papel e a passagem para o terreno real.
// Ideia e função aim() adaptadas de "Flat to 3D / 04 Build Time-Lapse" (c) 2026 Samnang Aing, licença MIT
// (ver js/LICENSE-flat-to-3d.txt). Cada prancha é o mesmo modelo visto por uma lente de 2°, desenhada no seu retângulo.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';

const DEG = Math.PI / 180;

// câmera descrita pelo que olha: alvo T, azimute e elevação (graus), h = meia altura do quadro no alvo, fov.
// O quadro vai para o retângulo `rect` (px css) de uma tela W×H; o frustum se estende fora do centro para cobrir a tela.
export function aim(cam, s, rect, W, H) {
  const t = Math.tan(s.fov * DEG / 2), D = s.h / t;
  const az = s.az * DEG, el = s.el * DEG;
  cam.position.set(s.T.x + Math.cos(el) * Math.cos(az) * D, s.T.y + Math.sin(el) * D, s.T.z + Math.cos(el) * Math.sin(az) * D);
  cam.up.set(0, 1, 0); cam.lookAt(s.T); cam.updateMatrixWorld();
  const near = Math.max(0.08, D - 200), far = D + (s.fov < 10 ? 260 : 4000);
  const wy = t, wx = t * rect.w / rect.h;
  const u = (x) => ((x - rect.x) / rect.w * 2 - 1) * wx, v = (y) => (1 - (y - rect.y) / rect.h * 2) * wy;
  cam.projectionMatrix.makePerspective(u(0) * near, u(W) * near, v(0) * near, v(H) * near, near, far);
  cam.projectionMatrixInverse.copy(cam.projectionMatrix).invert();
  cam.near = near; cam.far = far; cam.userData.D = D;
  return cam;
}
export function toK(E, Tg, fov) {
  const d = E.clone().sub(Tg), D = d.length();
  return { T: Tg.clone(), az: Math.atan2(d.z, d.x) / DEG, el: Math.asin(d.y / D) / DEG, h: D * Math.tan(fov * DEG / 2), fov };
}
export function lerpK(a, b, t, o = {}) {
  const L = (x, y, k) => x + (y - x) * k;
  let daz = b.az - a.az; while (daz > 180) daz -= 360; while (daz < -180) daz += 360;
  const tf = o.f ?? t, te = o.e ?? t, tt = o.T ?? t, th = o.h ?? t;
  return { T: a.T.clone().lerp(b.T, tt), az: a.az + daz * te, el: L(a.el, b.el, te), h: Math.exp(L(Math.log(a.h), Math.log(b.h), th)), fov: Math.exp(L(Math.log(a.fov), Math.log(b.fov), tf)) };
}

// normal + classe; uClipY corta o modelo na altura da planta (1,3 m) e as faces de trás que aparecem no corte viram poché
const ND_VS = 'varying vec3 vN; varying float vY; void main(){ vN = normalize(normalMatrix * normal); vY = (modelMatrix * vec4(position, 1.)).y; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }';
const ND_VS_INST = 'varying vec3 vN; varying float vY; void main(){ vN = normalize(normalMatrix * mat3(instanceMatrix) * normal); vY = (modelMatrix * instanceMatrix * vec4(position, 1.)).y; gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4(position, 1.); }';
const ND_FS = 'uniform float uClass, uClipY, uPoche, uPocheOk; varying vec3 vN; varying float vY; void main(){ if (vY > uClipY) discard; vec3 n = normalize(vN); float c = uClass; if (!gl_FrontFacing) { n = -n; if (uPoche * uPocheOk > .5) c = 7.; } gl_FragColor = vec4(n.xy * .5 + .5, c / 8., 1.); }';

const DISPLAY_FS = `
  uniform sampler2D tND, tDepth, tReal;
  uniform vec2 uRes; uniform float uNear, uFar, uPour, uRealOnly, uExpo, uInkOver, uTime;
  uniform vec4 uRects[6]; uniform float uReveal[6]; uniform vec4 uRect0;
  uniform vec3 uPaper, uInk, uAccent;
  varying vec2 vUv;
  vec4 R;
  float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
  float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
  vec2 cl(vec2 p){ return clamp(p, R.xy + .5, R.zw - .5); }
  float dAt(vec2 p){ return texture2D(tDepth, cl(p) / uRes).r; }
  vec4 ndAt(vec2 p){ return texture2D(tND, cl(p) / uRes); }
  vec3 nAt(vec2 p){ vec2 t = ndAt(p).xy * 2. - 1.; return vec3(t, sqrt(max(0., 1. - dot(t, t)))); }
  float lin(float d){ float z = d * 2. - 1.; return 2. * uNear * uFar / (uFar + uNear - z * (uFar - uNear)); }
  bool inside(vec2 p, vec4 r){ return p.x >= r.x && p.y >= r.y && p.x < r.z && p.y < r.w; }
  vec3 aces(vec3 c){
    const mat3 I = mat3(vec3(.59719, .07600, .02840), vec3(.35458, .90834, .13383), vec3(.04823, .01566, .83777));
    const mat3 O = mat3(vec3(1.60475, -.10208, -.00327), vec3(-.53108, 1.10813, -.07276), vec3(-.07367, -.00605, 1.07602));
    c *= uExpo / .6; c = I * c; vec3 a = c * (c + .0245786) - .000090537, b = c * (.983729 * c + .4329510) + .238081; return clamp(O * (a / b), 0., 1.);
  }
  vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(c, vec3(1. / 2.4)) - .055, step(.0031308, c)); }
  vec3 realAt(vec2 uv){ return srgb(aces(texture2D(tReal, uv).rgb)); }
  vec3 paper(vec2 p){ float g = vn(p * .9) * .5 + vn(p * .21) * .5; return uPaper * (.985 + .03 * g); }
  void main(){
    vec2 p = gl_FragCoord.xy;
    bool in0 = inside(p, uRect0);
    if (uRealOnly > .5) { gl_FragColor = vec4(realAt(vUv), 1.); return; }
    int ti = -1; float rev = 1.;
    for (int i = 0; i < 6; i++) if (inside(p, uRects[i])) { ti = i; R = uRects[i]; rev = uReveal[i]; }
    if (ti < 0) { gl_FragColor = vec4(paper(p), 1.); return; }
    float dc = dAt(p); bool bg = dc >= 1.;
    vec4 nd = ndAt(p); float cls = floor(nd.z * 8. + .5);
    vec3 nc = nAt(p);
    float e = 0.;
    vec2 o = vec2(1., 0.), q = vec2(0., 1.);
    if (bg) {
      for (int i = 0; i < 4; i++) { vec2 d = i == 0 ? o : i == 1 ? -o : i == 2 ? q : -q; if (dAt(p + d) < 1.) e = max(e, .9); }
    } else {
      float lc = lin(dc);
      for (int i = 0; i < 2; i++) {
        vec2 d = i == 0 ? o : q;
        float da = dAt(p + d), db = dAt(p - d);
        if (da >= 1. || db >= 1.) { e = max(e, .9); continue; }
        float d2 = abs(lin(da) + lin(db) - 2. * lc);
        float dn = max(1. - dot(nc, nAt(p + d)), 1. - dot(nc, nAt(p - d)));
        float ca = floor(ndAt(p + d).z * 8. + .5), cb = floor(ndAt(p - d).z * 8. + .5);
        float ec = (ca != cls || cb != cls) ? .75 : 0.;
        float sc = (cls == 6. || cls == 3.) ? .55 : 1.;
        e = max(e, max(max(smoothstep(.06, .2, d2) * .9, smoothstep(.12, .32, dn) * .7) * sc, ec));
      }
    }
    vec3 base = paper(p);
    if (!bg) {
      float sh = .9 + .1 * dot(nc, normalize(vec3(-.35, .55, .75)));
      base *= sh;
      if (cls == 1.) { if (h21(floor(p / 2.)) < .045) e = max(e, .4); base *= vec3(.95, .98, .92); }
      else if (cls == 2.) { base = mix(base, vec3(.78, .89, .9), .8); if (fract(p.y / 5. + vn(p * .05) * 1.4) < .16) e = max(e, .3); }
      else if (cls == 3.) { float hh = fract((p.x * .35 - p.y) / 4.); if (hh < .22) e = max(e, .38); base *= .96; }
      else if (cls == 4.) { base = mix(base, vec3(.88, .93, .94), .5); }
      else if (cls == 5.) { if (h21(floor(p)) < .012) e = max(e, .28); }
      else if (cls == 6.) { base *= .86; if (h21(floor(p / 2.)) < .12) e = max(e, .4); }
      else if (cls == 7.) { base = mix(base, uInk, .82); }
    }
    vec3 col = mix(base, uInk, clamp(e, 0., .92));
    // revelação da prancha: o desenho sobe do chão, com tinta fresca na frente
    float ly = (p.y - R.y) / max(1., R.w - R.y);
    if (ly > rev) col = paper(p);
    else col = mix(col, uAccent, smoothstep(rev - .06, rev, ly) * e * (rev < .999 ? 1. : 0.));
    // o terreno real entra por trás do nanquim
    if (in0 && uPour > 0.) {
      vec2 c = (R.xy + R.zw) * .5; float rr = length((p - c) / (R.zw - R.xy));
      float m = rr * .9 + vn(p * .012) * .35 + vn(p * .05) * .1;
      float k = 1. - smoothstep(uPour * 1.5 - .14, uPour * 1.5, m);
      vec3 real = realAt(vUv);
      vec3 inked = mix(real, real * .55 + uInk * .25, clamp(e, 0., 1.) * uInkOver);
      col = mix(col, inked, k);
      float band = exp(-pow((uPour * 1.5 - .07 - m) / .025, 2.)) * (uPour < .99 ? 1. : 0.);
      col = mix(col, uInk, band * .55);
    }
    gl_FragColor = vec4(col, 1.);
  }`;

export function makeInk(renderer, scene, cam, opt) {
  const P = {};
  const nearest = { minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, type: THREE.UnsignedByteType };
  P.ndRT = new THREE.WebGLRenderTarget(4, 4, nearest);
  P.ndRT.depthTexture = new THREE.DepthTexture(4, 4, THREE.FloatType);
  P.realRT = new THREE.WebGLRenderTarget(4, 4, { type: THREE.HalfFloatType, samples: opt.samples });
  // o terreno real: render + oclusão ambiente (GTAO, como no 04) para a sombra de contato
  if (opt.ao) {
    P.comp = new EffectComposer(renderer, P.realRT); P.comp.renderToScreen = false;
    P.comp.addPass(new RenderPass(scene, cam));
    const ao = new GTAOPass(scene, cam, 4, 4);
    ao.updateGtaoMaterial({ radius: 1.1, distanceExponent: 1.4, thickness: 1.6, scale: 1.7, samples: 16 });
    ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16 });
    ao.blendIntensity = 1.0;
    ao.normalMaterial.side = THREE.DoubleSide; // peças de face dupla do GLB (poltronas, palha) entram no G-buffer
    const r0 = ao.render.bind(ao); // vidro, céu e chão distante ficam fora da oclusão
    ao.render = (...a) => { const hid = []; scene.traverse((m) => { if ((m.userData.kind === 'glass' || m.userData.sky || m.userData.palm || m.userData.noAO) && m.visible) { m.visible = false; hid.push(m); } }); r0(...a); hid.forEach((m) => (m.visible = true)); };
    P.comp.addPass(ao); P.ao = ao;
  }
  P.mat = new THREE.ShaderMaterial({
    uniforms: {
      tND: { value: P.ndRT.texture }, tDepth: { value: P.ndRT.depthTexture }, tReal: { value: P.realRT.texture },
      uRes: { value: new THREE.Vector2() }, uNear: { value: 1 }, uFar: { value: 2 }, uPour: { value: 0 }, uRealOnly: { value: 0 }, uExpo: { value: 1 }, uInkOver: { value: 0 }, uTime: { value: 0 },
      uRects: { value: Array.from({ length: 6 }, () => new THREE.Vector4(-1, -1, -1, -1)) }, uReveal: { value: [1, 1, 1, 1, 1, 1] }, uRect0: { value: new THREE.Vector4(-1, -1, -1, -1) },
      uPaper: { value: new THREE.Vector3(0.953, 0.937, 0.894) }, uInk: { value: new THREE.Vector3(0.11, 0.105, 0.095) }, uAccent: { value: new THREE.Vector3(0.71, 0.33, 0.17) },
    },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }',
    fragmentShader: DISPLAY_FS, depthTest: false, depthWrite: false, toneMapped: false,
  });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), P.mat); quad.frustumCulled = false;
  const qScene = new THREE.Scene(); qScene.add(quad);
  const qCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  // material de normal+classe por grupo
  const ndCache = new Map(), CLIP = { value: 1e4 }, POCHE = { value: 0 };
  const ndMat = (cls, inst, pok) => {
    const key = cls + (inst ? 'i' : '') + (pok ? 'p' : '');
    if (!ndCache.has(key)) ndCache.set(key, new THREE.ShaderMaterial({ uniforms: { uClass: { value: cls }, uClipY: CLIP, uPoche: POCHE, uPocheOk: { value: pok ? 1 : 0 } }, vertexShader: inst ? ND_VS_INST : ND_VS, fragmentShader: ND_FS, side: THREE.DoubleSide }));
    return ndCache.get(key);
  };
  const inkList = [], noInk = [];
  scene.traverse((o) => {
    if (!o.isMesh) return;
    const d = o.userData;
    if (d.noink) noInk.push(o);
    if (d.stage === undefined || d.blades || d.noink) return;
    inkList.push({ o, nd: ndMat(d.ink || 0, o.isInstancedMesh, ['plaster', 'wood', 'cement', 'stone'].includes(d.kind)), main: o.material });
  });
  P.setSize = (W, H, dpr) => {
    P.W = W; P.H = H; P.dpr = dpr;
    const w = Math.round(W * dpr), h = Math.round(H * dpr);
    P.ndRT.setSize(w, h);
    if (P.comp) { P.comp.setPixelRatio(1); P.comp.setSize(w, h); } else P.realRT.setSize(w, h);
    P.mat.uniforms.uRes.value.set(w, h);
  };
  const dev = (r, out) => out.set(r.x * P.dpr, (P.H - r.y - r.h) * P.dpr, (r.x + r.w) * P.dpr, (P.H - r.y) * P.dpr);
  const onScreen = (r) => r.x < P.W && r.y < P.H && r.x + r.w > 0 && r.y + r.h > 0;

  // o desenho: cada prancha é a mesma câmera mirada no seu retângulo, na sua etapa
  P.draw = (tiles, hide) => {
    const vis = new Map(); scene.traverse((o) => vis.set(o, o.visible));
    hide.concat(noInk).forEach((o) => (o.visible = false));
    const keep = renderer.autoClear; renderer.autoClear = false;
    const bgKeep = scene.background, fogKeep = scene.fog; scene.background = null; scene.fog = null;
    P.ndRT.scissorTest = false; renderer.setRenderTarget(P.ndRT); renderer.setClearColor(0x000000, 0); renderer.clear();
    const R = P.mat.uniforms.uRects.value;
    inkList.forEach((e) => (e.o.material = e.nd));
    const shadowKeep = renderer.shadowMap.enabled; renderer.shadowMap.enabled = false;
    tiles.forEach((t, i) => {
      if (!t || t.hidden || !onScreen(t.rect)) { R[i].set(-1, -1, -1, -1); return; }
      dev(t.rect, R[i]);
      P.mat.uniforms.uReveal.value[i] = t.reveal ?? 1;
      aim(cam, t.cam, t.rect, P.W, P.H);
      CLIP.value = t.clipY ?? 1e4; POCHE.value = t.clipY !== undefined && t.clipY < 50 ? 1 : 0;
      inkList.forEach((e) => { const s = e.o.userData.stage; e.o.visible = s <= t.stage && !(s === 1 && t.stage > 1); });
      const x0 = Math.max(0, Math.floor(R[i].x)), y0 = Math.max(0, Math.floor(R[i].y)), x1 = Math.min(P.ndRT.width, Math.ceil(R[i].z)), y1 = Math.min(P.ndRT.height, Math.ceil(R[i].w));
      P.ndRT.scissor.set(x0, y0, x1 - x0, y1 - y0); P.ndRT.scissorTest = true;
      renderer.setRenderTarget(P.ndRT); renderer.render(scene, cam);
    });
    renderer.shadowMap.enabled = shadowKeep;
    inkList.forEach((e) => (e.o.material = e.main));
    scene.traverse((o) => { if (vis.has(o)) o.visible = vis.get(o); });
    scene.background = bgKeep; scene.fog = fogKeep;
    renderer.setRenderTarget(null); renderer.autoClear = keep;
    P.mat.uniforms.uNear.value = cam.near; P.mat.uniforms.uFar.value = cam.far;
  };
  P.real = () => {
    renderer.setClearColor(0x000000, 1);
    if (P.comp) { P.comp.render(); P.mat.uniforms.tReal.value = P.comp.readBuffer.texture; }
    else { renderer.setRenderTarget(P.realRT); renderer.clear(); renderer.render(scene, cam); }
    renderer.setRenderTarget(null);
  };
  P.show = (o) => {
    const u = P.mat.uniforms;
    dev(o.rect0, u.uRect0.value);
    u.uPour.value = o.pour; u.uRealOnly.value = o.realOnly ? 1 : 0; u.uInkOver.value = o.inkOver || 0;
    if (o.realOnly) u.uRects.value.forEach((r) => r.set(-1, -1, -1, -1));
    renderer.setRenderTarget(null); renderer.render(qScene, qCam);
  };
  return P;
}
