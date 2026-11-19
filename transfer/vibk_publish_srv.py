#!/usr/bin/env python3
# VIBKAPTUR - Actualiza los datos de un cliente al PUBLICAR un informe.
# Lee las fichas subidas (.xls/.xlsx/.xlsm) y el PDF, y actualiza el JSON del cliente
# (estado, grado, fenomenos, comentarios, tendencias, RMS, no medidos, OK sin ficha).
# Uso: vibk_publish_srv.py <cid> <carpeta_fichas> <pdf> <datos.json> [planta] [--dry]
import xlrd, openpyxl, glob, os, re, json, sys, subprocess, shutil, datetime as _dt

SECT={'ESPECTROS','HISTORIAL','DATOS','CONDICIONES','TIPOLOGÍA','ERGOMETRÍA','COMENTARIOS','PUNTOS','ÁREA','MOTOR Y BOMBA','ANÁLISIS','ESPECTRO'}
MESES=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
def norm(s): return re.sub(r'\s+',' ',str(s if s is not None else '')).strip().upper()
import unicodedata
def _noacc(t): return ''.join(ch for ch in unicodedata.normalize('NFD',t) if unicodedata.category(ch)!='Mn')
def alnum(s): return re.sub(r'[^A-Z0-9]','',_noacc(norm(s)))
_ABR={'BBA':'BOMBA','BBAS':'BOMBA','VENT':'VENTILADOR','SOP':'SOPLANTE','MOT':'MOTOR','ALIM':'ALIMENTACION','REF':'REFRIGERACION','CALD':'CALDERA','EMERG':'EMERGENCIA','LIQ':'LIQUIDO','MOTORED':'MOTOREDUCTOR','W':''}
_STOPW={'DE','DEL','LA','EL','AL','LOS','LAS','Y'}
def toks(s):
    out=set()
    for t in re.split(r'[^A-Z0-9]+',_noacc(norm(s))):
        if not t or t in _STOPW: continue
        if re.search(r'\d',t) and re.search(r'[A-Z]',t) and len(t)>=4: continue   # codigo/TAG
        t=_ABR.get(t,t)
        if t: out.add(t)
    return frozenset(out)
def isnum(v):
    try: return float(v)
    except: return None
def titlecase(s):
    s=re.sub(r'\s+',' ',str(s)).strip()
    return s.title() if s else s
def st(g): return 'bueno' if g<=2 else 'seg' if g<=4 else 'alerta' if g<=6 else 'peligro'

