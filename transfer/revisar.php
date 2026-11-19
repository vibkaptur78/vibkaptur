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
$dir='/var/www/vibkaptur/reports/'.$c; $pdf=$dir.'/pending.pdf'; $fic=$dir.'/fichas';
if(!is_file($pdf)){echo json_encode(array('ok'=>false,'e'=>'nopdf'));exit;}
if(!is_dir($fic)){echo json_encode(array('ok'=>false,'e'=>'nofichas'));exit;}
$cmd='python3 /var/www/vibkaptur/scripts/vibk_validate_srv.py '.escapeshellarg($pdf).' '.escapeshellarg($fic).' '.escapeshellarg(ucfirst($c)).' Vibraciones '.escapeshellarg(date('m/Y')).' 2>&1';
$out=shell_exec($cmd);
$j=json_decode($out,true);
if($j===null){echo json_encode(array('ok'=>false,'e'=>'val','raw'=>substr((string)$out,0,500)));exit;}
$n=isset($j['findings'])?count($j['findings']):0;
$html=isset($j['aviso_html'])?$j['aviso_html']:'';
$per=date('m/Y'); $cli=ucfirst($c);
$subject=$n>0 ? ('VIBKAPTUR - Revision '.$cli.' ('.$per.') - '.$n.' punto(s) a revisar') : ('VIBKAPTUR - Revision '.$cli.' ('.$per.') - correcto, listo para publicar');
$KEY=''; $avs=@file_get_contents(__DIR__.'/aviso.php');
if($avs && preg_match("/\\\$KEY\\s*=\\s*'([^']+)'/",$avs,$mk)) $KEY=$mk[1];
if(!$KEY){echo json_encode(array('ok'=>false,'e'=>'nokey'));exit;}
$to=array(array('email'=>$email),array('email'=>'pedro.ortega@ingenorsistemas.com'));
$body=array('sender'=>array('email'=>'avisos@vibkaptur.com','name'=>'VIBKAPTUR - Ingenor'),'to'=>$to,'subject'=>$subject,'htmlContent'=>$html);
$ch=curl_init('https://api.brevo.com/v3/smtp/email');
curl_setopt_array($ch,array(CURLOPT_RETURNTRANSFER=>true,CURLOPT_POST=>true,CURLOPT_HTTPHEADER=>array('accept: application/json','api-key: '.$KEY,'content-type: application/json'),CURLOPT_POSTFIELDS=>json_encode($body),CURLOPT_TIMEOUT=>20));
$resp=curl_exec($ch); $code=curl_getinfo($ch,CURLINFO_HTTP_CODE); curl_close($ch);
echo json_encode(array('ok'=>true,'n'=>$n,'mail'=>$code,'to'=>array($email,'pedro.ortega@ingenorsistemas.com')));
