import bpy,bmesh,sys,math,random,json,time
import numpy as np
from PIL import Image,ImageDraw
from mathutils import Vector
sys.path.insert(0,sys.argv[1]+'/bl');import cena,cena2,carro as carro_mod
from cena import hx,novo,ruido,rampa,relevo,esc
S=sys.argv[1]
def hexo(o):
    return o.material_slots[0].material.get('hex') if o.type=='MESH' and o.material_slots and o.material_slots[0].material else None
def imgo(o):
    return o.material_slots[0].material.get('img') if o.type=='MESH' and o.material_slots and o.material_slots[0].material else None
def caixa(o):
    vs=[o.matrix_world@Vector(c) for c in o.bound_box];return min(v.x for v in vs),max(v.x for v in vs),min(v.y for v in vs),max(v.y for v in vs),min(v.z for v in vs),max(v.z for v in vs)
def grama(sc,dens=3200):
    C=.02;X0,Y0=15.5,-23.5;W,H=int(38.5/C),int(24/C);ok=np.zeros((H,W),bool)
    def cel(x,y):return int((x-X0)/C),int((y-Y0)/C)
    for (xa,xb,za,zb) in [(16.05,21,.2,22.8),(21,52.7,10.2,15.8),(51.05,52.8,.2,22.8)]:   # jardim da frente, pátio, faixa do fundo (x, z da maquete)
        i0,j0=cel(xa,-zb);i1,j1=cel(xb,-za);ok[j0:j1,i0:i1]=True
    gram=None;n=0
    for o in sc.objects:
        if o.type!='MESH' or o.name.startswith(('coq','cf','franja')):continue
        x0,x1,y0,y1,z0,z1=caixa(o)
        if imgo(o)=='Image_1' and (x1-x0)>30:gram=o;continue
        if (x1-x0)>60 or z0>.3 or z1<.03:continue
        if hexo(o) in ('#35c3c9','#e6dcc6'):
            pts=[o.matrix_world@v.co for v in o.data.vertices];cx=sum(p.x for p in pts)/len(pts);cy=sum(p.y for p in pts)/len(pts)
            pts.sort(key=lambda p:math.atan2(p.y-cy,p.x-cx));im=Image.new('1',(W,H),0);ImageDraw.Draw(im).polygon([cel(p.x+(p.x-cx)*.02,p.y+(p.y-cy)*.05) for p in pts],fill=1);ok&=~np.array(im,bool);continue
        i0,j0=cel(x0-.02,y0-.02);i1,j1=cel(x1+.02,y1+.02);ok[max(0,j0):max(0,j1+1),max(0,i0):max(0,i1+1)]=False;n+=1
    for o in sc.objects:   # pé dos coqueiros
        if o.name.startswith('coq'):
            i,j=cel(o.location.x,o.location.y);r=int(.3/C);ok[max(0,j-r):j+r,max(0,i-r):i+r]=False
    zg=caixa(gram)[5];area=ok.sum()*C*C;N=int(area*dens);print('gramado %.0f m2, %d folhas, %d obstaculos'%(area,N,n))
    rs=np.random.RandomState(5);jj,ii=np.nonzero(ok);k=rs.randint(0,len(jj),N);px=X0+(ii[k]+rs.rand(N))*C;py=Y0+(jj[k]+rs.rand(N))*C
    th=rs.rand(N)*6.283;w=rs.uniform(.008,.016,N);h=rs.uniform(.035,.1,N)*(.75+.5*rs.rand(N));ph=rs.rand(N)*6.283;le=h*rs.uniform(0,.6,N)
    co=np.zeros((N,3,3),np.float32);co[:,0,0]=px-np.cos(th)*w/2;co[:,0,1]=py-np.sin(th)*w/2;co[:,1,0]=px+np.cos(th)*w/2;co[:,1,1]=py+np.sin(th)*w/2;co[:,2,0]=px+np.cos(ph)*le;co[:,2,1]=py+np.sin(ph)*le;co[:,:2,2]=zg-.005;co[:,2,2]=zg+h
    me=bpy.data.meshes.new('grama');me.vertices.add(3*N);me.loops.add(3*N);me.polygons.add(N);me.vertices.foreach_set('co',co.ravel());me.loops.foreach_set('vertex_index',np.arange(3*N,dtype=np.int32));me.polygons.foreach_set('loop_start',np.arange(0,3*N,3,dtype=np.int32));me.polygons.foreach_set('loop_total',np.full(N,3,np.int32))
    uv=me.uv_layers.new(name='uv');u=np.tile(np.array([0,0,1,0,.5,1],np.float32),N);uv.data.foreach_set('uv',u);me.update()
    m=bpy.data.materials.new('grama_folha');m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');b=nt.nodes.new('ShaderNodeBsdfPrincipled');b.inputs['Roughness'].default_value=.55
    tc=nt.nodes.new('ShaderNodeTexCoord');sp=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(tc.outputs['UV'],sp.inputs[0]);alt=rampa(nt,sp.outputs['Y'],hx('#3e6a22'),hx('#a4cb58'),.0,.9)
    n1=ruido(nt,.9,4,.6);r1=rampa(nt,n1.outputs['Fac'],(.72,.8,.6,1),(1.12,1.08,.95,1),.3,.72);n2=ruido(nt,30,2,.5);r2=rampa(nt,n2.outputs['Fac'],(.8,.8,.8,1),(1.15,1.15,1.15,1))
    a=nt.nodes.new('ShaderNodeMixRGB');a.blend_type='MULTIPLY';a.inputs[0].default_value=1;nt.links.new(alt.outputs[0],a.inputs[1]);nt.links.new(r1.outputs[0],a.inputs[2])
    a2=nt.nodes.new('ShaderNodeMixRGB');a2.blend_type='MULTIPLY';a2.inputs[0].default_value=1;nt.links.new(a.outputs[0],a2.inputs[1]);nt.links.new(r2.outputs[0],a2.inputs[2]);nt.links.new(a2.outputs[0],b.inputs['Base Color'])
    t=nt.nodes.new('ShaderNodeBsdfTranslucent');nt.links.new(a2.outputs[0],t.inputs[0]);mx=nt.nodes.new('ShaderNodeMixShader');mx.inputs[0].default_value=.3;nt.links.new(b.outputs[0],mx.inputs[1]);nt.links.new(t.outputs[0],mx.inputs[2]);nt.links.new(mx.outputs[0],out.inputs[0])
    me.materials.append(m);ob=bpy.data.objects.new('grama',me);sc.collection.objects.link(ob)
    gm=gram.material_slots[0].material;nt,b=novo(gm);b.inputs['Roughness'].default_value=1;n=ruido(nt,2,4,.6);r=rampa(nt,n.outputs['Fac'],hx('#33511f'),hx('#54782d'));nt.links.new(r.outputs[0],b.inputs['Base Color'])
