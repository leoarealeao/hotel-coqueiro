# Bancada da cozinha do apto 10: gabinete de carvalho (2 portas sob a pia + 3 gavetas sob o cooktop),
# tampo de granito com cuba inox embutida, torneira gourmet e cooktop de vidro com 4 bocas.
# Também o armário aéreo (3 portas) e a geladeira inox duplex. Gera, em assets/models/cozinha/:
# cozinha.glb (bancada), aereo.glb e geladeira.glb — sem texturas: madeira e inox ganham os shaders do site (js/props.js).
#
#   blender --background --python blender/cozinha.py [-- --preview previa.png]
#
# Eixos do Blender: X ao longo da bancada, -Y = frente, Z para cima; origem no piso, no meio da face que encosta na parede.
# No site a peça gira -90°: X vira +z do mundo, a frente olha para -x (parede x = 42,69, bancada z 4,8–6,5).
import bpy, bmesh, math, os, sys
from mathutils import Vector

L, D = 1.70, 0.57          # comprimento e profundidade do gabinete
PL = 0.10                  # rodapé
TOP0, TOP1 = 0.84, 0.87    # tampo de granito (3 cm)
OVF = 0.04                 # avanço do tampo sobre as portas
FT = 0.02                  # espessura das portas e frentes de gaveta
GAP = 0.003                # fresta entre frentes
XS = 0.85                  # divisa: pia (0–0,85) | cooktop (0,85–1,70)
SINK = (0.43, -0.30)       # centro da cuba
HOB = (1.275, -0.31)       # centro do cooktop

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *



