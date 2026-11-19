<?php
/* Guarda el analisis estadistico (HTML generado por la plataforma al publicar) y devuelve su enlace firmado */
header('Content-Type: application/json');
$in=json_decode(file_get_contents('php://input'),true);
$t=isset($in['t'])?$in['t']:'';
$c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($in['c'])?$in['c']:''));
$pl=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($in['p'])?$in['p']:''));
$m=preg_replace('/[^a-z0-9-]/','',strtolower(isset($in['m'])?$in['m']:''));
$html=isset($in['html'])?(string)$in['html']:'';
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
if(count($p)!=2 || !$secret || !hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
$a=array_pad(explode('|',base64_decode(strtr($p[0],'-_','+/'))),4,'');
if(time()>intval($a[2])){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'exp'));exit;}
if(strpos($a[3],'u')===false){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'noup'));exit;}
if($c==='' || $m==='' || strlen($html)<200 || strlen($html)>3000000){echo json_encode(array('ok'=>false,'e'=>'datos'));exit;}
$base='/var/www/vibkaptur/reports/'.$c;
if(!is_dir($base)){echo json_encode(array('ok'=>false,'e'=>'nocliente'));exit;}
$dir=$base.($pl!==''?('/'.$pl):'').'/hist';
@mkdir($dir,0755,true);
if(@file_put_contents($dir.'/'.$m.'_stats.html',$html)===false){echo json_encode(array('ok'=>false,'e'=>'write'));exit;}
$url='https://vibkaptur.com/api/informe.php?c='.$c.($pl!==''?('&p='.$pl):'').'&m='.$m.'&s=1&k='.hash_hmac('sha256','st|'.$c.'|'.$pl.'|'.$m,$secret);
echo json_encode(array('ok'=>true,'url'=>$url));
