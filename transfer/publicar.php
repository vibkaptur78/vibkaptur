<?php
header('Content-Type: application/json');
$in=json_decode(file_get_contents('php://input'),true);
$t=isset($in['t'])?$in['t']:'';
$c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($in['c'])?$in['c']:''));
$pl=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($in['p'])?$in['p']:''));
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
if(count($p)!=2 || !$secret){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
if(!hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
$a=array_pad(explode('|',base64_decode(strtr($p[0],'-_','+/'))),4,'');
$exp=intval($a[2]); $flags=$a[3];
if(time()>$exp){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'exp'));exit;}
if(strpos($flags,'u')===false){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'noup'));exit;}
if(!$c){echo json_encode(array('ok'=>false,'e'=>'nocliente'));exit;}
$base='/var/www/vibkaptur/reports/'.$c;
$dir=$base.($pl!==''?('/'.$pl):'');
$pend=$dir.'/pending.pdf';
$reenvio=false; $lastpub=@filemtime($dir.'/publicado.txt');
$fic=$dir.'/fichas'; $dj='/var/www/vibkaptur/private/data/'.$c.'.json';
/* Antes de publicar nada: comprobar por contenido que fichas y PDF son de este cliente/planta */
if(is_file($pend) && is_file($dj) && empty($in['confirm'])){
  $chk=json_decode((string)shell_exec('python3 /var/www/vibkaptur/scripts/vibk_publish_srv.py '.escapeshellarg($c).' '.escapeshellarg($fic).' '.escapeshellarg($pend).' '.escapeshellarg($dj).' '.escapeshellarg($pl!==''?$pl:'-').' --dry --strict 2>&1'),true);
  if(is_array($chk) && ((isset($chk['e'])&&$chk['e']==='otrocliente') || (!empty($chk['pdf_otro']) && empty($chk['pdf_cliente'])))){
    echo json_encode(array('ok'=>false,'e'=>'otrocliente','coinciden'=>isset($chk['coinciden'])?$chk['coinciden']:null,'total'=>isset($chk['total_fichas'])?$chk['total_fichas']:null,'pdf_otro'=>isset($chk['pdf_otro'])?$chk['pdf_otro']:''));exit;
  }
}
if(!is_file($pend)){
  /* Sin PDF nuevo pendiente: si ya hay un informe publicado, se vuelve a lanzar el envio sin tener que subir nada */
  if(!is_file($dir.'/informe.pdf')){echo json_encode(array('ok'=>false,'e'=>'nopending'));exit;}
  $reenvio=true;
} else {
  if(!@rename($pend,$dir.'/informe.pdf')){echo json_encode(array('ok'=>false,'e'=>'move'));exit;}
}
if($pl!==''){ @copy($dir.'/informe.pdf',$base.'/informe.pdf'); }
$force=!empty($in['force']);
@file_put_contents($dir.'/publicado.txt',date('c').($reenvio?' REENVIO':($force?' FORZADO':' OK'))."\n",FILE_APPEND);
// Actualizar los datos del cliente (Analisis / Estadisticas) a partir de las fichas subidas
$datos=array('ok'=>false,'e'=>'sinfichas');
$tec=isset($in['n'])?preg_replace('/[^\p{L}\p{N} .@_-]/u','',(string)$in['n']):'';
$ficnuevas=false;
if($reenvio && is_dir($fic)){ foreach(glob($fic.'/*') as $ff){ if(!$lastpub || @filemtime($ff)>$lastpub){ $ficnuevas=true; break; } } }
if($reenvio && !$ficnuevas){
  /* Reenvio puro: los datos ya se actualizaron al publicar; no se tocan */
  $per=trim((string)@file_get_contents($dir.'/periodo.txt'));
  if($per===''){ $hh=glob($dir.'/hist/*.pdf'); if($hh){ usort($hh,function($x,$y){return filemtime($y)-filemtime($x);}); $per=basename($hh[0],'.pdf'); } }
  $datos=array('ok'=>true,'reenvio'=>true,'periodo'=>$per);
}
elseif(!is_file($dj)){ $datos=array('ok'=>false,'e'=>'nodatos'); }
elseif(is_dir($fic)){
  $cmd='python3 /var/www/vibkaptur/scripts/vibk_publish_srv.py '.escapeshellarg($c).' '.escapeshellarg($fic).' '.escapeshellarg($dir.'/informe.pdf').' '.escapeshellarg($dj).' '.escapeshellarg($pl!==''?$pl:'-').' '.escapeshellarg('--tecnico='.$tec).' 2>&1';
  $out=shell_exec($cmd);
  $j=json_decode((string)$out,true);
  $datos=($j===null)?array('ok'=>false,'e'=>'error','raw'=>substr((string)$out,0,300)):$j;
}
// Enlace de descarga directa para el correo al cliente: firmado, sin caducidad, ligado a ESTE informe
$m=(is_array($datos)&&!empty($datos['periodo']))?preg_replace('/[^a-z0-9-]/','',strtolower($datos['periodo'])):date('Y-m');
@mkdir($dir.'/hist',0755,true);
if(!($reenvio && is_file($dir.'/hist/'.$m.'.pdf'))) @copy($dir.'/informe.pdf',$dir.'/hist/'.$m.'.pdf');
@file_put_contents($dir.'/periodo.txt',$m);
$dl='https://vibkaptur.com/api/informe.php?c='.$c.($pl!==''?('&p='.$pl):'').'&m='.$m.'&k='.hash_hmac('sha256','dl|'.$c.'|'.$pl.'|'.$m,$secret);
echo json_encode(array('ok'=>true,'force'=>$force,'reenvio'=>$reenvio,'datos'=>$datos,'dl'=>$dl));