def bancada():
    # ---------------------------------------------------------------- gabinete
    box('rodape', 0.005, L - 0.005, -D + 0.06, -0.02, 0, PL, M['rodape'])
    caixa = box('caixa', 0, L, -D, 0, PL, TOP0, M['madeira'])
    bm = bmesh.new(); bm.from_mesh(caixa.data)  # sem a face de cima: a cuba desce para dentro do gabinete
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY')
    bm.to_mesh(caixa.data); bm.free()
    yf0, yf1 = -D - FT, -D
    z0, z1 = PL + GAP, TOP0 - GAP
    # pia: duas portas com puxador vertical junto ao encontro
    for i, (a, b) in enumerate(((0, XS / 2), (XS / 2, XS))):
        box(f'porta{i}', a + GAP, b - GAP, yf0, yf1, z0, z1, M['madeira'], 0.0025, veio='v')
        px = b - 0.045 if i == 0 else a + 0.045
        tube(f'puxador_p{i}', [(px, yf0, z1 - 0.06), (px, yf0 - 0.025, z1 - 0.07), (px, yf0 - 0.025, z1 - 0.25), (px, yf0, z1 - 0.26)], 0.0055, M['puxador'])
    # cooktop: três gavetas (a de cima mais baixa, as de baixo para panelas)
    hs = [0.16, 0.28, 0.28]
    zc = z1
    for i, h in enumerate(hs):
        za = zc - h + GAP
        box(f'gaveta{i}', XS + GAP, L - GAP, yf0, yf1, max(za, z0), zc - GAP, M['madeira'], 0.0025, veio='v')
        zm = zc - 0.05 if i == 0 else zc - 0.06
        xm = (XS + L) / 2
        tube(f'puxador_g{i}', [(xm - 0.16, yf0, zm), (xm - 0.15, yf0 - 0.025, zm), (xm + 0.15, yf0 - 0.025, zm), (xm + 0.16, yf0, zm)], 0.0055, M['puxador'])
        zc = za - GAP

    # ---------------------------------------------------------------- tampo com recorte da cuba e espelho traseiro
    CW, CD, CR = 0.50, 0.40, 0.035   # recorte (abertura da cuba)
    bm = bmesh.new()
    x0, x1, y0, y1 = -0.01, L + 0.01, -D - FT - OVF + 0.02, 0.0
    outer_t = [bm.verts.new(p) for p in ((x0, y0, TOP1), (x1, y0, TOP1), (x1, y1, TOP1), (x0, y1, TOP1))]
    outer_b = [bm.verts.new((v.co.x, v.co.y, TOP0)) for v in outer_t]
    hole_t = rrect(bm, *SINK, CW, CD, CR, TOP1)
    hole_b = rrect(bm, *SINK, CW, CD, CR, TOP0)
    for i in range(4):  # bordas externas
        j = (i + 1) % 4
        bm.faces.new((outer_b[i], outer_b[j], outer_t[j], outer_t[i]))
    for i in range(len(hole_t)):  # parede do furo
        j = (i + 1) % len(hole_t)
        bm.faces.new((hole_t[i], hole_t[j], hole_b[j], hole_b[i]))
    # faces de cima e de baixo como anel (retângulo → furo), ligando cada canto ao arco mais próximo
    def cap(outer, hole, up):
        n = len(hole); k = n // 4
        corners = [2, 3, 0, 1]  # canto externo de cada quadrante do furo (+x+y, -x+y, -x-y, +x-y)
        for q in range(4):
            c = outer[corners[q]]
            arc = hole[q * k:(q + 1) * k + 1] if q < 3 else hole[3 * k:] + [hole[0]]
            for a, b in zip(arc, arc[1:]):
                f = (c, a, b) if up else (c, b, a)
                bm.faces.new(f)
            nxt = outer[corners[(q + 1) % 4]]
            last = arc[-1]
            bm.faces.new((c, last, nxt) if up else (c, nxt, last))
    cap(outer_t, hole_t, False)
    cap(outer_b, hole_b, True)
    tampo = finish('tampo', bm, M['granito'])
    bevel(tampo, 0.003, 2)
    tampo.modifiers['bev'].limit_method = 'ANGLE'
    tampo.modifiers['bev'].angle_limit = math.radians(60)
    box('espelho', -0.01, L + 0.01, -0.02, 0.0, TOP1, TOP1 + 0.07, M['granito'], 0.003)

    # ---------------------------------------------------------------- cuba inox com borda (aro) sobre o granito
    RW, RD = CW + 0.03, CD + 0.03
    bm = bmesh.new()
    o = rrect(bm, *SINK, RW, RD, CR + 0.015, TOP1 + 0.004)
    i_ = rrect(bm, *SINK, CW, CD, CR, TOP1 + 0.004)
    ring(bm, o, i_)
    o2 = rrect(bm, *SINK, RW, RD, CR + 0.015, TOP1)
    ring(bm, o2, o)
    lv = i_
    for depth, shrink in ((0.004, 0.0), (0.03, 0.002), (0.17, 0.018), (0.185, 0.03)):
        nv = rrect(bm, *SINK, CW - 2 * shrink, CD - 2 * shrink, max(CR - shrink, 0.012), TOP1 - depth)
        ring(bm, lv, nv)
        lv = nv
    c = bm.verts.new((SINK[0], SINK[1], TOP1 - 0.19))
    for a, b in zip(lv, lv[1:] + lv[:1]):
        bm.faces.new((a, b, c))
    bm.normal_update()
    for f in bm.faces:  # aro para cima, paredes e fundo voltados para dentro da cuba
        c = f.calc_center_median()
        want = Vector((0, 0, 1)) if c.z >= TOP1 - 0.001 else (Vector((SINK[0], SINK[1], TOP1 - 0.1)) - c)
        if f.normal.dot(want) < 0:
            f.normal_flip()
    me = bpy.data.meshes.new('cuba'); bm.to_mesh(me); bm.free()
    cuba = link(bpy.data.objects.new('cuba', me), M['cuba'])
    for p in cuba.data.polygons:  # borda chata: sem suavizar o aro
        p.use_smooth = p.center.z < TOP1
    cyl('ralo', 0.045, TOP1 - 0.19, TOP1 - 0.186, SINK[0], SINK[1], M['inox'])
    cyl('ralo_furo', 0.022, TOP1 - 0.186, TOP1 - 0.185, SINK[0], SINK[1], M['rodape'])

    # ---------------------------------------------------------------- torneira gourmet de bica alta
    FX, FY = SINK[0], -0.06
    cyl('torneira_base', 0.026, TOP1, TOP1 + 0.03, FX, FY, M['inox'], 32)
    H = 0.36
    reach = SINK[1] - FY + 0.04   # bica termina um pouco além do centro da cuba (negativo: para a frente)
    pts = [(FX, FY, TOP1 + 0.02), (FX, FY, TOP1 + H - 0.09)]
    for k in range(1, 13):
        a = math.pi * k / 12
        pts.append((FX, FY + (reach / 2) * (1 - math.cos(a)), TOP1 + H - 0.09 + abs(reach) / 2 * math.sin(a) * 1.25))
    pts.append((FX, FY + reach, TOP1 + H - 0.16))
    tube('torneira', pts, 0.0125, M['inox'])
    cyl('arejador', 0.015, TOP1 + H - 0.175, TOP1 + H - 0.155, FX, FY + reach, M['inox'])
    # alavanca lateral
    tube('alavanca_corpo', [(FX, FY, TOP1 + 0.16), (FX + 0.035, FY, TOP1 + 0.16)], 0.016, M['inox'])
    tube('alavanca', [(FX + 0.03, FY, TOP1 + 0.165), (FX + 0.08, FY, TOP1 + 0.18), (FX + 0.09, FY - 0.012, TOP1 + 0.185)], 0.006, M['inox'])

    # ---------------------------------------------------------------- cooktop de vidro, 4 bocas (sobre o tampo, borda chanfrada)
    GW, GD = 0.58, 0.51
    box('cooktop', HOB[0] - GW / 2, HOB[0] + GW / 2, HOB[1] - GD / 2, HOB[1] + GD / 2, TOP1, TOP1 + 0.006, M['vidro'], 0.002, 1)
    bocas = [(-0.14, 0.11, 0.095), (0.14, 0.11, 0.075), (-0.14, -0.10, 0.075), (0.14, -0.10, 0.095)]
    for n, (dx, dy, r) in enumerate(bocas):
        for rr in (r, r * 0.55):
            bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.0012, major_segments=40, minor_segments=4,
                                             location=(HOB[0] + dx, HOB[1] + dy, TOP1 + 0.006))
            t = bpy.context.active_object
            t.scale.z = 0.3
            t.name = f'boca{n}'
            t.data.materials.append(M['serigrafia'])
    # comandos touch na frente
    for k in range(5):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.007, depth=0.0008, vertices=16, location=(HOB[0] - 0.08 + k * 0.04, HOB[1] - GD / 2 + 0.035, TOP1 + 0.0062))
        bpy.context.active_object.data.materials.append(M['serigrafia'])


