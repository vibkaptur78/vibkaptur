# Tema 1 paso 2: quita de la plataforma las medidas que no fueron reales (aprobado por Pedro 20/11/2026).
# Uso: python3 fix_t1.py [--dry]
import json,os,sys,time,shutil,re,unicodedata
DATA='/var/www/vibkaptur/private/data'; BAK='/var/www/vibkaptur/private/backups'
FIX=json.loads(r'''{"otua|reydesa": {"Fragmentadora 1": {"q": ["ago-26"]}, "Fragmentadora 5": {"q": ["jun-26", "ago-26", "nov-26"]}, "Ventilador Aspiraci\u00f3n Fragmentadora 1 (Aux)": {"q": ["ago-26", "nov-26"]}, "Ventilador Aspiraci\u00f3n Fragmentadora 5": {"q": ["jun-26", "ago-26", "sep-26", "oct-26", "nov-26"]}, "Ventilador Aspiraci\u00f3n F": {"q": ["jun-26", "jul-26", "ago-26", "sep-26", "oct-26", "nov-26"], "ult": "may-26"}, "Eriez Gruesos": {"q": ["jun-26", "oct-26"]}, "Molino 3": {"q": ["jul-26", "ago-26", "sep-26"]}, "Molino 4": {"q": ["jun-26", "oct-26", "nov-26"]}, "Ventilador Aspiraci\u00f3n Molino 3": {"q": ["sep-26"]}, "Ventilador Aspiraci\u00f3n Molino 4": {"q": ["jun-26", "oct-26"]}, "Aspaleck": {"q": ["jun-26", "oct-26", "nov-26"]}}, "otua|refial": {"Horno 1": {"q": ["jul-26"]}, "Ventilador Aspiraci\u00f3n Grande": {"q": ["sep-26"]}, "Ventilador Aspiraci\u00f3n Peque\u00f1a": {"q": ["ago-26", "oct-26"]}, "Ventilador Cal Aditivos Aspiraci\u00f3n Peque\u00f1a": {"q": ["ago-26", "oct-26"]}, "Accionamiento Horno 1": {"q": ["jun-26", "jul-26", "nov-26"]}, "Vent Ran Horno 2": {"q": ["ago-26"]}, "Accionamiento Motoreductor Placas": {"q": ["jul-26"]}}, "otua|resal": {"Ventilador Aspiraci\u00f3n": {"q": ["ago-26"]}, "Criba": {"q": ["ago-26"]}, "Bomba Tanque Agua Maderas P104": {"q": ["ago-26", "oct-26", "nov-26"]}, "Bomba Condensado Vapor P105": {"q": ["ago-26", "oct-26"]}, "Bomba 106 Condensados Proceso": {"q": ["ago-26", "oct-26"]}, "Bomba 107 Condensados Precalentador": {"q": ["ago-26", "oct-26"]}, "Bomba 108 Condensados A Tc": {"q": ["ago-26", "oct-26"]}, "Bomba Alimentaci\u00f3n P110": {"q": ["ago-26", "oct-26"]}, "Bomba P-112 Foso": {"q": ["ago-26", "oct-26"]}, "Bomba Ph-01 Slurry": {"q": ["ago-26", "oct-26"]}}, "weylchem|-": {"Bba Acido Sulfurico B 230P1B": {"q": ["jun-26", "jul-26", "ago-26", "nov-26"]}, "Bba Agua Demi Circuito Cerrado A 514P1A": {"q": ["jun-26", "jul-26", "ago-26"]}, "Bba Agua Demi Circuito Cerrado B 514P3B": {"q": ["jun-26", "jul-26"]}, "Bba Alim De Agua A Cald A 514P2A": {"q": ["jun-26", "jul-26"]}, "Bba Carga Oleum A 230P2A": {"q": ["jun-26", "nov-26"]}, "Bba Condensado A 535P1Am": {"q": ["jun-26", "jul-26", "ago-26", "sep-26", "nov-26"]}, "Bba Refrigeracion B 370P1B": {"q": ["jun-26", "jul-26", "ago-26", "sep-26", "nov-26"]}, "Vent Torre Ref B 370Ctbm": {"q": ["sep-26"]}, "Bomba Acido Sulfurico A": {"q": ["sep-26", "oct-26"]}, "Bomba Agua Demi Circuito Cerrado A 514P3A": {"q": ["jun-26", "jul-26", "ago-26", "sep-26", "oct-26", "nov-26"], "ult": "oct-24"}, "Bomba Agua Demi Circuito Cerrado B 514P1B": {"q": ["sep-26", "oct-26", "nov-26"]}, "Bomba Alimentacion De Agua A Caldera B 514P2B": {"q": ["ago-26", "sep-26", "oct-26", "nov-26"]}, "Bomba Alimentacion Emergencia De Agua A Caldera C 514P2C": {"q": ["jun-26", "jul-26", "ago-26", "sep-26", "oct-26", "nov-26"], "ult": "ago-24"}, "Bomba Carga De Oleum B 230P2B": {"q": ["jun-26", "jul-26", "ago-26", "sep-26", "oct-26", "nov-26"], "ult": "nov-25"}, "Bomba De Precapa 503P2A": {"q": ["jun-26", "jul-26", "ago-26", "sep-26", "oct-26", "nov-26"], "ult": "dic-24"}, "Bomba Condensado B": {"q": ["oct-26"]}, "Bomba De Refrigeracion A": {"q": ["oct-26"]}, "Tanque Precapa 503Mx3": {"q": ["jun-26", "jul-26", "ago-26", "sep-26", "oct-26", "nov-26"], "ult": "dic-24"}}, "teraplast|-": {"Bomba Principal 1": {"q": ["ene-26", "mar-26", "jul-26", "sep-26"]}, "Bomba Principal 2": {"q": ["nov-25"]}, "Desmenuzadora Nueva": {"q": ["nov-25", "ene-26", "mar-26", "jul-26", "sep-26"], "ult": "ago-24"}, "Molino 2": {"q": ["nov-25", "ene-26", "mar-26", "jul-26", "sep-26"], "ult": "ago-24"}, "Extrusora 12": {"q": ["jul-26"]}, "Extrusora 14": {"q": ["nov-25", "ene-26", "mar-26", "jul-26"]}, "Extrusora 15": {"q": ["mar-26", "sep-26"]}, "Extrusora 5": {"q": ["nov-25", "sep-26"]}, "Extrusora 6": {"q": ["ene-26", "jul-26", "sep-26"]}, "Extrusora Zona Molino": {"q": ["mar-26"]}}, "edisonnext|-": {"Bomba P022": {"q": ["sep-25", "dic-25", "ago-26"]}, "Bomba P047": {"q": ["dic-25", "ago-26"]}, "Grupo 2": {"q": ["mar-25"]}}, "tecnoaranda|-": {"Accionamiento Inferior Rod-002 R60": {"q": ["ago-26"]}, "Accionamiento Inferior Rod-002 R75": {"q": ["ago-26"], "ult": "ago-22"}, "Accionamiento Inferior Rod-002 R90": {"q": ["ago-25"]}, "Accionamiento Rod-001 R60": {"q": ["ago-26"]}, "Accionamiento Superior R90": {"q": ["ago-25"]}}}''')
dry='--dry' in sys.argv
MES=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
def ym(l):
    m=re.match(r'^([a-z]{3})-(\d{2})$',str(l or '').strip().lower())
    return (2000+int(m.group(2)),MES.index(m.group(1))+1) if m and m.group(1) in MES else (0,0)
