import subprocess,shutil,time,os
F='/var/www/vibkaptur/private/users.php'
shutil.copy2(F,'/root/users.php.antes_'+time.strftime('%Y%m%d_%H%M'))
php=r'''$f="/var/www/vibkaptur/private/users.php"; $u=include $f; if(!is_array($u)||!count($u)){echo "NO HE TOCADO NADA: no puedo leer los usuarios\n"; exit;} $n=0; foreach($u as $e=>$x){ if(isset($x["role"]) && $x["role"]==="admin"){ $antes=(!empty($x["dl"])?"descarga si":"descarga NO").", ".(!empty($x["up"])?"subida si":"subida NO"); if(empty($x["dl"])||empty($x["up"])){ $u[$e]["dl"]=true; $u[$e]["up"]=true; $n++; echo "CORREGIDO ".$e." (antes: ".$antes.")\n"; } else echo "ya estaba bien ".$e."\n"; } } if($n){ $t=$f.".tmp"; file_put_contents($t,"<?php\n// VIBKAPTUR usuarios (servidor). Claves cifradas.\nreturn ".var_export($u,true).";\n"); $v=include $t; if(is_array($v)&&count($v)===count($u)){ rename($t,$f); } else { unlink($t); echo "NO HE TOCADO NADA: fallo al guardar\n"; exit; } } echo "PERMISOS DE ADMINISTRADOR REVISADOS (".count($u)." usuarios)\n";'''
st=os.stat(F)
print(subprocess.run(['php','-r',php],capture_output=True,text=True).stdout.strip())
os.chown(F,st.st_uid,st.st_gid); os.chmod(F,st.st_mode)
