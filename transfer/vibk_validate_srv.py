#!/usr/bin/env python3
# VIBKAPTUR - Validador automatico de informes (AUTONOMO, para el servidor).
# Lee fichas (.xls/.xlsm) + PDF, revisa TODO lo mecanico salvo el analisis,
# y devuelve JSON con stats, findings (uno por fallo) y el HTML del aviso.
# Uso: vibk_validate_srv.py <pdf> <carpeta_fichas> [cliente] [tecnica] [periodo] [emails]
import xlrd, openpyxl, glob, os, re, json, sys, subprocess, datetime as _dt

SECT={'ESPECTROS','HISTORIAL','DATOS','CONDICIONES','TIPOLOGÍA','ERGOMETRÍA','COMENTARIOS','PUNTOS','ÁREA','MOTOR Y BOMBA','ANÁLISIS','ESPECTRO'}
def norm(s): return re.sub(r'\s+',' ',str(s if s is not None else '')).strip().upper()
def isnum(v):
    try: return float(v)
    except: return None
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
                area_row=r; a=str(cell(r,c+2) if c+2<ncols else '').strip()
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
    mg=max([c['maxgrade'] for c in comps],default=None)
    if grade is not None: mg=max(mg or 0,grade)
    fens=[{'f':p,'grado':g,'estado':summ.get(norm(p),{}).get('estado',''),'rec':summ.get(norm(p),{}).get('rec','')} for c in comps for p,g in c['phen']]
    return {'name':name,'grade':mg,'fens':fens}
def parse_xls(path):
    sh=xlrd.open_workbook(path).sheet_by_index(0)
    return parse_grid(lambda r,c: sh.cell_value(r,c) if c<sh.ncols else '', sh.nrows, sh.ncols)
def parse_xlsm_sheets(path):
    wb=openpyxl.load_workbook(path,data_only=True,read_only=True); res={}
    for sh in wb.sheetnames:
        if sh in ('RESUMEN','EXTRA'): continue
        ws=wb[sh]; grid=[[c.value for c in row] for row in ws.iter_rows()]
        nr=len(grid); nc=max((len(r) for r in grid),default=0)
        def cell(r,c,grid=grid,nc=nc): return grid[r][c] if (r<len(grid) and c<len(grid[r])) else ''
        d=parse_grid(cell,nr,nc); d['name']=d['name'] or sh; res[sh]=d
    wb.close(); return res

# ---------- Validador ----------
TABLE={10:'INSATISFACTORIO - EFECTO GRAVE',9:'INSATISFACTORIO - EFECTO GRAVE',8:'INSATISFACTORIO - EFECTO DAÑINO',7:'INSATISFACTORIO - EFECTO DAÑINO',6:'ATENCIÓN - EFECTO MODERADO',5:'ATENCIÓN - EFECTO SIGNIFICATIVO',4:'SATISFACTORIO - EFECTO SIGNIFICATIVO',3:'SATISFACTORIO - EFECTO LEVE',2:'SATISFACTORIO - EFECTO LEVE',1:'SATISFACTORIO - EFECTO MENOR'}
BANDA={g:t.split(' - ')[0] for g,t in TABLE.items()}
CODE=re.compile(r'(\d{3}[A-Z0-9]+)')

# --- Ortografía (hunspell es_ES) con lista blanca de tecnicismos ---
_WHITE=set("""rms tag vibkaptur ingenor weylchem kronospan betanzos otua rodamiento rodamientos desequilibrio desequilibrios desalineacion acoplamiento acoplamientos engrase engrases holgura holguras espectro espectros armonico armonicos cojinete cojinetes chumacera chumaceras impulsor impulsores rodete rodetes ventilador ventiladores soplante soplantes reductor reductora reductoras multiplicadora acelerometro termografia vibraciones vibracion envolvente cinematica engranaje engranajes polea poleas correa correas oleum absorcion sulfurico demi azufre fusion reglaje severidad satisfactorio insatisfactorio atencion significativo cuadro cuadros estabilidad""".split())
_WHITE2=set("acelerómetro acelerómetros termográfica termográficas videoscopía endoscopía holgura hertzios hercios triaxial triaxiales ergometría ergometria rotacionales rotacional desalineación desalineacion electromagnética electromagnetica report reporte espectral espectrales envolventes axial radial tangencial cinemático cinemáticos".split())
def spell_findings(sources):
    # sources: lista de (etiqueta, texto). Devuelve (etiqueta, 'palabra -> sugerencia').
    out=[]; seen=set()
    for label,text in sources:
        if not text or not text.strip(): continue
        try:
            r=subprocess.run(['hunspell','-d','es_ES','-a'],input=text,capture_output=True,text=True,timeout=30)
        except Exception:
            continue
        for ln in r.stdout.splitlines():
            if not ln or ln[0] not in '&#': continue
            parts=ln.split()
            if len(parts)<2: continue
            w=parts[1]
            if len(w)<5 or w.isupper() or any(ch.isdigit() for ch in w): continue
            lw=w.lower()
            if lw in _WHITE or lw in _WHITE2: continue
            if (label,lw) in seen: continue
            seen.add((label,lw))
            sug=''
            if ln[0]=='&' and ':' in ln:
                sug=ln.split(':',1)[1].strip().split(',')[0].strip()
            out.append((label,'"%s"%s'%(w,(' → ¿"%s"?'%sug if sug else ''))))
            if len(out)>=60: return out
    return out