# ---------------------------------------------------------------- armário aéreo: 3 portas, veio vertical, 1,52–2,12 m do piso
AL, AD, AZ0, AZ1 = L, 0.33, 1.52, 2.12


def aereo():
    box('aereo_caixa', -AL / 2, AL / 2, -AD, 0, AZ0, AZ1, M['madeira'])
    w = AL / 3
    for i in range(3):
        a = -AL / 2 + i * w
        box(f'aereo_porta{i}', a + GAP, a + w - GAP, -AD - FT, -AD, AZ0 + GAP, AZ1 - GAP, M['madeira'], 0.0025, veio='v')
        px = a + w - 0.045 if i < 2 else a + 0.045   # puxador na base, do lado que abre
        pull(f'aereo_puxador{i}', px, -AD - FT, AZ0 + 0.13, 0.16, M['puxador'])


# ---------------------------------------------------------------- geladeira inox duplex (congelador em cima), 0,62 × 0,66 × 1,80
GW_, GD_, GH = 0.62, 0.66, 1.80


def geladeira():
    box('gel_corpo', -GW_ / 2, GW_ / 2, -GD_ + 0.05, -0.02, 0.06, GH, M['inox'], 0.01, 3)
    box('gel_base', -GW_ / 2 + 0.02, GW_ / 2 - 0.02, -GD_ + 0.08, -0.06, 0, 0.06, M['borracha'])
    zc = 1.30  # divisa congelador | refrigerador
    box('gel_porta_inf', -GW_ / 2, GW_ / 2, -GD_, -GD_ + 0.05, 0.065, zc - 0.006, M['inox'], 0.012, 3)
    box('gel_porta_sup', -GW_ / 2, GW_ / 2, -GD_, -GD_ + 0.05, zc + 0.006, GH - 0.005, M['inox'], 0.012, 3)
    box('gel_vedacao', -GW_ / 2 + 0.01, GW_ / 2 - 0.01, -GD_ + 0.04, -GD_ + 0.05, zc - 0.006, zc + 0.006, M['borracha'])
    # puxadores verticais embutidos na lateral que abre (+X), barras inox com pés
    hx, hy = GW_ / 2 - 0.05, -GD_
    for nm, za, zb in (('inf', 0.75, 1.22), ('sup', 1.38, 1.62)):
        tube(f'gel_puxador_{nm}', [(hx, hy, zb), (hx, hy - 0.035, zb - 0.015), (hx, hy - 0.035, za + 0.015), (hx, hy, za)], 0.011, M['inox'])
    # painel de temperatura discreto na porta de cima
    box('gel_painel', -0.06, 0.06, -GD_ - 0.001, -GD_, 1.52, 1.56, M['vidro'])


def shift(objs, dx):
    for o in objs:
        o.location.x += dx


def piece(build, rel):
    global M
    reset(); lib._mats.clear(); M = lib.M()
    build()
    export(rel)


import lib
piece(lambda: (bancada(), shift(col().objects, -L / 2)), 'cozinha/cozinha.glb')
piece(aereo, 'cozinha/aereo.glb')
piece(geladeira, 'cozinha/geladeira.glb')

# ---------------------------------------------------------------- prévia (opcional): as três peças como ficam na parede
a = args()
if '--preview' in a:
    reset(); lib._mats.clear(); M = lib.M()
    bancada(); shift(col().objects, -L / 2)
    aereo()
    n0 = len(col().objects)
    geladeira()
    shift(list(col().objects)[n0:], -1.22)   # geladeira em z 4,12–4,74 (bancada começa em 4,8)
    preview(a[a.index('--preview') + 1], (0.9, -2.6, 1.6), (-0.3, -0.3, 1.0), 28)
