import bpy,bmesh,math
from mathutils import Vector,Matrix
from cena import hx,novo
def _mat(nome,cor,rough=.4,metal=0,coat=0,emis=None):
    m=bpy.data.materials.new(nome);m.use_nodes=True;nt,b=novo(m);b.inputs['Base Color'].default_value=hx(cor);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if coat and 'Coat Weight' in b.inputs:b.inputs['Coat Weight'].default_value=coat;b.inputs['Coat Roughness'].default_value=.04
    if emis:b.inputs['Emission Color'].default_value=hx(emis[0]);b.inputs['Emission Strength'].default_value=emis[1]
    return m
MATS={}
def mats():
    if not MATS:
        MATS.update(vidro=_mat('car_vidro','#0a0e12',.03),pneu=_mat('car_pneu','#131313',.85),roda=_mat('car_roda','#b9bdc2',.28,.9),preto=_mat('car_plastico','#1b1b1c',.6),farol=_mat('car_farol','#f4f6f8',.08,0,0,('#fff2d8',.6)),lanterna=_mat('car_lanterna','#8a0f0f',.2),cromo=_mat('car_cromo','#c9ccd0',.15,1))
    return MATS
def prisma(nome,perfil,yf,mat,bisel=.06,seg=4):
    bm=bmesh.new();L=[bm.verts.new((x,yf(z),z)) for x,z in perfil];R=[bm.verts.new((x,-yf(z),z)) for x,z in perfil];n=len(perfil)
    bm.faces.new(L);bm.faces.new(R[::-1])
    for i in range(n):bm.faces.new((L[i],R[i],R[(i+1)%n],L[(i+1)%n]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);me=bpy.data.meshes.new(nome);bm.to_mesh(me);bm.free();me.materials.append(mat)
    o=bpy.data.objects.new(nome,me)
    if bisel:
        md=o.modifiers.new('b','BEVEL');md.width=bisel;md.segments=seg;md.limit_method='ANGLE';md.angle_limit=math.radians(25)
    for p in me.polygons:p.use_smooth=True
    return o
def caixa(nome,x0,x1,y0,y1,z0,z1,mat,bisel=.02):
    return prisma(nome,[(x0,z0),(x0,z1),(x1,z1),(x1,z0)],lambda z:0,mat,0) if False else _cx(nome,x0,x1,y0,y1,z0,z1,mat,bisel)
def _cx(nome,x0,x1,y0,y1,z0,z1,mat,bisel):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);me=bpy.data.meshes.new(nome)
    for v in bm.verts:v.co=Vector(((x0+x1)/2+v.co.x*(x1-x0),(y0+y1)/2+v.co.y*(y1-y0),(z0+z1)/2+v.co.z*(z1-z0)))
    bm.to_mesh(me);bm.free();me.materials.append(mat);o=bpy.data.objects.new(nome,me)
    if bisel:
        md=o.modifiers.new('b','BEVEL');md.width=bisel;md.segments=3
    for p in me.polygons:p.use_smooth=True
    return o
def painel(nome,pts,mat):
    bm=bmesh.new();bm.faces.new([bm.verts.new(p) for p in pts]);me=bpy.data.meshes.new(nome);bm.to_mesh(me);bm.free();me.materials.append(mat);return bpy.data.objects.new(nome,me)
def cil(nome,r,w,x,y,z,mat,bis=0,nv=32):
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=nv,radius1=r,radius2=r,depth=w,matrix=Matrix.Translation((x,y,z))@Matrix.Rotation(math.pi/2,4,'X'))
    me=bpy.data.meshes.new(nome);bm.to_mesh(me);bm.free();me.materials.append(mat);o=bpy.data.objects.new(nome,me)
    if bis:
        md=o.modifiers.new('b','BEVEL');md.width=bis;md.segments=4;md.limit_method='ANGLE'
    for p in me.polygons:p.use_smooth=True
    return o