def carros(sc):
    corpo=[o for o in sc.objects if hexo(o) in cena.CARRO];cab=[o for o in sc.objects if hexo(o)=='#2c3440'];rod=[o for o in sc.objects if hexo(o)=='#222222' and o.dimensions.z<.5 and o.dimensions.z>.2 and caixa(o)[4]<.3]
    print('carros',len(corpo),'cabines',len(cab),'rodas',len(rod))
    def bisel(o,w,topo=None):
        if topo:
            zc=sum(v.co.z for v in o.data.vertices)/len(o.data.vertices);ax=0 if o.dimensions.x>o.dimensions.y else 1
            cm=sum(v.co[ax] for v in o.data.vertices)/len(o.data.vertices)
            for v in o.data.vertices:
                if v.co.z>zc:v.co[ax]=cm+(v.co[ax]-cm)*topo;v.co[1-ax]*=1 if abs(v.co[1-ax])<1e-6 else .93
        md=o.modifiers.new('b','BEVEL');md.width=w;md.segments=5;md.limit_method='ANGLE'
        for p in o.data.polygons:p.use_smooth=True
    for o in corpo:bisel(o,.2)
    for o in cab:bisel(o,.16,.72)
    mp=bpy.data.materials.new('pneu');mp.use_nodes=True;nt,b=novo(mp);b.inputs['Base Color'].default_value=hx('#151515');b.inputs['Roughness'].default_value=.8
    mc=bpy.data.materials.new('calota');mc.use_nodes=True;nt,b=novo(mc);b.inputs['Base Color'].default_value=hx('#b8bcc0');b.inputs['Roughness'].default_value=.3;b.inputs['Metallic'].default_value=.9
    for o in rod:
        x0,x1,y0,y1,z0,z1=caixa(o);eixo_y=(y1-y0)>(x1-x0);cx,cy=(x0+x1)/2,(y0+y1)/2;R=.34
        for sgn in (-1,1):
            loc=(cx,cy+sgn*((y1-y0)/2-.12),R) if eixo_y else (cx+sgn*((x1-x0)/2-.12),cy,R);rot=(math.pi/2,0,0) if eixo_y else (0,math.pi/2,0)
            bpy.ops.mesh.primitive_cylinder_add(radius=R,depth=.24,vertices=28,location=loc,rotation=rot);p=bpy.context.object;p.data.materials.append(mp);md=p.modifiers.new('b','BEVEL');md.width=.05;md.segments=3
            for q in p.data.polygons:q.use_smooth=True
            bpy.ops.mesh.primitive_cylinder_add(radius=R*.58,depth=.26,vertices=24,location=loc,rotation=rot);bpy.context.object.data.materials.append(mc)
        bpy.data.objects.remove(o,do_unlink=True)
