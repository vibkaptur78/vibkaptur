<?php
$c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_GET['c'])?$_GET['c']:''));
$pl=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_GET['p'])?$_GET['p']:''));
$t=isset($_GET['t'])?$_GET['t']:'';
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
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