def carro(sc,nome,tipo,cor):
    M=mats();pint=_mat(nome+'_pintura',cor,.32,.35,1);P=[];raiz=bpy.data.objects.new(nome,None);sc.collection.objects.link(raiz)
    HW=.93;EF,ET=1.68,-1.58;RR=.4
    corpo=prisma(nome+'_corpo',[(-2.62,.5),(-2.64,1.02),(-2.5,1.07),(1.0,1.09),(1.9,1.05),(2.5,.97),(2.66,.84),(2.68,.52),(2.5,.36),(-2.5,.36)],lambda z:HW-.05*max(0,(z-.8))/.3-.03*max(0,(.6-z))/.24,pint,.07,5);P.append(corpo)
    for k,ex in enumerate((EF,ET)):   # caixas de roda recortadas
        c=cil(nome+'_corte%d'%k,RR+.07,2.4,ex,0,RR+.02,M['preto'],0,40);c.hide_render=True;c.hide_viewport=True;c.display_type='WIRE';P.append(c)
        md=corpo.modifiers.new('cx%d'%k,'BOOLEAN');md.operation='DIFFERENCE';md.object=c;md.solver='EXACT'
        P.append(cil(nome+'_arco%d'%k,RR+.065,HW*2-.2,ex,0,RR+.02,M['preto'],0,40))
    yc=lambda z:.89-.17*(z-1.05)/.72
    if tipo=='picape':
        cab=[(-.98,1.05),(-.9,1.74),(-.2,1.79),(.38,1.76),(1.12,1.07)];jan=[[(.04,1.15),(.04,1.67),(.36,1.67),(.9,1.15)],[(-.82,1.15),(-.78,1.67),(-.06,1.67),(-.06,1.15)]];tras=((-.98,1.05),(-.9,1.74))
        P.append(_cx(nome+'_capota',-2.52,-1.06,-.8,.8,1.02,1.085,M['preto'],.02))
        P.append(_cx(nome+'_santo',-1.12,-.98,-.84,.84,1.05,1.5,M['preto'],.03))
    else:
        cab=[(-2.6,1.05),(-2.42,1.72),(-1.2,1.8),(.38,1.77),(1.12,1.07)];jan=[[(.04,1.15),(.04,1.67),(.36,1.67),(.9,1.15)],[(-.82,1.15),(-.82,1.68),(-.06,1.67),(-.06,1.15)],[(-2.28,1.17),(-2.18,1.66),(-.92,1.68),(-.92,1.15)]];tras=((-2.6,1.05),(-2.42,1.72))
        for sg in (-1,1):P.append(_cx(nome+'_rack%d'%sg,-2.0,.0,sg*.62-.02,sg*.62+.02,1.8,1.84,M['preto'],.01))
    P.append(prisma(nome+'_cabine',cab,yc,pint,.09,5))
    for i,j in enumerate(jan):
        for sg in (-1,1):P.append(painel(nome+'_jan%d%d'%(i,sg),[(x,sg*(yc(z)+.012),z) for x,z in (j if sg>0 else j[::-1])],M['vidro']))
    def face(a,b,t0,t1,rec,nm):
        dx,dz=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dz);n=Vector((dz/l,0,-dx/l));n=n if (n.x>0)==(nm>0) else -n;pts=[]
        for t,s in ((t0,1),(t1,1),(t1,-1),(t0,-1)):
            x=a[0]+dx*t;z=a[1]+dz*t;pts.append(Vector((x,s*(yc(z)-rec),z))+n*.014)
        return painel(nome+'_vid%d'%nm,pts if nm>0 else pts[::-1],M['vidro'])
    P.append(face(cab[-1],cab[-2],.12,.92,.1,1));P.append(face(tras[0],tras[1],.3,.9,.12,-1))
    for k,ex in enumerate((EF,ET)):
        for sg in (-1,1):
            P.append(cil(nome+'_pneu%d%d'%(k,sg),RR,.27,ex,sg*.8,RR,M['pneu'],.07));P.append(cil(nome+'_aro%d%d'%(k,sg),RR*.62,.285,ex,sg*.8,RR,M['roda'],.02,20));P.append(cil(nome+'_cubo%d%d'%(k,sg),RR*.2,.3,ex,sg*.8,RR,M['preto'],0,12))
    P.append(_cx(nome+'_parachoque_f',2.56,2.74,-.93,.93,.38,.56,M['preto'],.05));P.append(_cx(nome+'_grade',2.62,2.7,-.52,.52,.6,.88,M['preto'],.02));P.append(_cx(nome+'_friso',2.66,2.71,-.5,.5,.86,.9,M['cromo'],.01))
    for sg in (-1,1):
        P.append(_cx(nome+'_farol%d'%sg,2.6,2.69,sg*.58,sg*.88,.72,.88,M['farol'],.02));P.append(_cx(nome+'_lant%d'%sg,-2.67,-2.6,sg*.7,sg*.9,.74,1.0,M['lanterna'],.02))
        P.append(_cx(nome+'_retro%d'%sg,.86,1.0,sg*.9,sg*1.06,1.16,1.3,M['preto'],.03));P.append(_cx(nome+'_soleira%d'%sg,-1.05,1.15,sg*.9,sg*.95,.36,.47,M['preto'],.02))
        for hx_ in (.1,-.75):P.append(_cx(nome+'_mac%d%d'%(sg,int(hx_*10)),hx_,hx_+.14,sg*.905,sg*.935,1.02,1.05,M['preto'],.008))
    P.append(_cx(nome+'_parachoque_t',-2.74,-2.58,-.93,.93,.4,.56,M['preto'],.05));P.append(_cx(nome+'_placa',-2.69,-2.66,-.2,.2,.62,.74,M['farol'],0))
    for o in P:
        sc.collection.objects.link(o);o.parent=raiz
    return raiz
CORES=['#e9e9e6','#2b2d30','#8f9498','#6d1f1c','#1f3550','#c9c5bb']
def trocar(sc,hexo,caixa_fn,CARRO):
    corpos=[o for o in sc.objects if hexo(o) in CARRO];cabs=[o for o in sc.objects if hexo(o)=='#2c3440'];rod=[o for o in sc.objects if hexo(o)=='#222222' and .2<o.dimensions.z<.5 and caixa_fn(o)[4]<.3]
    info=[]
    for o in corpos:
        x0,x1,y0,y1,z0,z1=caixa_fn(o);cx,cy=(x0+x1)/2,(y0+y1)/2;ao_x=(x1-x0)>(y1-y0);cb=min(cabs,key=lambda c:(c.matrix_world.translation.x-cx)**2+(c.matrix_world.translation.y-cy)**2)
        bx=caixa_fn(cb);d=((bx[0]+bx[1])/2-cx) if ao_x else ((bx[2]+bx[3])/2-cy);info.append((cx,cy,ao_x,d))
    for o in corpos+cabs+rod:bpy.data.objects.remove(o,do_unlink=True)
    for i,(cx,cy,ao_x,d) in enumerate(sorted(info)):
        r=carro(sc,'carro%d'%i,'picape' if i%2==0 else 'suv',CORES[i%len(CORES)]);r.location=(cx,cy,0);r.scale=(.92,.92,.92)
        ang=0 if ao_x else math.pi/2
        if d>.05:ang+=math.pi   # cabine deslocada para trás no modelo antigo: frente fica do outro lado
        r.rotation_euler=(0,0,ang);print('carro',i,round(cx,1),round(-cy,1),'eixo x' if ao_x else 'eixo z',round(d,2))
