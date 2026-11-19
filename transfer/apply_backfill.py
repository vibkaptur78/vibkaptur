# Completa el historico (hasta 5 mediciones) con puntos de informes anteriores. Uso: apply_backfill.py parche.json [--dry]
import json,sys,os,shutil,datetime
MES=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
def ym(l):
    try: a,b=str(l).split('-'); return (2000+int(b))*12+MES.index(a)
    except Exception: return None
D='/var/www/vibkaptur/private/data'; B='/var/www/vibkaptur/private/backups'
patch=json.load(open(sys.argv[1],encoding='utf-8')); dry='--dry' in sys.argv
tm=tp=0
for cid,plants in patch.items():
    p=os.path.join(D,cid+'.json')
    if not os.path.isfile(p): print(cid,'sin datos en servidor'); continue
    data=json.load(open(p,encoding='utf-8')); nm=np=0
    for pid,add in plants.items():
        P=[x for x in data.get('plants',[]) if x.get('id')==pid]
        if not P: continue
        byid={m.get('id'):m for a in P[0].get('areas',[]) for m in a.get('machines',[])}
        for mid,v in add.items():
            m=byid.get(mid)
            if m is None or 'tmax' in m: continue
            tr=m.setdefault('trend',[]); have=[ym(t.get('l')) for t in tr]; have=[h for h in have if h is not None]
            if not have: continue
            first=min(have); did=0
            for pt in v['pts']:
                k=ym(pt['l'])
                if k is None or k>=first or k in have: continue
                tr.append({'l':pt['l'],'g':pt['g']}); m.setdefault('evo',[]).append({'q':pt['l'],'g':pt['g']})
                m.setdefault('edates',[]).append(pt['l'])
                if m.get('rms') and pt.get('rms') is not None: m['rms'].append({'l':pt['l'],'v':pt['rms']})
                cp={str(a).strip().lower():b for a,b in (pt.get('comps') or {}).items()}
                cl=list((pt.get('comps') or {}).values()); mc=m.get('comps',[])
                for ci,c in enumerate(mc):
                    g=cp.get(str(c.get('name')).strip().lower())
                    if g is None and len(cl)==len(mc): g=cl[ci]   # mismo numero de componentes: por orden
                    if g is None and len(cl)==1: g=cl[0]
                    if g is None: g=pt['g'] if len(mc)==1 else None
                    if g is not None: c.setdefault('series',[]).append({'d':pt['l'],'g':g})
                have.append(k); did+=1
            if did:
                tr.sort(key=lambda t:ym(t.get('l')) or 0); m['evo'].sort(key=lambda t:ym(t.get('q')) or 0)
                m['edates']=sorted(set(m['edates']),key=lambda l:ym(l) or 0)[-12:]
                if m.get('rms'): m['rms'].sort(key=lambda t:ym(t.get('l')) or 0)
                for c in m.get('comps',[]):
                    if c.get('series'): c['series'].sort(key=lambda t:ym(t.get('d')) or 0)
                nm+=1; np+=did
    if nm and not dry:
        os.makedirs(B,exist_ok=True)
        shutil.copy2(p,os.path.join(B,'%s.%s.bak'%(cid,datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))))
        st=os.stat(p); tmp=p+'.tmp'
        open(tmp,'w',encoding='utf-8').write(json.dumps(data,ensure_ascii=False))
        os.chmod(tmp,st.st_mode); os.chown(tmp,st.st_uid,st.st_gid); os.replace(tmp,p)
    print('%-14s maquinas completadas: %3d   mediciones anadidas: %3d'%(cid,nm,np)); tm+=nm; tp+=np
print('TOTAL: %d maquinas, %d mediciones%s'%(tm,tp,' (ENSAYO, no se ha guardado nada)' if dry else ''))
