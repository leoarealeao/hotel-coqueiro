import bpy,bmesh,sys,math,random,json,time
from mathutils import Vector
sys.path.insert(0,sys.argv[1]+'/bl');import cena
from cena import hx,novo,ruido,rampa,relevo,esc
S=sys.argv[1];Z=Vector((0,0,1))
def mat_folha():
    m=bpy.data.materials.new('folha_coqueiro');m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');b=nt.nodes.new('ShaderNodeBsdfPrincipled');b.inputs['Roughness'].default_value=.38
    n=ruido(nt,1.2,3,.6);r=rampa(nt,n.outputs['Fac'],hx('#35601f'),hx('#6c9a38'),.3,.75);nt.links.new(r.outputs[0],b.inputs['Base Color'])
    t=nt.nodes.new('ShaderNodeBsdfTranslucent');t.inputs[0].default_value=hx('#7fae3a');mx=nt.nodes.new('ShaderNodeMixShader');mx.inputs[0].default_value=.3;nt.links.new(b.outputs[0],mx.inputs[1]);nt.links.new(t.outputs[0],mx.inputs[2]);nt.links.new(mx.outputs[0],o.inputs[0]);return m
def mat_tronco():
    m=bpy.data.materials.new('tronco_coqueiro');m.use_nodes=True;nt,b=novo(m);b.inputs['Roughness'].default_value=.85
    tc=nt.nodes.new('ShaderNodeTexCoord');sp=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(tc.outputs['Object'],sp.inputs[0]);n=ruido(nt,3,3,.6)
    a=nt.nodes.new('ShaderNodeMath');a.operation='MULTIPLY';a.inputs[1].default_value=7;nt.links.new(sp.outputs['Z'],a.inputs[0]);ad=nt.nodes.new('ShaderNodeMath');ad.operation='ADD';nt.links.new(a.outputs[0],ad.inputs[0]);nt.links.new(n.outputs['Fac'],ad.inputs[1])
    fr=nt.nodes.new('ShaderNodeMath');fr.operation='FRACT';nt.links.new(ad.outputs[0],fr.inputs[0]);r=rampa(nt,fr.outputs[0],hx('#5d5142'),hx('#a39683'),.05,.6);nt.links.new(r.outputs[0],b.inputs['Base Color']);relevo(nt,b,fr.outputs[0],.8,.03);return m
def mat_coco():
    m=bpy.data.materials.new('coco');m.use_nodes=True;nt,b=novo(m);b.inputs['Base Color'].default_value=hx('#6f8a2e');b.inputs['Roughness'].default_value=.4;return m
def malha_coqueiro(nome,H,seed,MT,MF,MC):
    rd=random.Random(seed);bm=bmesh.new();inc=rd.uniform(.3,.9);az0=rd.uniform(0,6.28);hd=Vector((math.cos(az0),math.sin(az0),0))
    # tronco levemente inclinado, com base alargada
    aneis=[];NS=14
    for k in range(NS+1):
        t=k/NS;c=hd*(inc*t*t)+Z*(H*t);r=.19*(1-.4*t)+.09*math.exp(-9*t);aneis.append([bm.verts.new(c+Vector((math.cos(a)*r,math.sin(a)*r,0))) for a in [i*math.pi/5 for i in range(10)]])
    for k in range(NS):
        for i in range(10):
            f=bm.faces.new((aneis[k][i],aneis[k][(i+1)%10],aneis[k+1][(i+1)%10],aneis[k+1][i]));f.material_index=0;f.smooth=True
    C=hd*inc+Z*H
    def quad(a,b,c,d,mi=1):
        try:f=bm.faces.new([bm.verts.new(p) for p in (a,b,c,d)]);f.material_index=mi
        except ValueError:pass
    NF=26
    for i in range(NF):
        u=i/(NF-1);az=i*2.39996+rd.uniform(-.25,.25);e=math.radians(80-92*u**.9+rd.uniform(-6,6));L=(2.2+1.1*min(1,u*1.8))*rd.uniform(.88,1.08)*(H/6.5)**.3;dr=(.3+.3*u)*rd.uniform(.8,1.2)
        h=Vector((math.cos(az),math.sin(az),0));M=16;P=[C+h*(L*s*math.cos(e))+Z*(L*s*math.sin(e))-Z*(dr*L*s**2.3) for s in [j/M for j in range(M+1)]]
        def pt(s):
            x=s*M;j=min(M-1,int(x));return P[j].lerp(P[j+1],x-j),(P[j+1]-P[j]).normalized()
        for j in range(M):   # nervura central
            T=(P[j+1]-P[j]).normalized();sd=T.cross(Z);sd=sd.normalized() if sd.length>1e-4 else h.cross(Z);w0=.035*(1-j/M)+.008;w1=.035*(1-(j+1)/M)+.008;quad(P[j]-sd*w0,P[j]+sd*w0,P[j+1]+sd*w1,P[j+1]-sd*w1)
        NL=62
        for q in range(NL):
            s=.1+.9*q/(NL-1);p0,T=pt(s);sd=T.cross(Z);sd=sd.normalized() if sd.length>1e-4 else h.cross(Z);N=sd.cross(T).normalized()
            ll=(.95*math.sin(math.pi*(.06+.9*s))**.7+.12)*L/3.4
            for sg in (-1,1):
                d=(sd*sg*math.cos(.6)+T*math.sin(.6)).normalized();k=rd.uniform(.6,1.25);w=.065
                p1=p0+d*ll*.5+N*(.1*ll)-Z*(.06*ll*k);p2=p0+d*ll+N*(.02*ll)-Z*(.42*ll*k)
                quad(p0-T*w/2,p0+T*w/2,p1+T*w/2,p1-T*w/2);quad(p1-T*w/2,p1+T*w/2,p2+T*w*.12,p2-T*w*.12)
    me=bpy.data.meshes.new(nome);bm.to_mesh(me);bm.free()
    for mm in (MT,MF,MC):me.materials.append(mm)
    return me,C
