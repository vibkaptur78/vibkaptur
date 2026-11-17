#!/bin/sh
# ============================================================================
# VIBKAPTUR - puerta de descarga de informes (tras login, carpeta protegida)
# Crea: carpetas de informes (no publicas), secret, token.php e informe.php.
# Los usuarios se cargan desde /var/www/vibkaptur/private/users.php (aparte).
# Uso:  curl -sL <raw setup3.sh> | sh
# ============================================================================
BASE=/var/www/vibkaptur
PUB=$BASE/public
mkdir -p "$BASE/reports/elis" "$BASE/reports/otua" "$BASE/private" "$PUB/api"
[ -f "$BASE/private/secret.key" ] || (head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > "$BASE/private/secret.key")
chmod 600 "$BASE/private/secret.key"

cat > "$PUB/api/token.php" <<'PHP'
<?php
header('Content-Type: application/json');
$in=json_decode(file_get_contents('php://input'),true);
$email=strtolower(trim(isset($in['email'])?$in['email']:''));
$pass=isset($in['password'])?$in['password']:'';
$uf='/var/www/vibkaptur/private/users.php';
if(!is_file($uf)){echo json_encode(array('ok'=>false,'reason'=>'nousers'));exit;}
$users=include $uf;
if(!isset($users[$email])){echo json_encode(array('ok'=>false));exit;}
$u=$users[$email];
if(!hash_equals((string)$u['p'],(string)$pass)){echo json_encode(array('ok'=>false));exit;}
if(empty($u['dl'])){echo json_encode(array('ok'=>false,'reason'=>'nodl'));exit;}
$secret=trim(file_get_contents('/var/www/vibkaptur/private/secret.key'));
$exp=time()+5184000; // 60 dias
$payload=$u['role'].'|'.$u['c'].'|'.$exp;
$b64=rtrim(strtr(base64_encode($payload),'+/','-_'),'=');
$sig=hash_hmac('sha256',$b64,$secret);
echo json_encode(array('ok'=>true,'token'=>$b64.'.'.$sig));
PHP

cat > "$PUB/api/informe.php" <<'PHP'
<?php
$c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_GET['c'])?$_GET['c']:''));
$t=isset($_GET['t'])?$_GET['t']:'';
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
if(count($p)!=2 || !$secret){http_response_code(403);echo 'Acceso denegado';exit;}
if(!hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);echo 'Token no valido';exit;}
$pl=base64_decode(strtr($p[0],'-_','+/'));
$parts=array_pad(explode('|',$pl),3,'');
$role=$parts[0]; $pc=$parts[1]; $exp=intval($parts[2]);
if(time()>$exp){http_response_code(403);echo 'Sesion caducada, vuelve a entrar';exit;}
if($role!=='admin' && $pc!==$c){http_response_code(403);echo 'No autorizado';exit;}
$file='/var/www/vibkaptur/reports/'.$c.'/informe.pdf';
if(!is_file($file)){http_response_code(404);echo 'Informe no disponible';exit;}
header('Content-Type: application/pdf');
header('Content-Disposition: attachment; filename="Informe_'.$c.'.pdf"');
header('Content-Length: '.filesize($file));
readfile($file);
PHP

chmod 644 "$PUB/api/token.php" "$PUB/api/informe.php"
echo "OK: gate instalada (token.php + informe.php + carpetas). Ahora crea users.php."
