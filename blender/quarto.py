# Quarto 1 do apto 10: cama de casal 1,60 × 2,00 com cabeceira de palhinha trançada em moldura de madeira escura,
# criados-mudos suspensos de carvalho com gaveta e abajur de cerâmica, tapete de sisal.
# Gera assets/models/quarto/{cama,criado,tapete}.glb. Convenções em blender/lib.py (origem no piso, na face da parede).
#
#   blender --background --python blender/quarto.py [-- --preview previa.png]
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


def palhinha():
    """Trama octogonal de palhinha (cana-da-índia), um ladrilho que repete."""
    n = 128
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    img = np.empty((n, n, 3), np.float32); img[:] = np.array([0.20, 0.15, 0.10])      # fundo: o vão escuro
    tan, tan2 = np.array([0.80, 0.66, 0.44]), np.array([0.72, 0.57, 0.36])
    band = lambda t, w: (np.abs(((t % 0.5) - 0.25)) < w)                               # dois fios por ladrilho
    for t, c, w in ((x, tan, 0.045), (y, tan2, 0.045), ((x + y) % 1, tan, 0.03), ((x - y) % 1, tan2, 0.03)):
        m = band(t, w)
        shade = 0.85 + 0.15 * np.cos((np.abs(((t % 0.5) - 0.25)) / w) * math.pi / 2)
        img[m] = (c * shade[..., None])[m]
    rgba = np.concatenate([img ** 2.2, np.ones((n, n, 1), np.float32)], 2)[::-1]
    im = bpy.data.images.new('palhinha', n, n)
    im.pixels.foreach_set(rgba.ravel()); im.pack()
    return im


