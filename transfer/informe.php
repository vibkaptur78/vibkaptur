<?php
$c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_GET['c'])?$_GET['c']:''));
$pl=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_GET['p'])?$_GET['p']:''));
$t=isset($_GET['t'])?$_GET['t']:'';
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$k=isset($_GET['k'])?(string)$_GET['k']:'';
if($k!==''){
  /* Enlace directo del correo: firmado por el servidor, sin sesion ni caducidad, solo para ese informe */
  $m=preg_replace('/[^a-z0-9-]/','',strtolower(isset($_GET['m'])?$_GET['m']:''));
  if(!$secret || $c==='' || $m==='' || !hash_equals(hash_hmac('sha256','dl|'.$c.'|'.$pl.'|'.$m,$secret),$k)){http_response_code(403);echo 'Enlace no valido';exit;}
  $d='/var/www/vibkaptur/reports/'.$c.($pl!==''?('/'.$pl):'');
  $file=$d.'/hist/'.$m.'.pdf';
  if(!is_file($file)) $file=$d.'/informe.pdf';
  if(!is_file($file)){http_response_code(404);echo 'Informe no disponible';exit;}
  header('Content-Type: application/pdf');
  header('Content-Disposition: attachment; filename="Informe_'.$c.($pl!==''?('_'.$pl):'').'_'.$m.'.pdf"');
  header('Content-Length: '.filesize($file));
  readfile($file); exit;
}
if(count($p)!=2 || !$secret){http_response_code(403);echo 'Acceso denegado';exit;}
if(!hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);echo 'Token no valido';exit;}
$a=array_pad(explode('|',base64_decode(strtr($p[0],'-_','+/'))),4,'');
$role=$a[0]; $pc=$a[1]; $exp=intval($a[2]); $flags=$a[3];
if(time()>$exp){http_response_code(403);echo 'Sesion caducada, vuelve a entrar';exit;}
if(strpos($flags,'d')===false){http_response_code(403);echo 'Sin permiso de descarga';exit;}
if($role!=='admin' && $pc!==$c){http_response_code(403);echo 'No autorizado';exit;}
if($c===''){http_response_code(404);echo 'Informe no disponible';exit;}
$base='/var/www/vibkaptur/reports/'.$c;
$file=$base.'/informe.pdf';
$name='Informe_'.$c;
if($pl!==''){
  $pf=$base.'/'.$pl.'/informe.pdf';
  if(is_file($pf)){ $file=$pf; $name.='_'.$pl; }
  else if(count(glob($base.'/*/informe.pdf'))>0){ http_response_code(404);echo 'Informe no disponible';exit; }
}
if(!is_file($file)){http_response_code(404);echo 'Informe no disponible';exit;}
header('Content-Type: application/pdf');
header('Content-Disposition: attachment; filename="'.$name.'.pdf"');
header('Content-Length: '.filesize($file));
readfile($file);