def parse_grid(cell,nrows,ncols):
    grade=None
    for r in range(0,min(5,nrows)):
        for c in range(ncols):
            m=re.search(r'GRADO\s*(\d+)',str(cell(r,c)),re.I)
            if m: grade=int(m.group(1)); break
        if grade is not None: break
    name=None;area='GENERAL';area_row=None
    for r in range(2,min(6,nrows)):
        for c in range(ncols):
            if norm(cell(r,c))=='ÁREA':
                area_row=r
                a=str(cell(r,c+2) if c+2<ncols else '').strip()
                if a and a!='None': area=a
            if norm(cell(r,c))=='MAQUINA':
                for cc in range(c+1,ncols):
                    v=str(cell(r,cc)).strip()
                    if v and v!='None' and norm(v)!='MAQUINA': name=v; break
    if name is None and area_row is not None:
        for cc in range(ncols-1,2,-1):
            v=str(cell(area_row,cc)).strip()
            if v and v!='None' and norm(v) not in ('MAQUINA',norm(area),'PUNTOS'): name=v; break
    rmscol=ptcol=None
    for r in range(0,min(8,nrows)):
        for c in range(ncols):
            t=str(cell(r,c)).lower().replace('seg','/s')
            if 'mm/s' in t: rmscol=c
            if norm(cell(r,c))=='PUNTOS': ptcol=c
    if rmscol is None: rmscol=5
    if ptcol is None: ptcol=max(0,rmscol-1)
    cv=[r for r in range(nrows) if norm(cell(r,1)).startswith('CAUSA')]
    comps=[]
    for idx,hr in enumerate(cv):
        cname=norm(cell(hr-1,0))
        if cname in ('Ü','','NONE'): cname='COMP%d'%(idx+1)
        phen=[]; end=cv[idx+1]-1 if idx+1<len(cv) else nrows
        for r in range(hr+1,end):
            f=cell(r,1); g=isnum(cell(r,3)); fn=norm(f)
            if fn and fn not in SECT and g is not None and str(f).strip()[0].isalpha():
                phen.append((str(f).strip().title(),int(g)))
        if phen:
            mx=max(p[1] for p in phen); drv=[p[0] for p in phen if p[1]==mx][0]
            comps.append({'name':cname.title(),'phen':phen,'maxgrade':mx,'driver':drv})
    pts=[]
    for r in range(nrows):
        pn=str(cell(r,ptcol)).strip(); v=isnum(cell(r,rmscol))
        if pn and pn[0:1].isdigit() and v is not None and 0<v<2000: pts.append((pn,round(v,2)))
    maxrms=max((v for _,v in pts),default=None); focus=([p for p,v in pts if v==maxrms]+[None])[0] if pts else None
    phenset=set()
    for c in comps:
        for p,g in c['phen']: phenset.add(norm(p))
    STAT=('SATISFACTOR','ADMISIBLE','ACEPTABLE','INSATISFACTOR','INADMISIBLE','ALARMA','ALERTA','PELIGRO','TOLERABLE','EFECTO','CORRECTO','VIGILANC','SEGUIMIENTO','BUENO','GRAVE','SIGNIFICAT','MENOR','LEVE','NORMAL')
    RECW=('REQUIERE','INTERVEN','REVIS','SUSTITU','CAMBIAR','EQUILIBR','ALINE','CORREG','VIGIL','PROGRAM','PLANIFIC','APRIET','ENGRAS','LUBRIC','PARAR','MANTENER','CONTINU','ACTUAC','RECOMIEND','SEGUIR','NO REQUIERE')
    def _cls(t):
        u=norm(t); return (any(w in u for w in RECW), any(w in u for w in STAT))
    summ={}
    for r in range(nrows):
        a=cell(r,0); na=norm(a)
        if not (na and na in phenset): continue
        texts=[]
        for c in range(1,ncols):
            raw=cell(r,c); t=str(raw).strip()
            if t and t.lower()!='none' and isnum(raw) is None and len(t)>2: texts.append(t)
        if not texts: continue
        est=''; rec=''
        for t in texts:
            isr,iss=_cls(t)
            if isr and not rec: rec=t
            elif iss and not est: est=t
        if not rec and not est:
            est=texts[0]; rec=texts[1] if len(texts)>1 else ''
        elif rec and not est:
            for t in texts:
                if t!=rec: est=t; break
        elif est and not rec:
            for t in texts:
                if t!=est: rec=t; break
        if na not in summ: summ[na]={'estado':est,'rec':rec}
    note=[]
    for r in range(nrows):
        lbl=norm(cell(r,0))
        if lbl.startswith('COMENTARIO') or lbl.startswith('DETALLE') or lbl.startswith('OBSERVAC'):
            for c in range(1,ncols):
                raw=cell(r,c); t=str(raw).strip()
                if t and t.lower()!='none' and isnum(raw) is None and len(t)>8: note.append(t)
    mg=max([c['maxgrade'] for c in comps],default=None)
    if grade is not None: mg=max(mg or 0,grade)
    allph=[(p,g,c['name']) for c in comps for p,g in c['phen']]
    rec=''
    if allph:
        top=max(allph,key=lambda x:x[1]); rec=summ.get(norm(top[0]),{}).get('rec','')
    fens=[{'f':p,'grado':g,'comp':c['name'],'estado':summ.get(norm(p),{}).get('estado',''),'rec':summ.get(norm(p),{}).get('rec','')} for c in comps for p,g in c['phen']]
    return {'name':name,'area':area,'grade':mg,'comps':comps,'fens':fens,'pts':pts,'maxrms':maxrms,'focus':focus,'rec':rec,'note':note}