# --- Lectura de celdas + fecha de ficha (para detectar fichas arrastradas) ---
def _cells(f):
    vals=[]
    try:
        if f.lower().endswith(('.xlsx','.xlsm')):
            wb=openpyxl.load_workbook(f,data_only=True,read_only=True)
            for sh in wb.sheetnames:
                for row in wb[sh].iter_rows(values_only=True):
                    for c in row:
                        if c is not None: vals.append(c)
            wb.close()
        else:
            bk=xlrd.open_workbook(f); sh=bk.sheet_by_index(0)
            for r in range(sh.nrows):
                for c in range(sh.ncols):
                    cell=sh.cell(r,c)
                    if cell.ctype==3:
                        try: vals.append(_dt.datetime(*xlrd.xldate_as_tuple(cell.value,bk.datemode)))
                        except Exception: pass
                    elif cell.value not in (None,''): vals.append(cell.value)
    except Exception: pass
    return vals
def _ficha_my(vals):
    best=None
    for v in vals:
        y=mn=None
        if isinstance(v,_dt.datetime): y,mn=v.year,v.month
        elif isinstance(v,str):
            m=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',v)
            if m:
                mn=int(m.group(2)); y=int(m.group(3)); y=y+2000 if y<100 else y
        if y and mn and 1<=mn<=12:
            k=(y,mn)
            if best is None or k>best: best=k
    return best
def _texts(vals):
    return [v for v in vals if isinstance(v,str) and len(v)>3]

def pdf_resumen(pdf):
    txt=subprocess.run(['pdftotext','-f','1','-l','16','-layout',pdf,'-'],capture_output=True,text=True).stdout
    grades,nomed={},[]
    for ln in txt.splitlines():
        c=CODE.search(ln)
        if not c: continue
        code=c.group(1)
        if 'NO MEDIDO' in ln.upper(): nomed.append(code); continue
        g=re.search(r'\b([1-9]|10)\b\s+\d+[.,]\d+',ln)
        if g: grades[code]=int(g.group(1))
    m=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',txt)
    return grades,nomed,(m.group(0) if m else None),txt

def validate(pdf,fich,ftexts=None):
    pg,pn,fecha,txt=pdf_resumen(pdf); out=[]
    rep_my=None
    if fecha:
        _m=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',fecha)
        if _m:
            _yy=int(_m.group(3)); rep_my=(_yy+2000 if _yy<100 else _yy,int(_m.group(2)))
    def carried(c):
        my=fich.get(c,{}).get('my')
        return rep_my is not None and my is not None and my<rep_my
    # Completitud: fichas de este mes que no aparecen en el resumen del PDF
    _pdftxt=re.sub(r'[^A-Z0-9]','',txt.upper())
    def _inpdf(c):
        if not re.match(r'^\d{3}',c): return True
        cc=re.sub(r'[^A-Z0-9]','',c.upper())
        return (cc in _pdftxt) or (len(cc)>=5 and cc[:-1] in _pdftxt)
    for c in fich:
        if carried(c) or _inpdf(c): continue
        out.append(('Completitud', 'La ficha «%s» (%s) no aparece en el resumen de medidas del PDF.'%(fich[c].get('file') or fich[c]['name'],c)))
    # Cuadre de grados PDF vs ficha (solo fichas actuales)
    for c,g in pg.items():
        if c in fich and fich[c]['grade'] is not None and fich[c]['grade']!=g and not carried(c):
            out.append(('Cuadre de grados', 'Ficha «%s» (%s): el PDF pone grado %s y la ficha pone grado %s.'%(fich[c].get('file') or fich[c]['name'],c,g,fich[c]['grade'])))
    # Texto vs grado (tabla de severidad)
    for c,d in fich.items():
        if carried(c): continue
        for fe in d.get('fens',[]):
            est=(fe.get('estado') or '').upper().strip(); gr=fe.get('grado')
            if est and gr in BANDA and BANDA[gr] not in est:
                out.append(('Texto vs grado', 'Ficha «%s» (%s): el fenómeno con grado %s dice "%s", pero para grado %s la tabla indica "%s".'%(d.get('file') or d['name'],d['name'],gr,est[:45],gr,TABLE[gr])))
    if not fecha: out.append(('Fechas','No se ha encontrado la fecha del informe en el PDF.'))
    for label,det in spell_findings([('el informe PDF (resumen)',txt)]+(ftexts or [])):
        out.append(('Ortografía', 'En «%s»: %s'%(label,det)))
    carr=sum(1 for c in fich if carried(c))
    return out,{'pdf_medidas':len(pg),'pdf_no_medido':len(pn),'fichas':len(fich),'fecha':fecha,'arrastradas':carr}

