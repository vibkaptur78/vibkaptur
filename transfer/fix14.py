import subprocess,shutil,time,sys,os
F='/var/www/vibkaptur/public/api/informe.php'
if len(sys.argv)>1: F=sys.argv[1]
s=open(F,encoding='utf-8').read()
A="if(count($p)!=2 || !$secret)"
if "$p=explode('.',$t);" in s: print('YA ESTABA CORREGIDO, no he tocado nada'); sys.exit()
if s.count(A)!=1: print('NO HE TOCADO NADA: el archivo no es como esperaba'); sys.exit()
n=s.replace(A,"$p=explode('.',$t);\n"+A)
T=F+'.nuevo.php'; open(T,'w',encoding='utf-8').write(n)
r=subprocess.run(['php','-l',T],capture_output=True,text=True)
if r.returncode!=0: os.remove(T); print('NO HE TOCADO NADA: error de sintaxis',r.stdout); sys.exit()
os.makedirs('/root/vibk_api_antes',exist_ok=True)
shutil.copy2(F,'/root/vibk_api_antes/informe.php.'+time.strftime('%Y%m%d_%H%M'))
st=os.stat(F); os.replace(T,F); os.chown(F,st.st_uid,st.st_gid); os.chmod(F,st.st_mode)
print('DESCARGA DE INFORMES CORREGIDA')
