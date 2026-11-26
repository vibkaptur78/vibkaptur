import subprocess,shutil,time,os,sys
F='/var/www/vibkaptur/private/users.php'
if len(sys.argv)>1: F=sys.argv[1]
B=('/root/users.php.antes_tecnicos_'+time.strftime('%Y%m%d_%H%M')) if len(sys.argv)==1 else F+'.antes'
shutil.copy2(F,B); st=os.stat(F)
php=r'''$f="@@F@@"; $u=include $f; if(!is_array($u)||!count($u)){echo "NO HE TOCADO NADA: no puedo leer los usuarios\n"; exit;}
$abc="abcdefghjkmnpqrstuvwxyz"; $num="23456789"; $out=array();
foreach($u as $e=>$x){ if((isset($x["role"])?$x["role"]:"")!=="tecnico") continue;
  $p=""; for($i=0;$i<4;$i++){ $p.=$abc[random_int(0,strlen($abc)-1)]; } $p=ucfirst($p); for($i=0;$i<3;$i++){ $p.=$num[random_int(0,strlen($num)-1)]; } $p.="-"; for($i=0;$i<4;$i++){ $p.=$abc[random_int(0,strlen($abc)-1)]; } for($i=0;$i<2;$i++){ $p.=$num[random_int(0,strlen($num)-1)]; }
  $u[$e]["p"]=password_hash($p,PASSWORD_BCRYPT); $out[$e]=$p; }
if(!count($out)){echo "No hay usuarios de tecnico. No he tocado nada\n"; exit;}
$t=$f.".tmp"; file_put_contents($t,"<?php\n// VIBKAPTUR usuarios (servidor). Claves cifradas.\nreturn ".var_export($u,true).";\n"); $v=include $t;
if(!is_array($v)||count($v)!==count($u)){ unlink($t); echo "NO HE TOCADO NADA: fallo al guardar\n"; exit; }
foreach($out as $e=>$p){ if(!password_verify($p,$v[$e]["p"])){ unlink($t); echo "NO HE TOCADO NADA: fallo al comprobar\n"; exit; } }
rename($t,$f);
echo "CONTRASENAS NUEVAS DE LOS TECNICOS (apuntalas ahora, no se vuelven a mostrar):\n\n"; foreach($out as $e=>$p){ echo "   ".str_pad($e,36)." ".$p."\n"; } echo "\nHECHO: ".count($out)." contrasenas cambiadas\n";'''
print(subprocess.run(['php','-r',php.replace('@@F@@',F)],capture_output=True,text=True).stdout)
os.chown(F,st.st_uid,st.st_gid); os.chmod(F,st.st_mode)