def _dates_from(vals):
    best=None
    for v in vals:
        y=mn=dd=None
        if isinstance(v,_dt.datetime): y,mn,dd=v.year,v.month,v.day
        elif isinstance(v,str):
            m=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',v)
            if m:
                dd=int(m.group(1)); mn=int(m.group(2)); y=int(m.group(3)); y=y+2000 if y<100 else y
        if y and mn and 1<=mn<=12 and 2015<=y<=2100 and dd and 1<=dd<=31:
            k=(y,mn,dd)
            if best is None or k>best: best=k
    return best

def read_fichas(folder):
    """Devuelve lista de dicts: {file, info, my}. Una entrada por ficha (o por hoja en .xlsm)."""
    out=[]
    for f in sorted(glob.glob(os.path.join(folder,'*.xls*'))):
        if 'plantilla' in f.lower() or 'conflict' in f.lower() or os.path.basename(f).startswith('~'): continue
        base=os.path.splitext(os.path.basename(f))[0]
        try:
            if f.lower().endswith(('.xlsm','.xlsx')):
                wb=openpyxl.load_workbook(f,data_only=True,read_only=True)
                for sh in wb.sheetnames:
                    if sh in ('RESUMEN','EXTRA'): continue
                    grid=[[c.value for c in row] for row in wb[sh].iter_rows()]
                    nr=len(grid); nc=max((len(r) for r in grid),default=0)
                    def cell(r,c,grid=grid): return grid[r][c] if (r<len(grid) and c<len(grid[r])) else ''
                    info=parse_grid(cell,nr,nc)
                    if not info['comps']: continue
                    vals=[v for row in grid for v in row if v is not None]
                    multi=len(wb.sheetnames)>1
                    _d=_dates_from(vals); out.append({'file':(sh if multi else base),'info':info,'my':(_d[:2] if _d else None),'date':_d})
                wb.close()
            else:
                bk=xlrd.open_workbook(f); sh=bk.sheet_by_index(0)
                info=parse_grid(lambda r,c: sh.cell_value(r,c) if c<sh.ncols else '', sh.nrows, sh.ncols)
                if not info['comps']: continue
                vals=[]
                for r in range(sh.nrows):
                    for c in range(sh.ncols):
                        cl=sh.cell(r,c)
                        if cl.ctype==3:
                            try: vals.append(_dt.datetime(*xlrd.xldate_as_tuple(cl.value,bk.datemode)))
                            except Exception: pass
                        elif cl.value not in (None,''): vals.append(cl.value)
                _d=_dates_from(vals); out.append({'file':base,'info':info,'my':(_d[:2] if _d else None),'date':_d})
        except Exception:
            pass
    return out