def an(s): return re.sub(r'[^A-Z0-9]','',''.join(c for c in unicodedata.normalize('NFD',str(s or '').upper()) if unicodedata.category(c)!='Mn'))
tot=0; tm=0; ts=time.strftime('%Y%m%d%H%M%S')
bycid={}
for k,v in FIX.items(): bycid.setdefault(k.split('|')[0],[]).append((k.split('|')[1],v))
for cid,pls in sorted(bycid.items()):
    fp=os.path.join(DATA,cid+'.json')
    if not os.path.exists(fp): print('NO EXISTE',fp); continue
    d=json.load(open(fp,encoding='utf-8')); ch=0
    for pl,fx in pls:
        P=[p for p in d.get('plants',[]) if pl=='-' or p.get('id')==pl]
        if not P: print('  planta no encontrada',cid,pl); continue
        P=P[0]; ms={}
        for a in P.get('areas',[]):
            for m in a.get('machines',[]):
                if 'tmax' in m or m.get('placeholder'): continue
                ms[an(m.get('name'))]=m
        for name,e in fx.items():
            m=ms.get(an(name))
            if m is None: print('  no encontrada: %s / %s'%(cid,name)); continue
            Q=set(e['q']); tr=m.get('trend') or []
            had=[t.get('l') for t in tr if t.get('l') in Q]
            if not had: continue
            lastwas=max((t.get('l') for t in tr),key=ym) in Q
            m['trend']=[t for t in tr if t.get('l') not in Q]
            if m.get('evo'): m['evo']=[t for t in m['evo'] if t.get('q') not in Q]
            if m.get('edates'): m['edates']=[x for x in m['edates'] if x not in Q]
            for c in m.get('comps',[]) or []:
                s=c.get('series') or []
                if not s: continue
                lastg=s[-1].get('g')
                c['series']=[x for x in s if x.get('d') not in Q]
                if not c['series'] and e.get('ult'): c['series']=[{'d':e['ult'],'g':lastg}]
            if not m['trend'] and e.get('ult') and m.get('grade') is not None:
                m['trend']=[{'l':e['ult'],'g':m['grade']}]; m['evo']=[{'q':e['ult'],'g':m['grade']}]; m['edates']=[e['ult']]
            if lastwas:
                m['nomedido']=True; m['state']='nomedido'; m['hasValues']=False
            m.pop('okSinFicha',None)
            ch+=len(had); tm+=1
            print('  %s/%s · %s: quitados %s -> ultima real %s%s'%(cid,pl,m.get('name'),','.join(had),(m['trend'][-1]['l'] if m['trend'] else '-'),' (gris)' if lastwas else ''))
    tot+=ch
    if ch and not dry:
        os.makedirs(BAK,exist_ok=True); shutil.copy2(fp,os.path.join(BAK,'%s.%s.t1.bak'%(cid,ts)))
        tmp=fp+'.tmp'; st=os.stat(fp)
        json.dump(d,open(tmp,'w',encoding='utf-8'),ensure_ascii=False)
        os.chmod(tmp,st.st_mode&0o7777)
        try: os.chown(tmp,st.st_uid,st.st_gid)
        except Exception: pass
        os.replace(tmp,fp)
print(('ENSAYO (no se ha guardado nada): ' if dry else 'T1 PASO 2 APLICADO: ')+'%d maquinas, %d puntos'%(tm,tot))
