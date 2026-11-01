# Porta de madeira escura do apto 10: folha lisa com dois frisos, batente que cobre a espessura da parede (12 cm),
# guarnições dos dois lados, três dobradiças e maçaneta de alavanca preta dos dois lados. Fechada.
# Gera assets/models/porta/porta_80.glb (quartos e banho) e porta_90.glb (entrada).
# Origem: no piso, no meio do vão e no meio da parede; X ao longo da parede, a maçaneta fica do lado +X.
#
#   blender --background --python blender/porta.py [-- --preview previa.png]
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from mathutils import Matrix

M = None
H, WALL = 2.10, 0.12


def fresh():
    global M
    reset(); lib._mats.clear(); M = lib.M()
    M['folha'] = mat('pt_folha', '#7a5236', 0.5)
    M['batente'] = mat('md_escura', '#5a3a24', 0.55)
    M['ferragem'] = mat('cz_puxador', '#1b1b1b', 0.35, 0.6)


def macaneta(x, side):
    """Roseta redonda + alavanca, na face y = side * (folha / 2)."""
    y = side * 0.0175
    cyl_y('roseta', 0.026, y, y + side * 0.008, x, 1.0, M['ferragem'])
    tube('alavanca', [(x, y + side * 0.006, 1.0), (x, y + side * 0.05, 1.0), (x - 0.12, y + side * 0.055, 1.0)], 0.0085, M['ferragem'], 3)
    cyl_y('espelho_chave', 0.012, y, y + side * 0.004, x, 0.86, M['ferragem'])


def cyl_y(name, r, y0, y1, x, z, m, seg=24):
    """Cilindro deitado no eixo Y (rosetas)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=abs(y1 - y0))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    bmesh.ops.translate(bm, vec=(x, (y0 + y1) / 2, z), verts=bm.verts)
    return bevel(finish(name, bm, m), 0.002, 1, 50)


def porta(W):
    """W = vão na parede. Batente por dentro do vão (sem coincidir com o reboco), guarnições por cima da parede."""
    j, g, gt = 0.035, 0.07, 0.015          # batente (espessura), guarnição (largura, espessura)
    t = 0.035                              # folha
    Wc, Hc = W - 2 * j, H - j              # luz livre
    yb = WALL / 2 + 0.003                  # batente um pouco além do reboco, escondido pela guarnição
    box('batente_e', -W / 2 + 0.001, -Wc / 2, -yb, yb, 0, H - 0.001, M['batente'], 0.002, veio='v')
    box('batente_d', Wc / 2, W / 2 - 0.001, -yb, yb, 0, H - 0.001, M['batente'], 0.002, veio='v')
    box('batente_t', -W / 2 + 0.001, W / 2 - 0.001, -yb, yb, Hc, H - 0.001, M['batente'], 0.002)
    # guarnições dos dois lados
    for sy in (-1, 1):
        y0, y1 = sorted((sy * (WALL / 2 + 0.001), sy * (WALL / 2 + gt)))
        box('guarnicao_e', -W / 2 - g, -Wc / 2 - 0.004, y0, y1, 0, H + g, M['batente'], 0.004, veio='v')
        box('guarnicao_d', Wc / 2 + 0.004, W / 2 + g, y0, y1, 0, H + g, M['batente'], 0.004, veio='v')
        box('guarnicao_t', -W / 2 - g, W / 2 + g, y0, y1, Hc + 0.004, H + g, M['batente'], 0.004)
    # batedor (onde a folha encosta)
    box('batedor_e', -Wc / 2, -Wc / 2 + 0.012, t / 2, t / 2 + 0.012, 0, Hc, M['batente'], veio='v')
    box('batedor_d', Wc / 2 - 0.012, Wc / 2, t / 2, t / 2 + 0.012, 0, Hc, M['batente'], veio='v')
    box('batedor_t', -Wc / 2, Wc / 2, t / 2, t / 2 + 0.012, Hc - 0.012, Hc, M['batente'])
    # folha com folga de 3 mm e 8 mm no piso
    box('folha', -Wc / 2 + 0.003, Wc / 2 - 0.003, -t / 2, t / 2, 0.008, Hc - 0.003, M['folha'], 0.002, veio='v')
    # dois frisos verticais rasos de cada lado (sombra fina)
    for sy in (-1, 1):
        for fx in (-Wc / 6, Wc / 6):
            y0, y1 = sorted((sy * t / 2, sy * (t / 2 + 0.0008)))
            box('friso', fx - 0.003, fx + 0.003, y0, y1, 0.09, Hc - 0.09, M['rodape'])
    # dobradiças do lado -X
    for z in (0.2, 1.0, 1.8):
        cyl('dobradica', 0.008, z - 0.05, z + 0.05, -Wc / 2, -t / 2 - 0.004, M['ferragem'], 12)
    # maçanetas dos dois lados, junto ao lado +X
    for side in (-1, 1):
        macaneta(Wc / 2 - 0.065, side)


for W in (0.80, 0.90):
    fresh(); porta(W); export(f'porta/porta_{int(W * 100)}.glb')

a = args()
if '--preview' in a:
    fresh(); porta(0.80)
    box('_parede_e', -1.5, -0.4, -WALL / 2, WALL / 2, 0, 2.7, mat('_p', '#f4f1ea', 0.9))
    box('_parede_d', 0.4, 1.5, -WALL / 2, WALL / 2, 0, 2.7, mat('_p', '#f4f1ea', 0.9))
    box('_parede_t', -0.4, 0.4, -WALL / 2, WALL / 2, H, 2.7, mat('_p', '#f4f1ea', 0.9))
    preview(a[a.index('--preview') + 1], (1.0, -2.6, 1.3), (0, 0, 1.0), 32, wall=False)
