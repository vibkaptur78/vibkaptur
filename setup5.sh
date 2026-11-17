#!/bin/sh
# ============================================================================
# VIBKAPTUR v5 - SEGURIDAD:
#  - token.php: login con clave CIFRADA (password_verify) + devuelve perfil
#  - datos.php: sirve a cada cliente SOLO sus datos (admin: todos), tras token
#  - clave.php: admin resetea/rota la clave de un usuario (reescribe users.php)
#  Requiere users.php v2 (claves hasheadas) en /private/ y los JSON por cliente
#  en /private/data/<cliente>.json
#  Uso:  curl -sL <raw setup5.sh> | sh
# ============================================================================
BASE=/var/www/vibkaptur
PUB=$BASE/public
mkdir -p "$PUB/api" "$BASE/private/data"
chown -R www-data:www-data "$BASE/private/data" 2>/dev/null || true
# users.php debe ser legible y ESCRIBIBLE por www-data (clave.php lo reescribe)
[ -f "$BASE/private/users.php" ] && { chown www-data:www-data "$BASE/private/users.php"; chmod 640 "$BASE/private/users.php"; }

# ---- token.php v2: valida clave cifrada y emite token + perfil ----
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
if(!password_verify($pass,$u['p'])){echo json_encode(array('ok'=>false));exit;}
$dl=!empty($u['dl']); $up=!empty($u['up']);
$secret=trim(file_get_contents('/var/www/vibkaptur/private/secret.key'));
$exp=time()+5184000; // 60 dias
$flags=($dl?'d':'').($up?'u':'');
$payload=$u['role'].'|'.$u['c'].'|'.$exp.'|'.$flags;
$b64=rtrim(strtr(base64_encode($payload),'+/','-_'),'=');
$sig=hash_hmac('sha256',$b64,$secret);
echo json_encode(array('ok'=>true,'token'=>$b64.'.'.$sig,
  'role'=>$u['role'],'c'=>$u['c'],'plant'=>isset($u['plant'])?$u['plant']:'',
  'name'=>isset($u['name'])?$u['name']:'','puesto'=>isset($u['puesto'])?$u['puesto']:'',
  'dl'=>$dl,'up'=>$up));
PHP

# ---- datos.php: devuelve SOLO los datos del cliente del token (admin: todos) ----
cat > "$PUB/api/datos.php" <<'PHP'
<?php
header('Content-Type: application/json');
$t=isset($_GET['t'])?$_GET['t']:(isset($_POST['t'])?$_POST['t']:'');
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
if(count($p)!=2 || !$secret){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
if(!hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
$a=array_pad(explode('|',base64_decode(strtr($p[0],'-_','+/'))),4,'');
$role=$a[0]; $pc=$a[1]; $exp=intval($a[2]);
if(time()>$exp){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'exp'));exit;}
$dir='/var/www/vibkaptur/private/data/';
if($role==='admin'){
  $out=array();
  foreach(glob($dir.'*.json') as $f){ $out[basename($f,'.json')]=json_decode(file_get_contents($f),true); }
  echo json_encode(array('ok'=>true,'role'=>'admin','data'=>$out)); exit;
}
$cid=preg_replace('/[^a-z0-9_-]/','',strtolower($pc));
$f=$dir.$cid.'.json';
if(!is_file($f)){http_response_code(404);echo json_encode(array('ok'=>false,'e'=>'nodata'));exit;}
echo json_encode(array('ok'=>true,'role'=>$role,'client'=>$cid,'data'=>array($cid=>json_decode(file_get_contents($f),true))));
PHP

# ---- clave.php: admin resetea/rota la clave de un usuario ----
cat > "$PUB/api/clave.php" <<'PHP'
<?php
header('Content-Type: application/json');
$t=isset($_POST['t'])?$_POST['t']:'';
$email=strtolower(trim(isset($_POST['email'])?$_POST['email']:''));
$newpass=isset($_POST['newpass'])?$_POST['newpass']:'';
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
if(count($p)!=2 || !$secret){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
if(!hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'token'));exit;}
$a=array_pad(explode('|',base64_decode(strtr($p[0],'-_','+/'))),4,'');
$role=$a[0]; $exp=intval($a[2]);
if(time()>$exp){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'exp'));exit;}
if($role!=='admin'){http_response_code(403);echo json_encode(array('ok'=>false,'e'=>'noadmin'));exit;}
$uf='/var/www/vibkaptur/private/users.php';
$users=include $uf;
if(!isset($users[$email])){echo json_encode(array('ok'=>false,'e'=>'nouser'));exit;}
if($newpass===''){
  $cs='ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#%+=._-';
  for($i=0;$i<14;$i++){$newpass.=$cs[random_int(0,strlen($cs)-1)];}
}
$users[$email]['p']=password_hash($newpass,PASSWORD_BCRYPT);
$php="<?php\n// VIBKAPTUR usuarios (servidor). Claves cifradas.\nreturn ".var_export($users,true).";\n";
if(@file_put_contents($uf,$php)===false){echo json_encode(array('ok'=>false,'e'=>'write'));exit;}
echo json_encode(array('ok'=>true,'email'=>$email,'newpass'=>$newpass));
PHP

chmod 644 "$PUB/api/token.php" "$PUB/api/datos.php" "$PUB/api/clave.php"
(systemctl reload php8.3-fpm 2>/dev/null || systemctl restart php8.3-fpm 2>/dev/null) || true
echo "OK v5: login cifrado + datos por cliente + reseteo de claves instalados."
echo "Recuerda: subir users.php v2 (hasheado) y los JSON a /private/data/."
