<?php
header('Content-Type: application/json');
$in=json_decode(file_get_contents('php://input'),true);
$t=isset($in['t'])?$in['t']:'';
$c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($in['c'])?$in['c']:''));
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
if(count($p)!=2 || !$secret){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
if(!hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
$a=array_pad(explode('|',base64_decode(strtr($p[0],'-_','+/'))),4,'');
$email=$a[0]; $exp=intval($a[2]); $flags=$a[3];
if(time()>$exp){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'exp'));exit;}
if(strpos($flags,'u')===false){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'noup'));exit;}
if(!$c){echo json_encode(array('ok'=>false,'e'=>'nocliente'));exit;}
$dir='/var/www/vibkaptur/reports/'.$c; $pdf=$dir.'/informe.pdf'; $fic=$dir.'/fichas';
if(!is_file($pdf)){echo json_encode(array('ok'=>false,'e'=>'nopdf'));exit;}
if(!is_dir($fic)){echo json_encode(array('ok'=>false,'e'=>'nofichas'));exit;}
$recips=$email.',pedro.ortega@ingenorsistemas.com';
$cmd='python3 /var/www/vibkaptur/scripts/vibk_validate_srv.py '.escapeshellarg($pdf).' '.escapeshellarg($fic).' '.escapeshellarg(ucfirst($c)).' Vibraciones '.escapeshellarg(date('m/Y')).' '.escapeshellarg($recips).' 2>&1';
$out=shell_exec($cmd);
$j=json_decode($out,true);
if($j===null){echo json_encode(array('ok'=>false,'e'=>'val','raw'=>substr((string)$out,0,500)));exit;}
$n=isset($j['findings'])?count($j['findings']):0;
echo json_encode(array('ok'=>true,'n'=>$n,'enviado'=>isset($j['enviado'])?$j['enviado']:null));
