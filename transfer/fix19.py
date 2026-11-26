import subprocess,shutil,time,os,sys,json
F='/var/www/vibkaptur/private/users.php'
if len(sys.argv)>1: F=sys.argv[1]
def php(code):
    return subprocess.run(['php','-r',code.replace('@@F@@',F)],capture_output=True,text=True).stdout
L=json.loads(php('$u=include "@@F@@"; $o=array(); foreach($u as $e=>$x){ $o[]=array($e,isset($x["role"])?$x["role"]:"",isset($x["c"])?$x["c"]:"",isset($x["name"])?$x["name"]:""); } echo json_encode($o);') or '[]')
if not L: print('NO HE TOCADO NADA: no puedo leer los usuarios'); sys.exit()
keep=[x for x in L if x[1] in ('admin','tecnico')]; quita=[x for x in L if x[1] not in ('admin','tecnico')]
print('SE QUEDAN (%d):'%len(keep))
for e,r,c,n in keep: print('   %-8s %s'%(r,e))
print('SE QUITAN (%d):'%len(quita))
for e,r,c,n in quita: print('   %-8s %-12s %s'%(r or '?',c,e))
if not quita: print('No hay nada que quitar.'); sys.exit()
if len([x for x in keep if x[1]=='admin'])<1: print('NO HE TOCADO NADA: no quedaria ningun administrador'); sys.exit()
r=input('Escribe SI (en mayusculas) y pulsa Intro para quitarlos. Cualquier otra cosa cancela: ').strip()
if r!='SI': print('CANCELADO. No he tocado nada.'); sys.exit()
B='/root/users.php.antes_limpieza_'+time.strftime('%Y%m%d_%H%M') if len(sys.argv)==1 else F+'.antes'
shutil.copy2(F,B); st=os.stat(F)
out=php('$f="@@F@@"; $u=include $f; $n=count($u); foreach($u as $e=>$x){ $r=isset($x["role"])?$x["role"]:""; if($r!=="admin" && $r!=="tecnico") unset($u[$e]); } $t=$f.".tmp"; file_put_contents($t,"<?php\\n// VIBKAPTUR usuarios (servidor). Claves cifradas.\\nreturn ".var_export($u,true).";\\n"); $v=include $t; if(is_array($v) && count($v)===count($u) && count($u)>0){ rename($t,$f); echo "USUARIOS DE EJEMPLO QUITADOS: quedan ".count($u)." de ".$n; } else { unlink($t); echo "NO HE TOCADO NADA: fallo al guardar"; }')
os.chown(F,st.st_uid,st.st_gid); os.chmod(F,st.st_mode)
print(out); print('Copia de la lista anterior en',B)