def coqueiros(sc):
    MT,MF,MC=mat_tronco(),mat_folha(),mat_coco();troncos=[o for o in sc.objects if o.type=='MESH' and o.material_slots and o.material_slots[0].material and o.material_slots[0].material.get('hex')=='#8a6f4d']
    folhas=[o for o in sc.objects if o.type=='MESH' and o.material_slots and o.material_slots[0].material and o.material_slots[0].material.get('hex') in cena.FOLHA and o.location.z>3.5]
    print('troncos',len(troncos),'folhas removidas',len(folhas))
    base=[(o.location.x,o.location.y,o.dimensions.z) for o in troncos]
    for o in troncos+folhas:bpy.data.objects.remove(o,do_unlink=True)
    for i,(x,y,H) in enumerate(base):
        me,C=malha_coqueiro('coq%d'%i,H+1.2,100+i,MT,MF,MC);o=bpy.data.objects.new('coq%d'%i,me);sc.collection.objects.link(o);o.location=(x,y,0)
    # coqueiral de fundo: três variações instanciadas fora dos muros
    var=[malha_coqueiro('coqf%d'%k,h,900+k,MT,MF,MC)[0] for k,h in enumerate((7.5,9,10.5))];rd=random.Random(7);n=0
    while n<170:
        x=rd.uniform(-70,140);y=rd.uniform(-120,95)
        if -5<x<58 and -28<y<5:continue
        if -22<x<0 and -34<y<12:continue
        o=bpy.data.objects.new('cf%d'%n,var[n%3]);sc.collection.objects.link(o);o.location=(x,y,0);o.rotation_euler=(0,0,rd.uniform(0,6.28));sc_=rd.uniform(.8,1.2);o.scale=(sc_,sc_,sc_);n+=1
def mat_palha(m,borda=False):
    nt,b=novo(m);b.inputs['Roughness'].default_value=1
    tc=nt.nodes.new('ShaderNodeTexCoord');sp=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(tc.outputs['Object'],sp.inputs[0])
    fib=ruido(nt,1,6,.75,estica=(70,70,2.2));man=ruido(nt,.35,3,.5);ond=ruido(nt,2.5,2,.5)
    a=nt.nodes.new('ShaderNodeMath');a.operation='MULTIPLY';a.inputs[1].default_value=3.0;nt.links.new(sp.outputs['Z'],a.inputs[0])
    o2=nt.nodes.new('ShaderNodeMath');o2.operation='MULTIPLY';o2.inputs[1].default_value=.35;nt.links.new(ond.outputs['Fac'],o2.inputs[0])
    ad=nt.nodes.new('ShaderNodeMath');ad.operation='ADD';nt.links.new(a.outputs[0],ad.inputs[0]);nt.links.new(o2.outputs[0],ad.inputs[1])
    fr=nt.nodes.new('ShaderNodeMath');fr.operation='FRACT';nt.links.new(ad.outputs[0],fr.inputs[0])
    inv=nt.nodes.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;nt.links.new(fr.outputs[0],inv.inputs[1])   # espessura da fiada: maior embaixo
    cor=rampa(nt,fib.outputs['Fac'],hx('#6e5837'),hx('#cdb383'),.28,.72)
    sombra=rampa(nt,fr.outputs[0],(1,1,1,1),(.5,.46,.4,1),.82,.99)
    mancha=rampa(nt,man.outputs['Fac'],(.78,.76,.72,1),(1.12,1.1,1.05,1),.3,.7)
    m1=nt.nodes.new('ShaderNodeMixRGB');m1.blend_type='MULTIPLY';m1.inputs[0].default_value=0 if borda else 1;nt.links.new(cor.outputs[0],m1.inputs[1]);nt.links.new(sombra.outputs[0],m1.inputs[2])
    m2=nt.nodes.new('ShaderNodeMixRGB');m2.blend_type='MULTIPLY';m2.inputs[0].default_value=1;nt.links.new(m1.outputs[0],m2.inputs[1]);nt.links.new(mancha.outputs[0],m2.inputs[2]);nt.links.new(m2.outputs[0],b.inputs['Base Color'])
    hf=nt.nodes.new('ShaderNodeMath');hf.operation='MULTIPLY';hf.inputs[1].default_value=.25;nt.links.new(fib.outputs['Fac'],hf.inputs[0])
    ht=nt.nodes.new('ShaderNodeMath');ht.operation='ADD';nt.links.new(hf.outputs[0],ht.inputs[0])
    if borda:ht.inputs[1].default_value=0
    else:nt.links.new(inv.outputs[0],ht.inputs[1])
    relevo(nt,b,ht.outputs[0],1,.12 if not borda else .03)