CODE=re.compile(r'(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{4,}')
AREAS={'BOMBAS','VENTILADORES','MOTORES','GENERAL','MOLIENDA','EXTRUSORA','SOPLANTES','COMPRESORES','MOTOREDUCTORES','TURBINAS','REDUCTORAS','BOMBA','VENTILADOR','PRENSA','SECADO','MEZCLADOR','CALEFACCION','VAPORIZACION','MAQUINA','TAG','AREA','ÁREA','RECOMENDACION','RECOMENDACIÓN','GRADO','RMS','ZONA'}
def pdf_info(pdf):
    try:
        info=subprocess.run(['pdfinfo',pdf],capture_output=True,text=True).stdout
        npag=int(re.search(r'Pages:\s+(\d+)',info).group(1))
    except Exception: npag=30
    txt=subprocess.run(['pdftotext','-f','1','-l',str(min(npag,40)),'-layout',pdf,'-'],capture_output=True,text=True).stdout
    nomed=[]
    for ln in txt.splitlines():
        U=ln.upper()
        if 'NO MEDIDO' not in U: continue
        pre=U.split('NO MEDIDO')[0]
        codes=CODE.findall(pre); code=codes[-1] if codes else ''
        toks=pre.split()
        while toks and toks[0] in AREAS: toks=toks[1:]
        nm=' '.join(toks).strip()
        if len(alnum(nm))>=4 or code: nomed.append((code,nm))
    meta={}
    U=_noacc(txt.upper())
    MES=['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
    cov=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',U)
    cy=cm=None
    if cov:
        cy=int(cov.group(3)); cy=cy+2000 if cy<100 else cy; cm=int(cov.group(2))
        meta['fecha_informe']='%02d/%02d/%04d'%(int(cov.group(1)),cm,cy)
    dm=re.search(r'\bDIAS?\s+(\d{1,2})(?:\s*(?:,|Y|AL|-)\s*\d{1,2})*\s+DE\s+('+'|'.join(MES)+r')(?:\s+DE\s+(\d{4}))?',U)
    if dm:
        d=int(dm.group(1)); mo=MES.index(dm.group(2))+1
        y=int(dm.group(3)) if dm.group(3) else (cy or _dt.date.today().year)
        if not dm.group(3) and cm and mo>cm: y-=1
        if 1<=d<=31: meta['medicion']='%02d/%02d/%04d'%(d,mo,y)
    rz=re.search(r'REALIZADO:\s*(.+?)\s+APROBADO:\s*([^\n]+)',txt,re.I)
    if rz:
        meta['tecnico']=titlecase(rz.group(1)); meta['aprobado']=titlecase(rz.group(2))
    return alnum(txt), nomed, set(t for t in re.split(r'[^A-Z0-9]+',_noacc(norm(txt))) if t), meta

def upsert(lst,keyname,label,item):
    if lst and lst[-1].get(keyname)==label: lst[-1]=item
    else: lst.append(item)
    del lst[:-12]

def codes_of(s): return set(CODE.findall(norm(s)))

_GEN={'PLANTA','FOODS','FOOD','NEXT','CHEMICAL','SISTEMAS','INFORME','GRUPO','INDUSTRIAL'}
def _ntoks(n): return [t for t in re.split(r'[^A-Z0-9]+',_noacc(norm(n))) if len(t)>=3 and t not in _GEN]
def pdf_owner(pdfwords,data,cid,datapath,P):
    """El PDF nombra a este cliente/planta? Nombra en cambio a otro? Solo por palabras completas del texto del PDF."""
    if not pdfwords: return None,''
    own=set(_ntoks(data.get('name'))+_ntoks(cid)); multi=len(data.get('plants') or [])>1
    ownp=set(_ntoks(P.get('name'))+_ntoks(P.get('id'))) if multi else set()
    own_ok=bool((own|ownp)&pdfwords) if (own or ownp) else None
    otro=''
    if multi and not (ownp&pdfwords):
        for q in data.get('plants') or []:
            if q is P: continue
            t=set(_ntoks(q.get('name'))+_ntoks(q.get('id')))-ownp
            if t and t<=pdfwords: otro=str(q.get('name')); break
    if not otro and not own_ok:
        try:
            for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(datapath)),'*.json'))):
                oc=os.path.splitext(os.path.basename(f))[0]
                if oc==cid: continue
                try: on=json.load(open(f,encoding='utf-8')).get('name') or oc
                except Exception: on=oc
                t=set(_ntoks(on))
                if t and t<=pdfwords: otro=str(on); break
        except Exception: pass
    return own_ok,otro