def plane_uv(name, x0, x1, z0, z1, y, m, tile):
    """Painel vertical (frente para -Y) com UV repetida a cada `tile` metros."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new((x, y, z)) for x, z in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
    f = bm.faces.new(vs)
    for l, (x, z) in zip(f.loops, ((x0, z0), (x1, z0), (x1, z1), (x0, z1))):
        l[uv].uv = ((x - x0) / tile, (z - z0) / tile)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if me.polygons[0].normal.y > 0:
        me.flip_normals()
    return link(bpy.data.objects.new(name, me), m)


# ---------------------------------------------------------------- cama: 1,60 × 2,00, colchão a 0,55
BW, BL = 1.60, 2.00


def cama():
    # cabeceira: moldura de madeira escura com palhinha, encostada na parede
    HW, HZ0, HZ1, fr = 1.80, 0.30, 1.30, 0.05
    box('cab_fundo', -HW / 2, HW / 2, -0.03, 0, HZ0, HZ1, M['escura'], 0.004)
    box('cab_topo', -HW / 2 - 0.01, HW / 2 + 0.01, -0.06, 0, HZ1 - fr, HZ1 + 0.01, M['escura'], 0.006)
    box('cab_base', -HW / 2, HW / 2, -0.06, 0, HZ0, HZ0 + fr, M['escura'], 0.006)
    for sx in (-1, 1):
        box('cab_lado', sx * HW / 2 - fr * (sx > 0), sx * HW / 2 + fr * (sx < 0), -0.06, 0, HZ0 + fr, HZ1 - fr, M['escura'], 0.006, veio='v')
    plane_uv('cab_palhinha', -HW / 2 + fr, HW / 2 - fr, HZ0 + fr, HZ1 - fr, -0.035, mat('qd_palhinha', '#ffffff', 0.8, image=palhinha()), 0.07)
    # base de madeira escura com rodapé recuado (parece flutuar)
    y0, y1 = -0.06 - BL - 0.04, -0.06
    box('cama_rodape', -BW / 2 + 0.08, BW / 2 - 0.08, y0 + 0.08, y1, 0, 0.08, M['rodape'])
    box('cama_base', -BW / 2 - 0.04, BW / 2 + 0.04, y0, y1, 0.08, 0.32, M['escura'], 0.012, 2)
    # colchão, lençol branco, edredom de linho e caimento
    cushion('colchao', -BW / 2 + 0.01, BW / 2 - 0.01, y0 + 0.02, y1 - 0.01, 0.32, 0.55, M['branco'], 0.04)
    ed0 = y0 + 0.05           # pé da cama
    ed1 = y1 - 0.62           # edredom dobrado para baixo antes dos travesseiros
    cushion('edredom', -BW / 2 - 0.05, BW / 2 + 0.05, ed0 - 0.05, ed1, 0.40, 0.59, M['linho'], 0.05)   # cai pelos lados e pelo pé
    cushion('edredom_dobra', -BW / 2 - 0.05, BW / 2 + 0.05, ed1 - 0.22, ed1 + 0.02, 0.585, 0.615, M['linho'], 0.02)
    # manta azul atravessada no pé
    cushion('manta', -BW / 2 - 0.07, BW / 2 + 0.07, ed0 + 0.12, ed0 + 0.52, 0.585, 0.625, M['azul'], 0.02)
    # travesseiros brancos de pé contra a cabeceira e duas almofadas
    for sx in (-1, 1):
        p = cushion('travesseiro', sx * 0.38 - 0.33, sx * 0.38 + 0.33, y1 - 0.22, y1 - 0.06, 0.55, 0.95, M['branco'], 0.08)
        turn(p, rx=-18)
    for x, m in ((-0.2, M['terracota']), (0.22, M['azul'])):
        p = cushion('almofada', x - 0.2, x + 0.2, y1 - 0.36, y1 - 0.24, 0.57, 0.92, m, 0.09)
        turn(p, rx=-14, rz=8 if x < 0 else -6)


# ---------------------------------------------------------------- criado-mudo suspenso (42 × 38) com gaveta e abajur
def criado():
    W, D, Z0, Z1 = 0.42, 0.38, 0.32, 0.56
    box('criado_corpo', -W / 2, W / 2, -D, 0, Z0, Z1, M['madeira'], 0.004)
    box('criado_gaveta', -W / 2 + 0.01, W / 2 - 0.01, -D - 0.006, -D, Z0 + 0.012, Z1 - 0.07, M['madeira'], 0.002, veio='v')
    box('criado_vao', -W / 2 + 0.01, W / 2 - 0.01, -D + 0.01, -0.01, Z1 - 0.065, Z1 - 0.015, M['rodape'])  # nicho aberto em cima
    tube('criado_puxador', [(-0.06, -D - 0.006, Z0 + 0.03), (0.06, -D - 0.006, Z0 + 0.03)], 0.004, M['puxador'])
    b = lathe('abajur_base', [(0, 0), (0.05, 0), (0.075, 0.06), (0.07, 0.14), (0.03, 0.2), (0.012, 0.22), (0, 0.22)], M['ceramica'])
    c = lathe('abajur_cupula', [(0.13, 0.0), (0.095, 0.17)], mat('lp_cupula', '#f3e9d6', 0.8), 40)
    t = tube('abajur_haste', [(0, 0, 0.22), (0, 0, 0.32)], 0.006, M['puxador'])
    for o, dz in ((b, 0), (c, 0.2), (t, 0)):
        o.location = (0.05, -D / 2, Z1 + dz)


def lathe(name, prof, m, seg=32):
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((a, b)) for a, b in zip(vs, vs[1:])]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=seg, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return finish(name, bm, m, True)


# ---------------------------------------------------------------- tapete de sisal 1,40 × 2,00 com borda de linho
def tapete():
    box('tapete', -0.7, 0.7, -1.0, 1.0, 0, 0.012, mat('tc_sisal', '#b9a37c', 1.0), 0.004)
    for sx in (-1, 1):
        box('tapete_borda', sx * 0.7 - 0.03 * (sx > 0), sx * 0.7 + 0.03 * (sx < 0), -1.0, 1.0, 0, 0.013, M['linho'])
    for sy in (-1, 1):
        box('tapete_borda', -0.7, 0.7, sy * 1.0 - 0.03 * (sy > 0), sy * 1.0 + 0.03 * (sy < 0), 0, 0.013, M['linho'])


for n, fn, uv in (('cama', cama, True), ('criado', criado, False), ('tapete', tapete, False)):
    fresh(); fn(); export(f'quarto/{n}.glb', uv=uv)

a = args()
if '--preview' in a:
    fresh()
    cama()
    for x in (-1.14, 1.14):
        n0 = len(col().objects); criado()
        for o in list(col().objects)[n0:]:
            o.location.x += x
    n0 = len(col().objects); tapete()
    for o in list(col().objects)[n0:]:
        o.rotation_euler.z = math.radians(90); o.location += Vector((0, -2.45, 0))
    preview(a[a.index('--preview') + 1], (1.9, -3.9, 1.7), (0, -1.0, 0.5), 26)
