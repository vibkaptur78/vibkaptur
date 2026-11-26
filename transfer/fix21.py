import shutil,time,sys,os,py_compile
F='/var/www/vibkaptur/scripts/vibk_termo_srv.py'
if len(sys.argv)>1: F=sys.argv[1]
s=open(F,encoding='utf-8').read()
A="elif k.startswith('ACCION RECOMENDADA'): blk['accion']=d[-1] if len(d)>1 else ''"
B="elif re.match(r'(ACCION(ES)?|ACTUACION(ES)?) RECOMENDADAS?',k): blk['accion']=d[-1] if len(d)>1 else ''"
if B in s: print('YA ESTABA, no he tocado nada'); sys.exit()
if s.count(A)!=1: print('NO HE TOCADO NADA: el archivo no es como esperaba'); sys.exit()
T=F+'.nuevo.py'; open(T,'w',encoding='utf-8').write(s.replace(A,B))
try: py_compile.compile(T,cfile='/tmp/vibk_chk.pyc',doraise=True)
except Exception as e: os.remove(T); print('NO HE TOCADO NADA: error',e); sys.exit()
if len(sys.argv)==1:
    os.makedirs('/root/vibk_api_antes',exist_ok=True); shutil.copy2(F,'/root/vibk_api_antes/vibk_termo_srv.py.'+time.strftime('%Y%m%d_%H%M'))
st=os.stat(F); os.replace(T,F); os.chown(F,st.st_uid,st.st_gid); os.chmod(F,st.st_mode)
print('TERMOGRAFIAS: LECTURA DE «ACTUACION RECOMENDADA» CORREGIDA')
