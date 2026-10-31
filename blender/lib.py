# Peças comuns aos scripts de móveis (cozinha.py, sala.py).
# Convenção de cada peça: origem no piso, no meio da face de trás (a que encosta na parede); frente para -Y do Blender
# (= +z do GLB, giro 0 em js/props.js). Peças soltas (mesa, cadeira) têm a origem no centro da base.
# Material com nome conhecido em js/props.js (SWAP) troca pelo shader do site; o resto vai como está.
# Objeto com o['veio'] = 'v' recebe veio de madeira na vertical no site (portas, frentes de gaveta).
import bpy, bmesh, math, os, sys
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def col():
    return bpy.context.scene.collection


_mats = {}


def mat(name, hex_, rough, metal=0.0, image=None):
    if name in _mats and name in bpy.data.materials:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    b.inputs['Base Color'].default_value = [x ** 2.2 for x in c] + [1]
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if image is not None:
        t = m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image = image
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    _mats[name] = m
    return m


# paleta comum (nomes = chaves de SWAP em js/props.js)
def M():
    return {
        'madeira': mat('cz_madeira', '#b98a5a', 0.55),
        'escura': mat('md_escura', '#5a3a24', 0.55),
        'rodape': mat('cz_rodape', '#161514', 0.6),
        'granito': mat('cz_granito', '#262628', 0.28),
        'inox': mat('cz_inox', '#c9ccd0', 0.3, 1.0),
        'cuba': mat('cz_cuba', '#b4b8bc', 0.38, 1.0),
        'vidro': mat('cz_vidro', '#0b0b0c', 0.08),
        'serigrafia': mat('cz_serigrafia', '#9a9a9a', 0.5),
        'puxador': mat('cz_puxador', '#1b1b1b', 0.35, 0.6),
        'linho': mat('tc_linho', '#e6dfd0', 0.95),
        'azul': mat('tc_azul', '#7f93a3', 0.95),
        'terracota': mat('tc_terracota', '#b9714c', 0.95),
        'palha': mat('tc_palha', '#c9a873', 0.9),
        'tela': mat('tv_tela', '#08090a', 0.12),
        'plastico': mat('tv_corpo', '#121212', 0.5),
        'branco': mat('pp_branco', '#f3efe6', 0.8),
        'ceramica': mat('cr_ceramica', '#d9cbb4', 0.5),
        'borracha': mat('cz_borracha', '#2a2a2a', 0.8),
    }


def link(o, m):
    if m is not None:
        o.data.materials.append(m)
    col().objects.link(o)
    return o


def smooth(o, on=True):
    for p in o.data.polygons:
        p.use_smooth = on
    return o


def bevel(o, w, seg=2, angle=None):
    b = o.modifiers.new('bev', 'BEVEL')
    b.width, b.segments, b.limit_method, b.harden_normals = w, seg, 'ANGLE', True
    if angle is not None:
        b.angle_limit = math.radians(angle)
    return smooth(o)


def box(name, x0, x1, y0, y1, z0, z1, m, bw=0.0, seg=2, veio=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me), m)
    if veio:
        o['veio'] = veio
    return bevel(o, bw, seg) if bw else o


def cushion(name, x0, x1, y0, y1, z0, z1, m, r=0.04):
    """Almofada: caixa com cantos bem arredondados e faces levemente estufadas."""
    o = box(name, x0, x1, y0, y1, z0, z1, m)
    sub = o.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
    b = o.modifiers.new('bev', 'BEVEL'); b.width = r; b.segments = 1
    o.modifiers.move(1, 0)  # chanfro antes da subdivisão: cantos macios, faces quase retas
    return smooth(o)


def turn(o, rx=0, ry=0, rz=0, pivot=None):
    """Gira o objeto (graus) em torno de um ponto (padrão: centro da caixa da malha)."""
    from mathutils import Matrix
    if pivot is None:
        vs = [v.co for v in o.data.vertices]
        pivot = sum(vs, Vector()) / len(vs)
    p = Vector(pivot)
    R = Matrix.Rotation(math.radians(rz), 4, 'Z') @ Matrix.Rotation(math.radians(ry), 4, 'Y') @ Matrix.Rotation(math.radians(rx), 4, 'X')
    o.matrix_world = Matrix.Translation(p) @ R @ Matrix.Translation(-p) @ o.matrix_world
    return o