def aviso_html(cliente,tecnica,periodo,findings):
    n=len(findings)
    order=[]; gmap={}
    for cat,det in findings:
        if cat not in gmap: gmap[cat]=[]; order.append(cat)
        gmap[cat].append(det)
    cuerpo=('La revisión automática ha encontrado <b>%d punto(s) a revisar</b> antes de publicar.'%n if n else 'La revisión automática no ha encontrado incongruencias. Listo para publicar.')
    body=''
    for cat in order:
        items=gmap[cat]
        lis=''.join('<li style="margin:3px 0">%s</li>'%d for d in items)
        body+='<p style="margin:14px 0 2px;font-weight:bold;color:#0d2d46;font-size:13px">%s (%d)</p><ul style="margin:2px 0 0;padding-left:20px">%s</ul>'%(cat,len(items),lis)
    pts=('<p style="margin:14px 0 4px"><b>Puntos a revisar (todo mecánico; el análisis no se valora):</b></p>%s'%body if n else '')
    return ('<div style="font-family:Arial,sans-serif;max-width:620px"><div style="background:#0d2d46;color:#fff;padding:14px 18px;font-weight:bold">INGENOR · VIBKAPTUR — Revisión de informe</div><div style="padding:18px 20px;color:#333;font-size:13.5px;line-height:1.6"><p>Hola,</p><p>Informe de <b>%s</b> (%s · %s) subido a la plataforma. %s</p>%s<p style="margin:16px 0 4px;color:#64748b;font-size:12.5px">Cuando el técnico corrija y se dé el <b>OK</b>, el informe se publica y le llega el aviso al cliente.</p><p style="color:#8a98a6;font-size:12px;margin:10px 0 0">— VIBKAPTUR · revisión automática</p></div></div>'%(cliente,tecnica,periodo,cuerpo,pts))

def parse_fichas(folder):
    res={}; sources=[]
    for f in sorted(glob.glob(os.path.join(folder,'*.xls*'))):
        if 'plantilla' in f.lower(): continue
        try:
            _v=_cells(f); _fd=_ficha_my(_v)
            _fn=os.path.splitext(os.path.basename(f))[0]
            _tx=' \n '.join(_texts(_v))
            if _tx.strip(): sources.append((_fn,_tx))
            if f.lower().endswith('.xlsm'):
                for sh,d in parse_xlsm_sheets(f).items():
                    _s=((d.get('name') or sh)+' '+sh).upper().replace(' ','').replace('_','')
                    cc=CODE.search(_s)
                    res[cc.group(1) if cc else (d.get('name') or sh)]={'grade':d.get('grade'),'name':d.get('name') or sh,'fens':d.get('fens',[]),'my':_fd,'file':_fn}
            else:
                d=parse_xls(f); base=os.path.splitext(os.path.basename(f))[0].upper()
                _s=(base+' '+(d.get('name') or '')).upper().replace(' ','').replace('_','')
                cc=CODE.search(_s)
                res[cc.group(1) if cc else (d.get('name') or base)]={'grade':d.get('grade'),'name':d.get('name') or base,'fens':d.get('fens',[]),'my':_fd,'file':_fn}
        except Exception: pass
    return res, sources

def construir_subject(cliente,periodo,findings):
    if not findings: return "VIBKAPTUR - Revision %s (%s) - correcto, listo para publicar"%(cliente,periodo)
    return "VIBKAPTUR - Revision %s (%s) - %d punto(s) a revisar"%(cliente,periodo,len(findings))
def enviar(subject,html,recipients,endpoint='https://vibkaptur.com/api/aviso.php'):
    import urllib.request
    payload={'type':'client','to':[e for e in recipients if e],'subject':subject,'html':html}
    data=json.dumps(payload,ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(endpoint,data=data,headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=25) as r: return r.status,r.read().decode()
    except Exception as e: return 0,'ERR '+str(e)

if __name__=='__main__':
    if len(sys.argv)<3:
        print(json.dumps({'error':'uso: vibk_validate_srv.py <pdf> <carpeta_fichas> [cliente] [tecnica] [periodo] [emails]'})); sys.exit(1)
    fich,ftexts=parse_fichas(sys.argv[2])
    findings,stats=validate(sys.argv[1],fich,ftexts)
    cliente=sys.argv[3] if len(sys.argv)>3 else 'CLIENTE'
    tecnica=sys.argv[4] if len(sys.argv)>4 else 'Vibraciones'
    periodo=sys.argv[5] if len(sys.argv)>5 else ''
    html=aviso_html(cliente,tecnica,periodo,findings)
    recipients=[]
    if len(sys.argv)>6 and sys.argv[6].strip():
        recipients=[e.strip() for e in sys.argv[6].split(',') if e.strip()]
    enviado=None
    if recipients:
        subject=construir_subject(cliente,periodo,findings)
        code,resp=enviar(subject,html,recipients)
        enviado={'code':code,'resp':resp,'to':recipients}
    print(json.dumps({'stats':stats,'findings':findings,'aviso_html':html,'enviado':enviado},ensure_ascii=False))