def main():
    tecnico=''
    for a in sys.argv[1:]:
        if a.startswith('--tecnico='): tecnico=a.split('=',1)[1].strip()
    args=[a for a in sys.argv[1:] if a not in ('--dry','--strict') and not a.startswith('--tecnico=')]; dry='--dry' in sys.argv; strict='--strict' in sys.argv
    if len(args)<4:
        print(json.dumps({'ok':False,'e':'uso'})); return
    cid,folder,pdf,datapath=args[0],args[1],args[2],args[3]
    plant=args[4].strip() if len(args)>4 else ''
    try: data=json.load(open(datapath,encoding='utf-8'))
    except Exception as e:
        print(json.dumps({'ok':False,'e':'nodatos','d':str(e)})); return
    plants=data.get('plants') or []
    if not plants: print(json.dumps({'ok':False,'e':'sinplantas'})); return
    P=None
    if len(plants)==1: P=plants[0]
    else:
        for p in plants:
            if plant and (norm(p.get('id'))==norm(plant) or norm(p.get('name'))==norm(plant)): P=p
        if P is None:
            print(json.dumps({'ok':False,'e':'planta','plantas':[p.get('id') for p in plants]},ensure_ascii=False)); return
    fichas=read_fichas(folder)
    mys=[f['my'] for f in fichas if f['my']]
    if fichas and not mys and os.path.isfile(pdf):
        # libro unico sin fechas por ficha (formato nuevo .xlsm): el periodo lo da el dia de medicion del PDF
        _pm=pdf_info(pdf)[3]; _fm=_pm.get('medicion') or _pm.get('fecha_informe')
        if _fm:
            _dd,_mm,_yy=[int(x) for x in _fm.split('/')]
            for f in fichas: f['my']=(_yy,_mm); f['date']=(_yy,_mm,_dd)
            mys=[(_yy,_mm)]
    if not fichas or not mys:
        r0={'ok':False,'e':'sinfichas','n':len(fichas)}
        if os.path.isfile(pdf):
            try:
                _o,_x=pdf_owner(pdf_info(pdf)[2],data,cid,datapath,P); r0['pdf_cliente']=_o; r0['pdf_otro']=_x
            except Exception: pass
        print(json.dumps(r0,ensure_ascii=False)); return
    period=max(mys); label='%s-%02d'%(MESES[period[1]-1],period[0]%100)
    current=[f for f in fichas if f['my']==period]
    pdftxt,nomed,pdfwords,pmeta=pdf_info(pdf) if os.path.isfile(pdf) else ('',[],set(),{})
    nm_codes={c for c,_ in nomed if c}; nm_names={alnum(n) for _,n in nomed if len(alnum(n))>=6}; nm_toks={toks(n) for _,n in nomed if len(toks(n))>=2}

    machines=[(a,m) for a in P.get('areas',[]) for m in a.get('machines',[]) if 'tmax' not in m]
    byname={}
    for a,m in machines: byname.setdefault(alnum(m.get('name')),[]).append((a,m))
    used=set(); upd=[]; added=[]
    def _keys(f):
        ks=[]
        for k in (alnum(f['info'].get('name')),alnum(f['file'])):
            if not k: continue
            ks.append(k)
            k2=re.sub(r'^\d{1,2}(?=[A-Z])','',k)   # numero de orden delante: 2_ASTILLADORA
            if k2!=k and len(k2)>=5: ks.append(k2)
        return ks
    def find(f):
        info=f['info']
        for k in _keys(f):
            cand=[(a,m) for a,m in byname.get(k,[]) if id(m) not in used]
            if len(cand)==1: return cand[0][1]
            if len(cand)>1:
                # varias maquinas con el mismo nombre en areas distintas: decidir por el area
                fa=alnum(info.get('area')); fd=set(re.findall(r'\d+',alnum(f['file'])+' '+alnum(info.get('area'))))
                for a,m in cand:
                    if fa and a is not None and alnum(a.get('name'))==fa: return m
                hit=[m for a,m in cand if a is not None and (set(re.findall(r'\d+',alnum(a.get('name')))) & fd)]
                if len(hit)==1: return hit[0]
                return cand[0][1]
        cs=codes_of(f['file']+' '+(info.get('name') or ''))
        if cs:
            hit=[m for a,m in machines if id(m) not in used and (codes_of(m.get('name')) & cs)]
            if len(hit)==1: return hit[0]
        # emparejado aproximado: pequenas diferencias de escritura (FOCAULT / FOUCAULT), mismos numeros
        import difflib
        best=None; bs=0.0; second=0.0
        for k in (alnum(info.get('name')),alnum(f['file'])):
            if not k or len(k)<5: continue
            kd=re.findall(r'\d+',k)
            for a,m in machines:
                if id(m) in used: continue
                mk=alnum(m.get('name'))
                if not mk or mk in exact_keys or re.findall(r'\d+',mk)!=kd: continue
                r=difflib.SequenceMatcher(None,k,mk).ratio()
                if r>bs:
                    if best is not None and best is not m: second=bs
                    bs=r; best=m
                elif best is not m and r>second: second=r
        if best is not None and bs>=0.84 and bs-second>=0.05:
            rn=(info.get('name') or '').strip()
            if rn and alnum(rn) and len(alnum(rn))>=5: best['name']=titlecase(rn)
            return best
        return None
    exact_keys=set()
    for f in current:
        for k in _keys(f):
            if k in byname: exact_keys.add(k)
    nextid=len(machines)
    for f in current:
        info=f['info']; g=info.get('grade')
        if g is None: continue
        m=find(f)
        isnew=m is None
        if isnew:
            rn=(info.get('name') or '').strip()
            nm=titlecase(rn) if (rn and rn.lower().replace(' ','').replace('.','') not in ('mm/s','mm/seg','mms')) else titlecase(f['file'].replace('_',' '))
            m={'id':cid+'n'+str(nextid),'name':nm,'insp':'','techs':['Vibraciones'],'comps':[],'edates':[],'trend':[],'evo':[],'rms':[]}
            nextid+=1
            arname=titlecase(info.get('area') or 'General')
            ar=[a for a in P['areas'] if norm(a.get('name'))==norm(arname)]
            if ar: ar[0]['machines'].append(m)
            else: P.setdefault('areas',[]).append({'name':arname,'machines':[m]})
            machines.append((None,m)); added.append(nm)
        used.add(id(m))
        multi=len({x['comp'] for x in info['fens']})>1
        m['grade']=g; m['state']=st(g)
        m['fens']=[{'f':(x['f']+' · '+x['comp'].title()) if multi else x['f'],'grado':x['grado'],'estado':x.get('estado',''),'rec':x.get('rec','')} for x in info['fens']]
        m['note']=' · '.join(info.get('note') or []); m['rec']=info.get('rec',''); m['recomendacion']=info.get('rec','')
        m.setdefault('comps',[])
        for c in info['comps']:
            ex=[x for x in m['comps'] if norm(x.get('name'))==norm(c['name'])]
            if ex: ex=ex[0]
            else: ex={'name':c['name'],'series':[]}; m['comps'].append(ex)
            ex['maxgrade']=c['maxgrade']; ex['driver']=c['driver']; ex.setdefault('series',[])
            upsert(ex['series'],'d',label,{'d':label,'g':c['maxgrade']})
        m.setdefault('trend',[]); m.setdefault('evo',[]); m.setdefault('edates',[]); m.setdefault('rms',[])
        upsert(m['trend'],'l',label,{'l':label,'g':g}); upsert(m['evo'],'q',label,{'q':label,'g':g})
        if not m['edates'] or m['edates'][-1]!=label: m['edates'].append(label)
        del m['edates'][:-12]
        if info.get('maxrms') is not None:
            upsert(m['rms'],'l',label,{'l':label,'v':info['maxrms']}); m['hasValues']=True
            m['maxrms']=info['maxrms']; m['focuspt']=info.get('focus') or ''
        else:
            m['hasValues']=bool(m.get('rms')) and False
        for k in ('nomedido','placeholder','okSinFicha'): m.pop(k,None)
        if not isnew: upd.append(m['name'])

    # Maquinas sin ficha nueva: no medido (gris) u OK sin ficha (se mantiene diagnostico, cambia la fecha)
    _FAB={'FRAG':'FRAGMENTADORA','ASP':'ASPIRACION','VENT':'VENTILADOR','BBA':'BOMBA','MOT':'MOTOR','SOP':'SOPLANTE'}
    def ftoks(t):
        out=set()
        for x in re.split(r'[^A-Z0-9]+',_noacc(norm(t))):
            if not x or x in _STOPW: continue
            mm=re.match(r'^M(\d{1,2})$',x)
            if mm: out.update(('MOLINO',mm.group(1))); continue
            out.add(_FAB.get(x,x))
        return out
    rest=[(a,m) for a,m in machines if id(m) not in used and not m.get('placeholder')]
    area_of={}
    for ar in P.get('areas',[]):
        for m in ar.get('machines',[]): area_of[id(m)]=ar.get('name','')
    nm_ids=set(); left=[]
    for code,nm in nomed:
        hit=None
        for a,m in rest:
            if id(m) in nm_ids: continue
            mc=codes_of(m.get('name'))
            if (code and code in mc) or (len(alnum(nm))>=6 and alnum(nm)==alnum(m.get('name'))) or (len(toks(nm))>=2 and toks(nm)==toks(m.get('name'))):
                hit=m; break
        if hit is not None: nm_ids.add(id(hit))
        else: left.append((code,nm))
    # Emparejado aproximado para nombres abreviados del PDF (p. ej. "ASPIRACION FRAG.5")
    cands=[]
    for idx,(code,nm) in enumerate(left):
        pt=ftoks(nm); pnum={x for x in pt if x.isdigit()}
        if not pt: continue
        best=[]
        for a,m in rest:
            if id(m) in nm_ids: continue
            nt=ftoks(m.get('name')); at=ftoks(area_of.get(id(m),''))
            if not pnum<=({x for x in nt if x.isdigit()}|{x for x in at if x.isdigit()}): continue
            ov=len(pt&nt); sc=ov+0.5*len((pt-nt)&at)
            strong=ov>=2 or (ov==1 and any(len(x)>=6 for x in pt&nt))
            if strong: best.append((sc,-len(nt-pt),m))
        if best:
            best.sort(key=lambda z:(z[0],z[1]),reverse=True)
            if len(best)==1 or (best[0][0],best[0][1])!=(best[1][0],best[1][1]): cands.append((best[0][0],idx,best[0][2]))
    done_left=set()
    for sc,idx,m in sorted(cands,key=lambda z:-z[0]):
        if id(m) in nm_ids or idx in done_left: continue
        nm_ids.add(id(m)); done_left.add(idx)
    left=[e for i2,e in enumerate(left) if i2 not in done_left]
    nomed_n=0; carried=[]
    for a,m in machines:
        if id(m) in used: continue
        mc=codes_of(m.get('name')); mn=alnum(m.get('name'))
        if id(m) in nm_ids:
            m['nomedido']=True; m['state']='nomedido'; m['hasValues']=False; m.pop('okSinFicha',None); nomed_n+=1
            continue
        _mw=set(_ABR.get(t,t) for t in re.split(r'[^A-Z0-9]+',_noacc(norm(m.get('name')))) if t and t not in _STOPW)
        _pw=pdfwords|set(_ABR.get(t,t) for t in pdfwords)
        inpdf=bool(pdftxt) and ((mn and len(mn)>=6 and mn in pdftxt) or any(c in pdftxt for c in mc) or (len(_mw)>=3 and _mw<=_pw))
        if inpdf and m.get('grade') is not None and not m.get('placeholder'):
            g=m['grade']; m['state']=st(g); m.pop('nomedido',None)
            m['okSinFicha']=True; m['hasValues']=False
            m.setdefault('trend',[]); m.setdefault('evo',[]); m.setdefault('edates',[])
            upsert(m['trend'],'l',label,{'l':label,'g':g}); upsert(m['evo'],'q',label,{'q':label,'g':g})
            if not m['edates'] or m['edates'][-1]!=label: m['edates'].append(label)
            del m['edates'][:-12]
            for c in m.get('comps',[]):
                if c.get('series'): upsert(c['series'],'d',label,{'d':label,'g':c['series'][-1]['g']})
            carried.append(m['name'])
    # No medidos del PDF sin maquina equivalente -> marcador en gris (solo si ya no existe uno igual)
    names_now={alnum(m.get('name')) for a,m in machines}
    ph=0
    for code,nm in left:
        if alnum(nm) in names_now: continue
        disp=titlecase(nm or code)
        if not disp: continue
        names_now.add(alnum(disp))
        pm={'id':cid+'nm'+str(nextid),'name':disp,'state':'nomedido','nomedido':True,'placeholder':True,'grade':None,'fens':[],'comps':[],'edates':[],'trend':[],'evo':[],'rms':[],'hasValues':False,'maxrms':None,'note':'','rec':'','recomendacion':'','insp':'','techs':['Vibraciones']}
        nextid+=1
        ar=[a for a in P['areas'] if a.get('name')=='Pendientes de medición']
        if ar: ar[0]['machines'].append(pm)
        else: P['areas'].append({'name':'Pendientes de medición','machines':[pm]})
        ph+=1

    _fd=max(f['date'] for f in current if f.get('date'))
    # La fecha de medida y el tecnico se toman del PDF (dia de la visita y "REALIZADO"); la ficha solo como ultimo recurso
    P['medicion']=pmeta.get('medicion') or pmeta.get('fecha_informe') or ('%02d/%02d/%04d'%(_fd[2],_fd[1],_fd[0]))
    if pmeta.get('tecnico'): P['tecnico']=pmeta['tecnico']
    elif tecnico: P['tecnico']=tecnico
    if pmeta.get('aprobado'): P['aprobado']=pmeta['aprobado']
    res={'ok':True,'planta':P.get('id'),'periodo':label,'medicion':P['medicion'],'tecnico':P.get('tecnico'),'fichas':len(fichas),'fichas_mes':len(current),'actualizadas':len(upd),'nuevas':added,'ok_sin_ficha':len(carried),'no_medidas':nomed_n,'pendientes_nuevas':ph,'dry':dry}
    # Comprobacion de destino: las fichas y el PDF son de este cliente/planta? (por contenido, no por nombre de archivo)
    _tot=len(upd)+len(added); _antes=len(machines)-len(added)
    try: _own,_otro=pdf_owner(pdfwords,data,cid,datapath,P)
    except Exception: _own,_otro=None,''
    res['coinciden']=len(upd); res['total_fichas']=_tot; res['pdf_cliente']=_own; res['pdf_otro']=_otro
    res['sospechoso']=bool((_tot>=3 and _antes>=3 and len(upd)*2<_tot) or (_otro and not _own))
    if strict and res['sospechoso']:
        res['ok']=False; res['e']='otrocliente'; print(json.dumps(res,ensure_ascii=False)); return
    if not upd and not added:
        res['ok']=False; res['e']='sincambios'; print(json.dumps(res,ensure_ascii=False)); return
    if not dry:
        txt=json.dumps(data,ensure_ascii=False)
        json.loads(txt)
        bdir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(datapath))),'backups')
        try:
            os.makedirs(bdir,exist_ok=True)
            shutil.copy2(datapath,os.path.join(bdir,'%s.%s.bak'%(cid,_dt.datetime.now().strftime('%Y%m%d-%H%M%S'))))
            res['backup']=True
        except Exception:
            res['backup']=False
        with open(datapath,'w',encoding='utf-8') as fh: fh.write(txt)
    else:
        json.dump(data,open('/tmp/_publish_dry_%s.json'%cid,'w',encoding='utf-8'),ensure_ascii=False)
    print(json.dumps(res,ensure_ascii=False))

if __name__=='__main__':
    main()
