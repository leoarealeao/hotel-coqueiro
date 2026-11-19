# Converte o Jeep Compass 2021 (arquivo .blend enviado pelo Leonardo, fora do repositório) num GLB leve para o site.
# uso: python3 -I blender/jeep.py -- "/caminho/JEEP COMPASS 2021.blend" [faces_alvo]
# Sai assets/models/jeep/jeep.glb: ~4,40 m de comprimento, origem no chão no centro do carro, frente para -Y do Blender
# (= +z do GLB, giro 0 em js/props.js). A lataria fica no material "jp_lataria", que o site recolore por carro.
import bpy, sys, os
from mathutils import Vector, Matrix
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
src, alvo = args[0], int(args[1]) if len(args) > 1 else 60000
bpy.ops.wm.open_mainfile(filepath=src, use_scripts=False)
obs = [o for o in bpy.data.objects if o.type == 'MESH']
total = sum(len(o.data.polygons) for o in obs)
# onde está a traseira: as lanternas vermelhas
red = next(o for o in obs if 'RED GLASS' in o.data.materials[0].name)
cy = sum((red.matrix_world @ Vector(c)).y for c in red.bound_box) / 8
pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
mid = (mn + mx) / 2
frente_menos_y = cy > mid.y            # traseira em +Y -> frente já aponta para -Y
s = 4.40 / (mx.y - mn.y)
T = Matrix.Scale(s, 4) @ Matrix.Translation(Vector((-mid.x, -mid.y, -mn.z)))
if not frente_menos_y: T = Matrix.Rotation(3.14159265, 4, 'Z') @ T
NOMES = {'BODY': 'jp_lataria', 'CLEAR GLASS': 'jp_vidro', 'WINDOW': 'jp_vidro_escuro', 'DARK GLASS': 'jp_vidro_escuro', 'TYRE': 'jp_pneu', 'CHROME': 'jp_cromo'}
for o in obs:
    bpy.context.view_layer.objects.active = o
    n = len(o.data.polygons)
    if n > 400:
        m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = max(0.04, min(1, alvo / total)) * (0.6 if 'PLASTIC' in o.data.materials[0].name else 1.15)
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]): bpy.ops.object.modifier_apply(modifier='dec')
    o.matrix_world = T @ o.matrix_world
    for p in o.data.polygons: p.use_smooth = True
    while o.data.uv_layers: o.data.uv_layers.remove(o.data.uv_layers[0])
    mat = o.data.materials[0]; chave = mat.name.split(' - ')[-1]
    b = next(nd for nd in mat.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
    cor = list(b.inputs['Base Color'].default_value); met = b.inputs['Metallic'].default_value; rug = b.inputs['Roughness'].default_value
    novo = bpy.data.materials.new(NOMES.get(chave, 'jp_' + chave.lower().replace(' ', '_'))); novo.use_nodes = True
    nb = novo.node_tree.nodes['Principled BSDF']
    nb.inputs['Base Color'].default_value = cor; nb.inputs['Metallic'].default_value = met; nb.inputs['Roughness'].default_value = max(rug, 0.08)
    if 'GLASS' in chave or chave == 'WINDOW':
        escuro = chave != 'CLEAR GLASS' and chave != 'RED GLASS'
        if chave != 'RED GLASS': nb.inputs['Base Color'].default_value = (0.02, 0.03, 0.035, 1) if escuro else (0.75, 0.85, 0.88, 1)
        nb.inputs['Alpha'].default_value = 0.82 if escuro else 0.4; nb.inputs['Roughness'].default_value = 0.06
        novo.blend_method = 'BLEND'
    o.data.materials[0] = novo
    o.name = novo.name
print('faces', total, '->', sum(len(o.data.polygons) for o in obs), 'escala', round(s, 3), 'frente -Y:', frente_menos_y)
out = os.path.join(ROOT, 'assets', 'models', 'jeep'); os.makedirs(out, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'jeep.glb'), export_format='GLB', export_apply=True, export_texcoords=False, export_yup=True, export_cameras=False, export_lights=False)
print('ok', os.path.getsize(os.path.join(out, 'jeep.glb')) // 1024, 'KB')
