# Sala do apto 10: sofá de linho com base de madeira escura, mesa redonda de pé central, cadeira de varas com assento
# de palha, rack ripado, TV de 50" e quatro quadros (pinturas geradas aqui, sem imagem de fora).
# Gera assets/models/sala/*.glb. Convenções em blender/lib.py (origem no piso e na face de trás; frente para -Y).
# Exceção: os quadros têm a origem no centro da moldura, atrás (no site, y = altura do centro).
#
#   blender --background --python blender/sala.py [-- --preview previa.png]
import bpy, bmesh, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from mathutils import Vector

M = None


def fresh():
    global M
    reset(); lib._mats.clear(); M = lib.M()


def lathe(name, prof, m, seg=32):
    """Sólido de revolução em torno de Z a partir de [(raio, z), ...] de baixo para cima."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((a, b)) for a, b in zip(vs, vs[1:])]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=seg, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return finish(name, bm, m, True)


# ---------------------------------------------------------------- sofá 1,80 × 0,86, assento a 0,47
SL, SD = 1.80, 0.86


def sofa():
    h = SL / 2
    box('sofa_base', -h, h, -SD, -0.03, 0.12, 0.30, M['escura'], 0.008)
    for x in (-h + 0.07, h - 0.07):
        for y in (-SD + 0.07, -0.09):
            cyl('sofa_pe', 0.024, 0, 0.125, x, y, M['escura'], 16, r2=0.03)
    box('sofa_encosto', -h, h, -0.24, -0.03, 0.30, 0.74, M['linho'], 0.03, 3)
    for x0, x1 in ((-h, -h + 0.15), (h - 0.15, h)):
        box('sofa_braco', x0, x1, -SD + 0.01, -0.05, 0.30, 0.62, M['linho'], 0.035, 3)
    for x0, x1 in ((-h + 0.155, -0.004), (0.004, h - 0.155)):
        cushion('sofa_assento', x0, x1, -SD + 0.02, -0.235, 0.30, 0.47, M['linho'], 0.045)
        c = cushion('sofa_encosto_alm', x0 + 0.01, x1 - 0.01, -0.40, -0.23, 0.46, 0.86, M['linho'], 0.06)
        turn(c, rx=-9, pivot=(0, -0.40, 0.46))   # inclina para trás, apoiado na frente de baixo
    for x, m, r in ((-h + 0.33, M['azul'], 18), (h - 0.33, M['terracota'], -14)):
        p = cushion('sofa_almofada', x - 0.21, x + 0.21, -0.48, -0.34, 0.47, 0.88, m, 0.09)
        turn(p, rx=-14, rz=r)
    # manta dobrada no braço direito
    box('sofa_manta', h - 0.17, h + 0.005, -0.62, -0.28, 0.62, 0.64, M['branco'], 0.008)


# ---------------------------------------------------------------- mesa redonda Ø 0,90, pé central com cruzeta
def mesa():
    lathe('mesa_tampo', [(0, 0.72), (0.43, 0.72), (0.45, 0.728), (0.45, 0.746), (0.44, 0.75), (0, 0.75)], M['madeira'], 64)
    lathe('mesa_coluna', [(0, 0.03), (0.055, 0.03), (0.045, 0.2), (0.04, 0.6), (0.05, 0.69), (0, 0.69)], M['escura'], 24)
    for a in (0, 90):
        turn(box('mesa_pe', -0.33, 0.33, -0.03, 0.03, 0, 0.045, M['escura'], 0.006), rz=a, pivot=(0, 0, 0))
        turn(box('mesa_apoio', -0.24, 0.24, -0.025, 0.025, 0.685, 0.72, M['escura'], 0.004), rz=a, pivot=(0, 0, 0))


# ---------------------------------------------------------------- cadeira: madeira clara, encosto de varas roliças, assento de palha
def cadeira():
    W, Dp, ZS = 0.44, 0.42, 0.45
    rake = lambda z: 0.18 + 0.035 * z / 0.86
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.025)
        tube('cad_pe_frente', [(x, -0.18, 0), (x, -0.18, ZS)], 0.017, M['madeira'], 3)
        tube('cad_pe_tras', [(x, 0.18, 0), (x, rake(ZS), ZS), (x, rake(0.86), 0.86)], 0.017, M['madeira'], 3)
        tube('cad_travessa_lado', [(x, -0.18, 0.16), (x, 0.18, 0.16)], 0.009, M['madeira'], 2)
    tube('cad_travessa_frente', [(-W / 2 + 0.025, -0.18, 0.2), (W / 2 - 0.025, -0.18, 0.2)], 0.009, M['madeira'], 2)
    # aro do assento e palha trançada
    box('cad_aro_f', -W / 2, W / 2, -Dp / 2 - 0.01, -Dp / 2 + 0.03, ZS - 0.045, ZS, M['madeira'], 0.004)
    box('cad_aro_t', -W / 2, W / 2, Dp / 2 - 0.04, Dp / 2, ZS - 0.045, ZS, M['madeira'], 0.004)
    for sx in (-1, 1):
        box('cad_aro_l', sx * W / 2 - (0.03 if sx > 0 else 0), sx * W / 2 + (0.03 if sx < 0 else 0), -Dp / 2, Dp / 2, ZS - 0.045, ZS, M['madeira'], 0.004)
    cushion('cad_palha', -W / 2 + 0.03, W / 2 - 0.03, -Dp / 2 + 0.03, Dp / 2 - 0.04, ZS - 0.03, ZS + 0.008, M['palha'], 0.01)
    # encosto: travessa curva no alto e cinco varas
    top = [(x, rake(0.82) + 0.025 * (1 - (x / 0.2) ** 2), 0.82) for x in np.linspace(-0.2, 0.2, 9)]
    tube('cad_encosto', top, 0.016, M['madeira'], 3)
    tube('cad_travessa_enc', [(x, rake(0.52) + 0.012 * (1 - (x / 0.2) ** 2), 0.52) for x in np.linspace(-0.2, 0.2, 7)], 0.01, M['madeira'], 2)
    for x in np.linspace(-0.12, 0.12, 5):
        tube('cad_vara', [(x, rake(0.52) + 0.012 * (1 - (x / 0.2) ** 2), 0.52), (x, rake(0.82) + 0.025 * (1 - (x / 0.2) ** 2), 0.82)], 0.0075, M['madeira'], 2)


# ---------------------------------------------------------------- rack ripado 1,40 × 0,40 × 0,53, com vaso e livros
RL, RD = 1.40, 0.40


def rack():
    h = RL / 2
    for x in (-h + 0.06, h - 0.06):
        for y in (-RD + 0.06, -0.06):
            cyl('rack_pe', 0.02, 0, 0.14, x, y, M['escura'], 12, r2=0.024)
    box('rack_corpo', -h, h, -RD + 0.015, 0, 0.14, 0.50, M['madeira'])
    box('rack_tampo', -h - 0.01, h + 0.01, -RD - 0.01, 0, 0.50, 0.53, M['madeira'], 0.004)
    n = 42
    sp = (RL - 0.02) / n
    for i in range(n):
        x = -h + 0.01 + sp * (i + 0.5)
        box('rack_ripa', x - sp * 0.36, x + sp * 0.36, -RD - 0.002, -RD + 0.015, 0.15, 0.49, M['madeira'], 0.002, 1, veio='v')
    box('rack_fundo_ripas', -h + 0.005, h - 0.005, -RD + 0.012, -RD + 0.015, 0.15, 0.49, M['rodape'])
    # vaso de cerâmica e dois livros
    v = lathe('rack_vaso', [(0, 0), (0.06, 0), (0.085, 0.07), (0.08, 0.15), (0.04, 0.22), (0.035, 0.26), (0.042, 0.27), (0.03, 0.27), (0.03, 0.23), (0, 0.23)], M['ceramica'], 32)
    v.location = (-0.45, -0.2, 0.53)
    for k, (t, m) in enumerate(((0.035, M['azul']), (0.028, M['branco']))):
        z0 = 0.53 + (0.035 if k else 0)
        turn(box('rack_livro', 0.24, 0.52, -0.31, -0.09, z0, z0 + t, m, 0.003), rz=8 - 14 * k)


# ---------------------------------------------------------------- TV 50" na parede, centro a 1,25 m do piso
def tv():
    W, H, ZC = 1.13, 0.655, 1.25
    box('tv_suporte', -0.15, 0.15, -0.035, 0, ZC - 0.12, ZC + 0.12, M['plastico'])
    box('tv_corpo', -W / 2, W / 2, -0.065, -0.035, ZC - H / 2, ZC + H / 2, M['plastico'], 0.004)
    box('tv_tela', -W / 2 + 0.008, W / 2 - 0.008, -0.0665, -0.0645, ZC - H / 2 + 0.012, ZC + H / 2 - 0.008, M['tela'])


# ---------------------------------------------------------------- quadros: pinturas feitas aqui com numpy
def paint(name, w, h, fn, px=420):
    W, H = int(px * w / max(w, h)) * 2, int(px * h / max(w, h)) * 2
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W, 1 - y / H                       # v para cima
    img = np.ones((H, W, 3), np.float32)
    fn(img, u, v)
    rgba = np.concatenate([img ** 2.2, np.ones((H, W, 1), np.float32)], 2)[::-1]  # Blender guarda de baixo para cima
    im = bpy.data.images.new(name, W, H)
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im


def hexc(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def grain(img, u, v, k=0.035, seed=1):
    rng = np.random.default_rng(seed)
    img *= 1 - k + k * 2 * rng.random(img.shape[:2], dtype=np.float32)[..., None]


def art_sol(img, u, v):
    img[:] = hexc('#efe5d2')
    for v0, v1, c in ((0.0, 0.18, '#d6bd94'), (0.18, 0.30, '#5f8296'), (0.30, 0.40, '#8fb1bf'), (0.40, 0.44, '#b9d0d6')):
        m = (v >= v0) & (v < v1 + 0.004 * np.sin(u * 40 + v0 * 9)); img[m] = hexc(c)
    d = np.hypot((u - 0.5) * 0.75, v - 0.62)
    img[d < 0.19] = hexc('#c46d45')
    img[(d < 0.19) & (v < 0.44)] = hexc('#efe5d2')  # o sol se põe atrás do mar
    for k in range(3):
        m = np.abs(v - (0.36 - 0.05 * k)) < 0.004
        img[m & (np.abs(u - 0.5) < 0.16 - 0.04 * k)] = hexc('#e9a77f')
    grain(img, u, v)


def art_folhas(img, u, v):
    img[:] = hexc('#ece3cf')
    for (cx, cy, a, L, c) in ((0.42, 0.18, 62, 0.75, '#4c6b4a'), (0.58, 0.20, 105, 0.62, '#6f8f61'), (0.35, 0.22, 128, 0.5, '#3f5a40')):
        r = math.radians(a)
        du, dv = (u - cx) * 0.75, v - cy
        s = du * math.cos(r) + dv * math.sin(r)        # ao longo do ramo
        t = -du * math.sin(r) + dv * math.cos(r)       # para o lado
        inside = (s > 0) & (s < L)
        f = np.sin(np.clip(s / L, 0, 1) * math.pi) * 0.11
        leaf = inside & (np.abs(t) < f) & (np.sin(s * 140) > -0.75 + 0.0 * t)  # folíolos: cortes ao longo do ramo
        img[leaf] = hexc(c)
        img[inside & (np.abs(t) < 0.004)] = hexc('#2f3f2e')
    grain(img, u, v)


def art_mare(img, u, v):
    img[:] = hexc('#f0e8d8')
    for k in range(9):
        y0 = 0.18 + k * 0.075 + 0.02 * np.sin(u * 6.28 * 1.5 + k)
        m = np.abs(v - y0) < 0.006 + 0.004 * (k % 3 == 0)
        img[m] = hexc(['#2f4f63', '#5f8296', '#9bb6c2'][k % 3])
    d = np.hypot((u - 0.78) * 1.5, v - 0.8)
    img[d < 0.07] = hexc('#c46d45')
    grain(img, u, v)


def art_blocos(img, u, v):
    img[:] = hexc('#eee4d0')
    for (u0, v0, u1, v1, c) in ((0.12, 0.52, 0.62, 0.88, '#c98b62'), (0.38, 0.14, 0.88, 0.46, '#7f93a3'),
                                 (0.12, 0.14, 0.32, 0.46, '#d8c39d'), (0.68, 0.52, 0.88, 0.88, '#3f5a40')):
        img[(u > u0) & (u < u1) & (v > v0) & (v < v1)] = hexc(c)
    d = np.hypot((u - 0.37) * 0.75, v - 0.70)
    img[(d < 0.09)] = hexc('#efe5d2')
    grain(img, u, v)


def quadro(w, h, fn, nome):
    """Moldura de madeira escura 2 cm, passe-partout branco, pintura; origem atrás no centro."""
    fr, pp, dp = 0.022, 0.05, 0.028
    box('q_moldura_t', -w / 2, w / 2, -dp, 0, h / 2 - fr, h / 2, M['escura'], 0.002)
    box('q_moldura_b', -w / 2, w / 2, -dp, 0, -h / 2, -h / 2 + fr, M['escura'], 0.002)
    box('q_moldura_l', -w / 2, -w / 2 + fr, -dp, 0, -h / 2 + fr, h / 2 - fr, M['escura'], 0.002)
    box('q_moldura_r', w / 2 - fr, w / 2, -dp, 0, -h / 2 + fr, h / 2 - fr, M['escura'], 0.002)
    box('q_passe', -w / 2 + fr, w / 2 - fr, -dp + 0.008, -0.004, -h / 2 + fr, h / 2 - fr, M['branco'])
    aw, ah = w - 2 * (fr + pp), h - 2 * (fr + pp)
    im = paint(nome, aw, ah, fn)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new((x, -dp + 0.0075, z)) for x, z in ((-aw / 2, -ah / 2), (aw / 2, -ah / 2), (aw / 2, ah / 2), (-aw / 2, ah / 2))]
    f = bm.faces.new(vs)
    for l, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[uv].uv = c
    me = bpy.data.meshes.new('q_pintura'); bm.to_mesh(me); bm.free()
    if me.polygons[0].normal.y > 0:
        me.flip_normals()
    link(bpy.data.objects.new('q_pintura', me), mat('qd_' + nome, '#ffffff', 0.85, image=im))


QUADROS = {'sol': (0.45, 0.62, art_sol), 'folhas': (0.45, 0.62, art_folhas), 'mare': (0.90, 0.60, art_mare), 'blocos': (0.45, 0.62, art_blocos)}

PIECES = {'sofa': sofa, 'mesa': mesa, 'cadeira': cadeira, 'rack': rack, 'tv': tv}
for n, fn in PIECES.items():
    fresh(); fn(); export(f'sala/{n}.glb')
for n, (w, h, fn) in QUADROS.items():
    fresh(); quadro(w, h, fn, n); export(f'sala/quadro_{n}.glb', uv=True)

# ---------------------------------------------------------------- prévia: sofá e quadros na parede, rack e TV ao lado, mesa e cadeiras na frente
a = args()
if '--preview' in a:
    fresh()

    def put(fn, x=0, y=0, z=0, rz=0, *extra):
        n0 = len(col().objects)
        fn(*extra)
        for o in list(col().objects)[n0:]:
            turn(o, rz=rz, pivot=(0, 0, 0))
            o.location += Vector((x, y, z))
    put(sofa, -0.9)
    put(quadro, -1.2, 0, 1.45, 0, 0.45, 0.62, art_sol, 'sol_p')
    put(quadro, -0.6, 0, 1.45, 0, 0.45, 0.62, art_folhas, 'folhas_p')
    put(rack, 1.15)
    put(tv, 1.15)
    put(quadro, 2.4, 0, 1.5, 0, 0.45, 0.62, art_blocos, 'blocos_p')
    put(quadro, 0.15, 0, 1.95, 0, 0.9, 0.6, art_mare, 'mare_p')
    put(mesa, 0.3, -1.9)
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        put(cadeira, 0.3 + 0.55 * math.cos(ang), -1.9 + 0.55 * math.sin(ang), 0, math.degrees(ang) - 90)   # frente (-Y) virada para a mesa
    preview(a[a.index('--preview') + 1], (0.4, -4.6, 2.0), (0.3, -0.6, 0.8), 26)
