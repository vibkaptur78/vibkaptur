#!/bin/sh
# ============================================================================
# VIBKAPTUR - informes: descarga (tras login) + SUBIDA desde la web.
# v4: subir.php acepta PDF (informe del cliente) Y .docx (Word de termografias,
#     se guarda en reports/<cliente>/termo/incoming/ para procesar despues).
# Usuarios desde /var/www/vibkaptur/private/users.php (aparte, con campo 'up').
# Uso:  curl -sL <raw setup4.sh> | sh
# ============================================================================
BASE=/var/www/vibkaptur
PUB=$BASE/public
mkdir -p "$BASE/reports/elis" "$BASE/reports/otua" "$BASE/reports/otua/termo/incoming" "$BASE/private" "$PUB/api"
chown -R www-data:www-data "$BASE/reports" 2>/dev/null || true  # php-fpm (www-data) debe poder escribir al subir
[ -f "$BASE/private/secret.key" ] || (head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > "$BASE/private/secret.key")
chmod 644 "$BASE/private/secret.key"  # legible por www-data (php-fpm); no accesible por web

# ---- token.php: valida login y emite token firmado (descarga 'd' y/o subida 'u') ----
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
$dl=!empty($u['dl']); $up=!empty($u['up']);
if(!$dl && !$up){echo json_encode(array('ok'=>false,'reason'=>'noperm'));exit;}
$secret=trim(file_get_contents('/var/www/vibkaptur/private/secret.key'));
$exp=time()+5184000; // 60 dias
$flags=($dl?'d':'').($up?'u':'');
$payload=$u['role'].'|'.$u['c'].'|'.$exp.'|'.$flags;
$b64=rtrim(strtr(base64_encode($payload),'+/','-_'),'=');
$sig=hash_hmac('sha256',$b64,$secret);
echo json_encode(array('ok'=>true,'token'=>$b64.'.'.$sig,'dl'=>$dl,'up'=>$up));
PHP

# ---- informe.php: sirve el PDF si el token tiene permiso de descarga ----
cat > "$PUB/api/informe.php" <<'PHP'
<?php
$c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_GET['c'])?$_GET['c']:''));
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
$file='/var/www/vibkaptur/reports/'.$c.'/informe.pdf';
if(!is_file($file)){http_response_code(404);echo 'Informe no disponible';exit;}
header('Content-Type: application/pdf');
header('Content-Disposition: attachment; filename="Informe_'.$c.'.pdf"');
header('Content-Length: '.filesize($file));
readfile($file);
PHP

# ---- subir.php: guarda PDF (informe) o .docx (Word de termografias) si token tiene 'u' ----
cat > "$PUB/api/subir.php" <<'PHP'
<?php
header('Content-Type: application/json');
$t=isset($_POST['t'])?$_POST['t']:'';
$c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_POST['c'])?$_POST['c']:''));
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
if(count($p)!=2 || !$secret){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
if(!hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
$a=array_pad(explode('|',base64_decode(strtr($p[0],'-_','+/'))),4,'');
$exp=intval($a[2]); $flags=$a[3];
if(time()>$exp){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'exp'));exit;}
if(strpos($flags,'u')===false){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'noup'));exit;}
if(!$c){echo json_encode(array('ok'=>false,'e'=>'nocliente'));exit;}
$f = isset($_FILES['file']) ? $_FILES['file'] : (isset($_FILES['pdf']) ? $_FILES['pdf'] : null);
if(!$f || $f['error']!==0){echo json_encode(array('ok'=>false,'e'=>'nofile'));exit;}
$tmp=$f['tmp_name'];
$fh=fopen($tmp,'rb'); $head=fread($fh,4); fclose($fh);
$dir='/var/www/vibkaptur/reports/'.$c;
if(strpos($head,'%PDF')===0){
  // PDF -> informe del cliente (descargable)
  if(!is_dir($dir)) mkdir($dir,0755,true);
  if(!move_uploaded_file($tmp,$dir.'/informe.pdf')){echo json_encode(array('ok'=>false,'e'=>'save'));exit;}
  echo json_encode(array('ok'=>true,'kind'=>'pdf','bytes'=>filesize($dir.'/informe.pdf'),'cliente'=>$c));
  exit;
}
if(substr($head,0,2)==='PK'){
  // .docx (zip) -> Word de termografias, a procesar
  $name=basename(isset($f['name'])?$f['name']:'informe.docx');
  $name=preg_replace('/[^A-Za-z0-9._-]+/','_',$name);
  if(substr(strtolower($name),-5)!=='.docx') $name.='.docx';
  $inc=$dir.'/termo/incoming';
  if(!is_dir($inc)) mkdir($inc,0775,true);
  $dest=$inc.'/'.date('Ymd_His').'_'.$name;
  if(!move_uploaded_file($tmp,$dest)){echo json_encode(array('ok'=>false,'e'=>'save'));exit;}
  echo json_encode(array('ok'=>true,'kind'=>'docx','bytes'=>filesize($dest),'cliente'=>$c,'file'=>basename($dest)));
  exit;
}
echo json_encode(array('ok'=>false,'e'=>'tipo'));
PHP

# ---- limites de tamano (Word de termografias puede pesar ~30 MB) ----
cat > "$PUB/api/.user.ini" <<'INI'
upload_max_filesize = 40M
post_max_size = 41M
INI
printf 'client_max_body_size 42M;\n' > /etc/nginx/conf.d/vibk_upload.conf

chmod 644 "$PUB/api/token.php" "$PUB/api/informe.php" "$PUB/api/subir.php" "$PUB/api/.user.ini"

(systemctl reload php8.3-fpm 2>/dev/null || systemctl restart php8.3-fpm 2>/dev/null) || true
if nginx -t 2>/dev/null; then systemctl reload nginx 2>/dev/null || true; echo "nginx recargado"; else echo "AVISO: revisa nginx -t"; fi
echo "OK v4: descarga + subida (PDF e .docx de termografias) instaladas."
