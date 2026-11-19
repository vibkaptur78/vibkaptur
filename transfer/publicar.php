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
if(!is_file($pend)){echo json_encode(array('ok'=>false,'e'=>'nopending'));exit;}
if(!@rename($pend,$dir.'/informe.pdf')){echo json_encode(array('ok'=>false,'e'=>'move'));exit;}
if($pl!==''){ @copy($dir.'/informe.pdf',$base.'/informe.pdf'); }
$force=!empty($in['force']);
@file_put_contents($dir.'/publicado.txt',date('c').($force?' FORZADO':' OK')."\n",FILE_APPEND);
// Actualizar los datos del cliente (Analisis / Estadisticas) a partir de las fichas subidas
$datos=array('ok'=>false,'e'=>'sinfichas');
$fic=$dir.'/fichas'; $dj='/var/www/vibkaptur/private/data/'.$c.'.json';
$tec=isset($in['n'])?preg_replace('/[^\p{L}\p{N} .@_-]/u','',(string)$in['n']):'';
if(!is_file($dj)){ $datos=array('ok'=>false,'e'=>'nodatos'); }
elseif(is_dir($fic)){
  $cmd='python3 /var/www/vibkaptur/scripts/vibk_publish_srv.py '.escapeshellarg($c).' '.escapeshellarg($fic).' '.escapeshellarg($dir.'/informe.pdf').' '.escapeshellarg($dj).' '.escapeshellarg($pl!==''?$pl:'-').' '.escapeshellarg('--tecnico='.$tec).' 2>&1';
  $out=shell_exec($cmd);
  $j=json_decode((string)$out,true);
  $datos=($j===null)?array('ok'=>false,'e'=>'error','raw'=>substr((string)$out,0,300)):$j;
}
echo json_encode(array('ok'=>true,'force'=>$force,'datos'=>$datos));