def nuvens(sc,cob=.6):
    nt=sc.world.node_tree;bg=nt.nodes['Background'];sky=[n for n in nt.nodes if n.bl_idname=='ShaderNodeTexSky'][0]
    tc=nt.nodes.new('ShaderNodeTexCoord');sp=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(tc.outputs['Generated'],sp.inputs[0])
    dz=nt.nodes.new('ShaderNodeMath');dz.operation='ADD';dz.inputs[1].default_value=.12;nt.links.new(sp.outputs['Z'],dz.inputs[0])
    ux=nt.nodes.new('ShaderNodeMath');ux.operation='DIVIDE';nt.links.new(sp.outputs['X'],ux.inputs[0]);nt.links.new(dz.outputs[0],ux.inputs[1])
    uy=nt.nodes.new('ShaderNodeMath');uy.operation='DIVIDE';nt.links.new(sp.outputs['Y'],uy.inputs[0]);nt.links.new(dz.outputs[0],uy.inputs[1])
    cb=nt.nodes.new('ShaderNodeCombineXYZ');nt.links.new(ux.outputs[0],cb.inputs[0]);nt.links.new(uy.outputs[0],cb.inputs[1])
    n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=.55;n.inputs['Detail'].default_value=8;n.inputs['Roughness'].default_value=.62;n.inputs['Distortion'].default_value=.6;nt.links.new(cb.outputs[0],n.inputs['Vector'])
    r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=1-cob*.9;r.color_ramp.elements[0].color=(0,0,0,1);r.color_ramp.elements[1].position=min(1,1.22-cob*.9);r.color_ramp.elements[1].color=(1,1,1,1);nt.links.new(n.outputs['Fac'],r.inputs[0])
    hz=nt.nodes.new('ShaderNodeValToRGB');hz.color_ramp.elements[0].position=.03;hz.color_ramp.elements[1].position=.22;nt.links.new(sp.outputs['Z'],hz.inputs[0])
    f=nt.nodes.new('ShaderNodeMath');f.operation='MULTIPLY';nt.links.new(r.outputs[0],f.inputs[0]);nt.links.new(hz.outputs[0],f.inputs[1])
    f2=nt.nodes.new('ShaderNodeMath');f2.operation='MULTIPLY';f2.inputs[1].default_value=.9;nt.links.new(f.outputs[0],f2.inputs[0])
    mx=nt.nodes.new('ShaderNodeMixRGB');nt.links.new(f2.outputs[0],mx.inputs[0]);nt.links.new(sky.outputs[0],mx.inputs[1]);mx.inputs[2].default_value=(NUV[0],NUV[1],NUV[2],1);nt.links.new(mx.outputs[0],bg.inputs[0])
