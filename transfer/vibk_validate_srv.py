#!/usr/bin/env python3
# VIBKAPTUR - Validador automatico de informes (AUTONOMO, para el servidor).
# Lee fichas (.xls/.xlsm) + PDF, revisa TODO lo mecanico salvo el analisis,
# y devuelve JSON con stats, findings y el HTML del aviso.
# Uso: vibk_validate_srv.py <pdf> <carpeta_fichas> [cliente] [tecnica] [periodo]
import xlrd, openpyxl, glob, os, re, json, sys, subprocess

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
TYPOS=[('asoiciad','asociad'),('componenetes','componentes'),('anomalias','anomalías'),('rodaniento','rodamiento'),('desequilbrio','desequilibrio'),('vibracon','vibración'),('alineacon','alineación')]
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
def validate(pdf,fich):
    pg,pn,fecha,txt=pdf_resumen(pdf); out=[]
    ef=[c for c in pg if c not in fich]
    fp=[c for c in fich if c not in pg and c not in pn]
    if ef: out.append(('Completitud', f'{len(ef)} máquina(s) medidas en el PDF sin ficha: '+', '.join(ef[:8])))
    if fp: out.append(('Completitud', f'{len(fp)} ficha(s) que no figuran en el resumen del PDF: '+', '.join(fp[:8])))
    disc=[f'{fich[c]["name"]} ({c}): PDF {g} vs ficha {fich[c]["grade"]}' for c,g in pg.items() if c in fich and fich[c]['grade'] is not None and fich[c]['grade']!=g]
    if disc: out.append(('Cuadre de grados PDF↔ficha', f'{len(disc)} discrepancia(s): '+'; '.join(disc[:6])))
    tbl=[]
    for c,d in fich.items():
        for fe in d.get('fens',[]):
            est=(fe.get('estado') or '').upper().strip(); gr=fe.get('grado')
            if est and gr in BANDA and BANDA[gr] not in est:
                tbl.append(f'{d["name"]}: fenómeno grado {gr} dice "{est[:26]}" (tabla: "{TABLE[gr]}")')
    if tbl: out.append(('Texto↔grado (tabla de severidad)', f'{len(tbl)} incongruencia(s): '+'; '.join(tbl[:6])))
    if not fecha: out.append(('Fechas','No se ha encontrado la fecha del informe en el PDF.'))
    low=txt.lower(); typ=[f'"{b}" → "{g}"' for b,g in TYPOS if b in low]
    if typ: out.append(('Ortografía','; '.join(typ)))
    return out,{'pdf_medidas':len(pg),'pdf_no_medido':len(pn),'fichas':len(fich),'fecha':fecha}
def aviso_html(cliente,tecnica,periodo,findings):
    li=''.join(f'<li style="margin:4px 0"><b>{t}:</b> {d}</li>' for t,d in findings); n=len(findings)
    cuerpo=(f'La revisión automática ha encontrado <b>{n} punto(s) a revisar</b> antes de publicar.' if n else 'La revisión automática no ha encontrado incongruencias. Listo para publicar.')
    pts=(f'<p style="margin:14px 0 4px"><b>Puntos a revisar (todo mecánico; el análisis no se valora):</b></p><ol style="margin:4px 0 0;padding-left:20px">{li}</ol>' if n else '')
    return (f'<div style="font-family:Arial,sans-serif;max-width:600px"><div style="background:#0d2d46;color:#fff;padding:14px 18px;font-weight:bold">INGENOR · VIBKAPTUR — Revisión de informe</div><div style="padding:18px 20px;color:#333;font-size:13.5px;line-height:1.6"><p>Hola,</p><p>Informe de <b>{cliente}</b> ({tecnica} · {periodo}) subido a la plataforma. {cuerpo}</p>{pts}<p style="margin:16px 0 4px;color:#64748b;font-size:12.5px">Cuando el técnico corrija y se dé el <b>OK</b>, el informe se publica y le llega el aviso al cliente.</p><p style="color:#8a98a6;font-size:12px;margin:10px 0 0">— VIBKAPTUR · revisión automática</p></div></div>')
def parse_fichas(folder):
    res={}
    for f in sorted(glob.glob(os.path.join(folder,'*.xls*'))):
        if 'plantilla' in f.lower(): continue
        try:
            if f.lower().endswith('.xlsm'):
                for sh,d in parse_xlsm_sheets(f).items():
                    cc=CODE.search((d.get('name') or sh).upper()) or CODE.search(sh.upper())
                    res[cc.group(1) if cc else (d.get('name') or sh)]={'grade':d.get('grade'),'name':d.get('name') or sh,'fens':d.get('fens',[])}
            else:
                d=parse_xls(f); base=os.path.splitext(os.path.basename(f))[0].upper()
                cc=CODE.search(base) or CODE.search((d.get('name') or '').upper())
                res[cc.group(1) if cc else (d.get('name') or base)]={'grade':d.get('grade'),'name':d.get('name') or base,'fens':d.get('fens',[])}
        except Exception: pass
    return res

def construir_subject(cliente,periodo,findings):
    if not findings: return f"VIBKAPTUR · Revisión {cliente} ({periodo}) — correcto, listo para publicar"
    return f"VIBKAPTUR · Revisión {cliente} ({periodo}) — {len(findings)} punto(s) a revisar"
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
        print(json.dumps({'error':'uso: vibk_validate_srv.py <pdf> <carpeta_fichas> [cliente] [tecnica] [periodo]'})); sys.exit(1)
    fich=parse_fichas(sys.argv[2])
    findings,stats=validate(sys.argv[1],fich)
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
