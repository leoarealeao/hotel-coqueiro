import bpy,sys,math,time,json
from mathutils import Vector
S=sys.argv[1]
def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def hx(h):h=h.lstrip('#');return tuple(lin(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
REBOCO={'#f4f1ea','#fbfaf6','#e9e4d8','#f1ede4','#e3ddd0','#f9f8f5'}
MADEIRA={'#5a3420','#3a2212','#7a4c2c','#6b4226','#8a5a36','#9a6a3e','#a9805c','#3a2a1c','#82664c','#8a6f4d'}
TECIDO={'#efe9dc','#efe6cf','#d9cdb6','#ece6d8','#c58a5a','#7e9a84','#c8a878','#e9dcc0','#f4eee0'}
PALHA={'#cdb07a','#b98f55','#bfa06a','#d8c08f','#d9c7a0','#cdbb98','#dcc49a'}
PEDRA={'#e6dcc6','#b9b4aa','#ddd2ba','#a8a398','#eadfc6','#d8c7a2'}
CARRO={'#3d5a80','#444444','#8d8d8d','#d9d9d9','#e8e8e8','#b8433a'}
FOLHA={'#3f8f3a','#4d9c45'}
def novo(m):
    nt=m.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');b=nt.nodes.new('ShaderNodeBsdfPrincipled');nt.links.new(b.outputs[0],o.inputs[0]);return nt,b
def ruido(nt,esc,det=4,rug=.6,vec=None,coord='Object',estica=None):
    tc=nt.nodes.new('ShaderNodeTexCoord');n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=esc;n.inputs['Detail'].default_value=det;n.inputs['Roughness'].default_value=rug
    if estica:
        mp=nt.nodes.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=estica;nt.links.new(tc.outputs[coord],mp.inputs[0]);nt.links.new(mp.outputs[0],n.inputs['Vector'])
    else:nt.links.new(tc.outputs[coord],n.inputs['Vector'])
    return n
def rampa(nt,src,c0,c1,p0=.3,p1=.7):
    r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=p0;r.color_ramp.elements[0].color=c0;r.color_ramp.elements[1].position=p1;r.color_ramp.elements[1].color=c1;nt.links.new(src,r.inputs[0]);return r
def relevo(nt,b,src,f,dist=.02):
    bp=nt.nodes.new('ShaderNodeBump');bp.inputs['Strength'].default_value=f;bp.inputs['Distance'].default_value=dist;nt.links.new(src,bp.inputs['Height']);nt.links.new(bp.outputs[0],b.inputs['Normal']);return bp
def esc(c,k):return (c[0]*k,c[1]*k,c[2]*k,1)
def mat_cor(m,c,rough,bump=None,var=.0,escv=8,metal=0):
    nt,b=novo(m);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if var:
        n=ruido(nt,escv,5,.6);r=rampa(nt,n.outputs['Fac'],esc(c,1-var),esc(c,1+var*.6));nt.links.new(r.outputs[0],b.inputs['Base Color'])
    else:b.inputs['Base Color'].default_value=c
    if bump:
        n2=ruido(nt,bump[0],6,.7);relevo(nt,b,n2.outputs['Fac'],bump[1],bump[2] if len(bump)>2 else .01)
    return nt,b
def materiais():
    for m in bpy.data.materials:
        if not m.node_tree:continue
        b=m.node_tree.nodes.get('Principled BSDF')
        if not b:   # luminárias (sem sombreamento no modelo)
            nt=m.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');e=nt.nodes.new('ShaderNodeEmission');e.inputs[0].default_value=hx('#ffd9a0');e.inputs[1].default_value=6;nt.links.new(e.outputs[0],o.inputs[0]);continue
        c=b.inputs['Base Color'];img=c.links[0].from_node.image.name if c.links else None
        h='#%02x%02x%02x'%tuple(round(v*255) for v in c.default_value[:3]);alpha=b.inputs['Alpha'].default_value
        m['hex']=h;m['img']=img or ''
        if img=='Image_0' or h=='#cdbf9f':   # areia
            nt,b=mat_cor(m,hx('#d8b074'),.95,None,.12,2.5);n=ruido(nt,45,8,.75);n2=ruido(nt,.6,3,.5);mx=nt.nodes.new('ShaderNodeMath');mx.operation='ADD';nt.links.new(n.outputs['Fac'],mx.inputs[0]);ml=nt.nodes.new('ShaderNodeMath');ml.operation='MULTIPLY';ml.inputs[1].default_value=3;nt.links.new(n2.outputs['Fac'],ml.inputs[0]);nt.links.new(ml.outputs[0],mx.inputs[1]);relevo(nt,b,mx.outputs[0],.5,.03)
        elif img=='Image_1' or h=='#4f8c3e':   # gramado e cerca viva
            nt,b=novo(m);b.inputs['Roughness'].default_value=.9;n=ruido(nt,1.3,5,.6);r=rampa(nt,n.outputs['Fac'],hx('#84ad3e'),hx('#b7d468'),.35,.7);nf=ruido(nt,220,3,.8);rf=rampa(nt,nf.outputs['Fac'],(.72,.72,.72,1),(1.12,1.12,1.12,1),.3,.75);mm=nt.nodes.new('ShaderNodeMixRGB');mm.blend_type='MULTIPLY';mm.inputs[0].default_value=1;nt.links.new(r.outputs[0],mm.inputs[1]);nt.links.new(rf.outputs[0],mm.inputs[2]);nt.links.new(mm.outputs[0],b.inputs['Base Color']);relevo(nt,b,nf.outputs['Fac'],1,.04)
        elif img=='Image_2':   # cimento queimado
            m['piso']=1
            nt,b=mat_cor(m,hx('#a9a59c'),.32,(3,.15,.01),.10,1.2)
        elif img=='Image_6':   # palha (provisório: passo 2)
            nt,b=novo(m);b.inputs['Roughness'].default_value=1;n=ruido(nt,3,5,.7,estica=(40,40,2.2));r=rampa(nt,n.outputs['Fac'],hx('#6f5a3c'),hx('#c2a878'),.3,.72);n2=ruido(nt,.8,3,.5);r2=rampa(nt,n2.outputs['Fac'],(.8,.8,.8,1),(1.1,1.1,1.1,1));mm=nt.nodes.new('ShaderNodeMixRGB');mm.blend_type='MULTIPLY';mm.inputs[0].default_value=1;nt.links.new(r.outputs[0],mm.inputs[1]);nt.links.new(r2.outputs[0],mm.inputs[2]);nt.links.new(mm.outputs[0],b.inputs['Base Color']);relevo(nt,b,n.outputs['Fac'],1,.06)
        elif img=='Image_3' or h in MADEIRA:   # madeira
            base=hx('#6a4326') if img else hx(h);nt,b=novo(m);b.inputs['Roughness'].default_value=.55;n=ruido(nt,6,6,.65,estica=(1,1,.08));n2=ruido(nt,6,6,.65,estica=(.08,1,1));mx=nt.nodes.new('ShaderNodeMath');mx.operation='MULTIPLY';nt.links.new(n.outputs['Fac'],mx.inputs[0]);nt.links.new(n2.outputs['Fac'],mx.inputs[1]);r=rampa(nt,mx.outputs[0],esc(base,.62),esc(base,1.25),.12,.42);nt.links.new(r.outputs[0],b.inputs['Base Color']);relevo(nt,b,mx.outputs[0],.25,.005)
        elif img=='Image_4' or h in TECIDO:mat_cor(m,hx('#e9e2d2') if img else hx(h),1,(900,.35,.002),.05,3)
        elif img=='Image_5' or h in PALHA:mat_cor(m,hx('#c2a06a') if img else hx(h),.85,(260,.8,.006),.18,90)
        elif h in REBOCO:mat_cor(m,hx('#e9e2d3'),.92,(70,.22,.004),.04,.9)
        elif h in PEDRA:mat_cor(m,hx(h),.75,(40,.4,.006),.10,6)
        elif h in CARRO:mat_cor(m,hx(h),.28,None,0,1,.75)
        elif h=='#2c3440':mat_cor(m,hx('#0b0f14'),.05)
        elif h in FOLHA:mat_cor(m,hx('#3f7a2e'),.6,None,.2,5)
        elif h=='#c9703f':mat_cor(m,hx(h),.7,(60,.3,.004),.1,8)
        elif h=='#35c3c9':   # água
            nt,b=novo(m);b.inputs['Base Color'].default_value=hx('#1c8f98');b.inputs['Roughness'].default_value=.03;b.inputs['IOR'].default_value=1.33;n=ruido(nt,2.2,3,.5);relevo(nt,b,n.outputs['Fac'],.35,.05)
        elif alpha<.9:   # vidro arquitetônico: transparente com reflexo
            nt=m.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');t=nt.nodes.new('ShaderNodeBsdfTransparent');t.inputs[0].default_value=(.86,.93,.93,1);g=nt.nodes.new('ShaderNodeBsdfGlossy');g.inputs['Roughness'].default_value=.02;mx=nt.nodes.new('ShaderNodeMixShader');f=nt.nodes.new('ShaderNodeFresnel');f.inputs[0].default_value=1.5;nt.links.new(f.outputs[0],mx.inputs[0]);nt.links.new(t.outputs[0],mx.inputs[1]);nt.links.new(g.outputs[0],mx.inputs[2]);nt.links.new(mx.outputs[0],o.inputs[0])
        elif h=='#ffe2a8':
            nt,b=novo(m);b.inputs['Base Color'].default_value=hx(h);b.inputs['Emission Color'].default_value=hx('#ffd9a0');b.inputs['Emission Strength'].default_value=5
        else:
            col=hx(h);rg=.6
            if c.links:continue
            mat_cor(m,col,rg)
def montar(el_sol=22,forca_sol=4.2,ceu=.32):
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=S+'/uni/so_o_condominio.glb');sc=bpy.context.scene;materiais()
    for o in sc.objects:
        if o.type=='MESH' and o.material_slots and o.material_slots[0].material and o.material_slots[0].material.get('piso'):o.scale=(.993,.993,.98)
    # chão de areia até o horizonte
    bpy.ops.mesh.primitive_plane_add(size=3000,location=(26,-11,-.045));p=bpy.context.object;m=bpy.data.materials.new('areia_fora');m.use_nodes=True;p.data.materials.append(m)
    nt,b=mat_cor(m,hx('#d8b074'),.95,(30,.5,.03),.12,.15)
    el=math.radians(el_sol);th=math.radians(160.8);s=Vector((math.cos(el)*math.cos(th),math.cos(el)*math.sin(th),math.sin(el)))
    L=bpy.data.lights.new('sol','SUN');L.energy=forca_sol;L.angle=math.radians(1.5);L.color=(1,.86,.68);o=bpy.data.objects.new('sol',L);sc.collection.objects.link(o);o.rotation_euler=s.to_track_quat('Z','Y').to_euler()
    w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;nt=w.node_tree;bg=nt.nodes['Background'];sky=nt.nodes.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_disc=False;sky.sun_elevation=el;sky.sun_rotation=math.radians(90-160.8)
    nt.links.new(sky.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=ceu
    sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.use_denoising=True;sc.cycles.max_bounces=6;sc.cycles.transparent_max_bounces=12;sc.cycles.caustics_reflective=False;sc.cycles.caustics_refractive=False
    sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-.3
    try:sc.view_settings.look='AgX - Medium High Contrast'
    except Exception as e:print('look',e)
    return sc
def foto(sc,p,a,fov,saida,amostras=96,res=(1280,720)):
    c=bpy.data.cameras.new('c');o=bpy.data.objects.new('c',c);sc.collection.objects.link(o)
    P=Vector((p[0],-p[2],p[1]));A=Vector((a[0],-a[2],a[1]));o.location=P;o.rotation_euler=(A-P).to_track_quat('-Z','Y').to_euler()
    c.sensor_fit='VERTICAL';c.angle_y=math.radians(fov);c.clip_start=.05;sc.camera=o
    sc.cycles.samples=amostras;sc.render.resolution_x,sc.render.resolution_y=res;sc.render.filepath=saida;t=time.time();bpy.ops.render.render(write_still=True);print('FOTO %s %.0fs'%(saida,time.time()-t))
if __name__=='__main__':
    sc=montar();cams=json.load(open(S+'/uni/cams.json'));quais=[int(x) for x in sys.argv[2].split(',')];am=int(sys.argv[3]) if len(sys.argv)>3 else 96
    for n in quais:
        nome,p,a,f=cams[n-1];foto(sc,p,a,f,S+'/bl/out/%02d_%s.png'%(n,nome),am)