def palha(sc):
    tel=[o for o in sc.objects if o.type=='MESH' and o.material_slots and o.material_slots[0].material and o.material_slots[0].material.get('img')=='Image_6']
    for m in {o.material_slots[0].material for o in tel}:mat_palha(m)
    MB=bpy.data.materials.new('palha_borda');MB.use_nodes=True;mat_palha(MB,True);rd=random.Random(3);bm=bmesh.new()
    def quad(a,b,c,d):bm.faces.new([bm.verts.new(p) for p in (a,b,c,d)])
    for o in tel:
        vs=[o.matrix_world@v.co for v in o.data.vertices];x0=min(v.x for v in vs);x1=max(v.x for v in vs);y0=min(v.y for v in vs);y1=max(v.y for v in vs);z0=min(v.z for v in vs)
        cant=[Vector((x0,y0,z0)),Vector((x1,y0,z0)),Vector((x1,y1,z0)),Vector((x0,y1,z0))];cen=Vector(((x0+x1)/2,(y0+y1)/2,z0))
        for k in range(4):
            A,B=cant[k],cant[(k+1)%4];T=(B-A).normalized();mid=(A+B)/2;Nf=Vector((T.y,-T.x,0))
            if (mid-cen).dot(Nf)<0:Nf=-Nf
            E=.2;quad(A,B,B-Z*E-Nf*.03,A-Z*E-Nf*.03)   # testeira de palha cortada, 20 cm
            quad(A-Z*E-Nf*.03,B-Z*E-Nf*.03,B-Z*E-Nf*.45,A-Z*E-Nf*.45)   # forro inclinado sob o beiral
            L=(B-A).length;n=int(L/.012)
            for i in range(n):
                p=A+T*(i*.012+rd.uniform(0,.008))+Nf*rd.uniform(-.02,.03)-Z*rd.uniform(0,.12);ln=rd.uniform(.1,.34);w=rd.uniform(.006,.016);d=(-Z+Nf*rd.uniform(-.12,.22)+T*rd.uniform(-.15,.15)).normalized()
                quad(p-T*w,p+T*w,p+d*ln+T*w*.4,p+d*ln-T*w*.4)
    me=bpy.data.meshes.new('franja');bm.to_mesh(me);bm.free();me.materials.append(MB);ob=bpy.data.objects.new('franja',me);sc.collection.objects.link(ob);print('franja faces',len(me.polygons))
def chao_fora():
    m=bpy.data.materials['areia_fora'];nt,b=novo(m);b.inputs['Roughness'].default_value=.95
    n=ruido(nt,.07,5,.6);r=rampa(nt,n.outputs['Fac'],hx('#5f7f33'),hx('#d8b074'),.44,.56);f=ruido(nt,3,5,.7);rf=rampa(nt,f.outputs['Fac'],(.8,.8,.8,1),(1.1,1.1,1.1,1))
    mm=nt.nodes.new('ShaderNodeMixRGB');mm.blend_type='MULTIPLY';mm.inputs[0].default_value=1;nt.links.new(r.outputs[0],mm.inputs[1]);nt.links.new(rf.outputs[0],mm.inputs[2]);nt.links.new(mm.outputs[0],b.inputs['Base Color']);relevo(nt,b,f.outputs['Fac'],.8,.08)
if __name__=='__main__':
    t=time.time();sc=cena.montar();coqueiros(sc);palha(sc);chao_fora();print('cena %.0fs'%(time.time()-t))
    cams=json.load(open(S+'/uni/cams.json'));am=int(sys.argv[3]) if len(sys.argv)>3 else 96;res=(1280,720) if len(sys.argv)<5 else (1920,1080)
    for n in [int(x) for x in sys.argv[2].split(',')]:
        nome,p,a,f=cams[n-1];cena.foto(sc,p,a,f,S+'/bl/out2/%02d_%s.png'%(n,nome),am,res)
