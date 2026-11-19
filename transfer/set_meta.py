# Pone en los datos de cada cliente la fecha real de medida, tecnico y aprobado (sacados del ultimo PDF).
import json,os,sys,shutil,datetime
M=json.load(open(sys.argv[1],encoding='utf-8')); D='/var/www/vibkaptur/private/data'; B='/var/www/vibkaptur/private/backups'
os.makedirs(B,exist_ok=True); n=0
for cid,plants in M.items():
    f=os.path.join(D,cid+'.json')
    if not os.path.isfile(f): print(cid,'sin datos'); continue
    d=json.load(open(f,encoding='utf-8')); ch=0
    for p in d.get('plants',[]):
        m=plants.get(p.get('id'))
        if not m: continue
        for k,v in m.items():
            if p.get(k)!=v: p[k]=v; ch+=1
    if ch:
        shutil.copy2(f,os.path.join(B,'%s.%s.bak'%(cid,datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))))
        txt=json.dumps(d,ensure_ascii=False); json.loads(txt)
        open(f,'w',encoding='utf-8').write(txt); n+=1
    print(cid,'actualizado' if ch else 'sin cambios')
print('CLIENTES ACTUALIZADOS:',n)
