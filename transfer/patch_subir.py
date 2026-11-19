# Parche de subir.php: guardar fichas y PDF por planta cuando el cliente tiene varias.
import sys,shutil,time
A=sys.argv[1]; s=open(A,encoding='utf-8').read()
if '$PL' in s:
    print('subir.php ya estaba parcheado'); sys.exit(0)
shutil.copy2(A,A+'.bak.'+str(int(time.time())))
old="'/var/www/vibkaptur/reports/'.$c"
n=s.count(old)
anchor="$secret=trim("
if n<1 or s.count(anchor)!=1:
    print('NO PARCHEADO: estructura inesperada (rutas=%d)'%n); sys.exit(1)
s=s.replace(old,old+".$PL")
s=s.replace(anchor,"$PL=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_POST['p'])?$_POST['p']:'')); $PL=($PL!==''?('/'.$PL):'');\n"+anchor,1)
open(A,'w',encoding='utf-8').write(s)
print('subir.php parcheado (%d rutas)'%n)