NUV=(5.5,4.9,4.3)
def acabamento(sc):
    for m in bpy.data.materials:   # reboco com manchas suaves e areia com grão
        h=m.get('hex')
        if h in cena.REBOCO:
            nt,b=novo(m);b.inputs['Roughness'].default_value=.9;n=ruido(nt,.5,5,.65);r=rampa(nt,n.outputs['Fac'],hx('#e4dccb'),hx('#f4efe4'),.3,.75);nt.links.new(r.outputs[0],b.inputs['Base Color']);n2=ruido(nt,55,6,.7);relevo(nt,b,n2.outputs['Fac'],.3,.006)
        if m.get('img')=='Image_0' or m.name=='areia_fora' and False:
            nt,b=novo(m);b.inputs['Roughness'].default_value=.95;n=ruido(nt,1.4,4,.6);r=rampa(nt,n.outputs['Fac'],hx('#c9a268'),hx('#e2bf88'),.3,.72);g=ruido(nt,380,2,.6);rg=rampa(nt,g.outputs['Fac'],(.78,.76,.72,1),(1.14,1.13,1.1,1),.35,.65)
            mm=nt.nodes.new('ShaderNodeMixRGB');mm.blend_type='MULTIPLY';mm.inputs[0].default_value=1;nt.links.new(r.outputs[0],mm.inputs[1]);nt.links.new(rg.outputs[0],mm.inputs[2]);nt.links.new(mm.outputs[0],b.inputs['Base Color'])
            g2=ruido(nt,14,5,.7);ad=nt.nodes.new('ShaderNodeMath');ad.operation='ADD';nt.links.new(g.outputs['Fac'],ad.inputs[0]);ml=nt.nodes.new('ShaderNodeMath');ml.operation='MULTIPLY';ml.inputs[1].default_value=4;nt.links.new(g2.outputs['Fac'],ml.inputs[0]);nt.links.new(ml.outputs[0],ad.inputs[1]);relevo(nt,b,ad.outputs[0],.9,.03)
def tudo():
    t=time.time();sc=cena.montar();cena2.coqueiros(sc);cena2.palha(sc);cena2.chao_fora();acabamento(sc);carro_mod.trocar(sc,hexo,caixa,cena.CARRO);grama(sc);nuvens(sc);print('cena %.0fs'%(time.time()-t));return sc
if __name__=='__main__':
    sc=tudo();cams=json.load(open(S+'/uni/cams.json'));am=int(sys.argv[3]) if len(sys.argv)>3 else 96;res=tuple(int(v) for v in sys.argv[4].split('x')) if len(sys.argv)>4 else (1280,720);pasta=sys.argv[5] if len(sys.argv)>5 else 'out3'
    cams+=[['t_carros',[9.2,1.7,11.5],[13.5,.8,18.6],58],['t_carros2',[7.5,2.2,9.5],[2.5,.8,5.0],60]]
    for n in [int(x) for x in sys.argv[2].split(',')]:
        nome,p,a,f=cams[n-1];cena.foto(sc,p,a,f,S+'/bl/%s/%02d_%s.png'%(pasta,n,nome),am,res)