def finish(name, bm, m, sm=False):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me), m)
    return smooth(o, sm)


def cyl(name, r, z0, z1, x, y, m, seg=24, r2=None, bw=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=z1 - z0)
    bmesh.ops.translate(bm, vec=(x, y, (z0 + z1) / 2), verts=bm.verts)
    o = finish(name, bm, m)
    return bevel(o, min(r * 0.3, 0.003) if bw is None else bw, 1, 50)


def tube(name, pts, r, m, res=2):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = r, res, True
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (*q, 1)
    o = bpy.data.objects.new(name, cu)
    col().objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    o.select_set(False)
    o.data.materials.append(m)
    return smooth(o)


def pull(name, x, y, z, length, m, vertical=True):
    """Puxador de barra preta em U (frente -Y)."""
    h = length / 2
    if vertical:
        pts = [(x, y, z + h), (x, y - 0.025, z + h - 0.01), (x, y - 0.025, z - h + 0.01), (x, y, z - h)]
    else:
        pts = [(x - h, y, z), (x - h + 0.01, y - 0.025, z), (x + h - 0.01, y - 0.025, z), (x + h, y, z)]
    return tube(name, pts, 0.0055, m)


def rrect(bm, cx, cy, w, d, r, z, seg=6):
    """Contorno de retângulo arredondado (anti-horário) na altura z."""
    pts = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + sx * (w / 2 - r), cy + sy * (d / 2 - r)
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append(bm.verts.new((ox + r * math.cos(a), oy + r * math.sin(a), z)))
    return pts


def ring(bm, outer, inner):
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((outer[i], outer[j], inner[j], inner[i]))


def export(rel, uv=False):
    """Exporta tudo que está na cena como assets/models/<rel> e diz o peso."""
    out = os.path.join(ROOT, 'assets', 'models', rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for o in list(col().objects):
        o.select_set(True)
    bpy.context.view_layer.objects.active = col().objects[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_apply=True, export_yup=True,
                              export_texcoords=uv, export_normals=True, export_materials='EXPORT', export_extras=True,
                              export_image_format='JPEG', export_jpeg_quality=82)
    tris = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in col().objects:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles(); tris += len(me.loop_triangles); e.to_mesh_clear()
    print(f'GLB: assets/models/{rel}  {os.path.getsize(out) / 1024:.0f} KB  {tris} triângulos')


def preview(png, cam, tgt, lens=30, wall=True):
    """Prévia rápida em Eevee: parede atrás (y = 0), piso, sol baixo e quente."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = 1200, 900
    sc.view_settings.view_transform = 'AgX'
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.9, 0.88, 0.84, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.8
    sc.world = w
    if wall:
        box('_parede', -3, 3, 0, 0.1, 0, 2.7, mat('_p', '#f4f1ea', 0.9))
    box('_piso', -3, 3, -4, 0.1, -0.02, 0, mat('_f', '#e9e4dc', 0.7))
    ld = bpy.data.lights.new('sol', 'SUN'); ld.energy = 3.0; ld.color = (1, 0.88, 0.72); ld.angle = 0.15
    lo = bpy.data.objects.new('sol', ld); lo.rotation_euler = (math.radians(55), 0, math.radians(-35)); col().objects.link(lo)
    ar = bpy.data.lights.new('area', 'AREA'); ar.energy = 150; ar.size = 2
    ao = bpy.data.objects.new('area', ar); ao.location = (0, -1.5, 2.4); ao.rotation_euler = (math.radians(30), 0, 0); col().objects.link(ao)
    cd = bpy.data.cameras.new('cam'); cd.lens = lens
    co = bpy.data.objects.new('cam', cd); col().objects.link(co); sc.camera = co
    co.location = cam
    co.rotation_euler = (Vector(tgt) - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = png
    bpy.ops.render.render(write_still=True)
    print('prévia:', png)


def args():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
