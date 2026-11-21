<?php
// VIBKAPTUR · alta, baja y listado de usuarios (solo administrador). Las claves se guardan cifradas (bcrypt).
header('Content-Type: application/json');
function out($a){echo json_encode($a);exit;}
$t=isset($_POST['t'])?$_POST['t']:'';
$secret=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$p=explode('.',$t);
if(count($p)!=2 || !$secret){http_response_code(403);out(array('ok'=>false,'e'=>'token'));}
if(!hash_equals(hash_hmac('sha256',$p[0],$secret),$p[1])){http_response_code(403);out(array('ok'=>false,'e'=>'token'));}
$a=array_pad(explode('|',base64_decode(strtr($p[0],'-_','+/'))),4,'');
if(time()>intval($a[2])){http_response_code(403);out(array('ok'=>false,'e'=>'exp'));}
if($a[0]!=='admin'){http_response_code(403);out(array('ok'=>false,'e'=>'noadmin'));}
$uf='/var/www/vibkaptur/private/users.php';
$users=@include $uf;
if(!is_array($users)) out(array('ok'=>false,'e'=>'nousers'));
function guardar($uf,$users){
  @copy($uf,$uf.'.bak');
  $php="<?php\n// VIBKAPTUR usuarios (servidor). Claves cifradas.\nreturn ".var_export($users,true).";\n";
  $tmp=$uf.'.tmp'; $ok=false;
  if(@file_put_contents($tmp,$php,LOCK_EX)!==false){
    @chmod($tmp,fileperms($uf)&0777);
    $ok=@rename($tmp,$uf); if(!$ok) @unlink($tmp);
  }
  if(!$ok && @file_put_contents($uf,$php,LOCK_EX)===false) return false;
  if(function_exists('opcache_invalidate')) @opcache_invalidate($uf,true);
  return true;
}
function publico($email,$u){
  return array('email'=>$email,'name'=>isset($u['name'])?$u['name']:'','role'=>isset($u['role'])?$u['role']:'',
    'c'=>isset($u['c'])?$u['c']:'','plant'=>isset($u['plant'])?$u['plant']:'','puesto'=>isset($u['puesto'])?$u['puesto']:'',
    'dl'=>!empty($u['dl']),'up'=>!empty($u['up']));
}
$op=isset($_POST['a'])?$_POST['a']:'list';
if($op==='list'){
  $l=array(); foreach($users as $e=>$u){$l[]=publico($e,$u);}
  out(array('ok'=>true,'users'=>$l));
}
$email=strtolower(trim(isset($_POST['email'])?$_POST['email']:''));
if($op==='baja'){
  if(!isset($users[$email])) out(array('ok'=>false,'e'=>'nouser'));
  if(isset($users[$email]['role']) && $users[$email]['role']==='admin') out(array('ok'=>false,'e'=>'esadmin'));
  unset($users[$email]);
  if(!guardar($uf,$users)) out(array('ok'=>false,'e'=>'write'));
  out(array('ok'=>true,'email'=>$email));
}
if($op==='alta'){
  if(!filter_var($email,FILTER_VALIDATE_EMAIL) || strlen($email)>120) out(array('ok'=>false,'e'=>'email'));
  if(isset($users[$email])) out(array('ok'=>false,'e'=>'existe'));
  $role=isset($_POST['role'])?$_POST['role']:'client';
  $name=trim(strip_tags(isset($_POST['name'])?$_POST['name']:'')); if(strlen($name)>80) $name=substr($name,0,80);
  $puesto=trim(strip_tags(isset($_POST['puesto'])?$_POST['puesto']:'')); if(strlen($puesto)>60) $puesto=substr($puesto,0,60);
  if($name==='') out(array('ok'=>false,'e'=>'nombre'));
  if($role==='client'){
    $c=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_POST['c'])?$_POST['c']:''));
    $pl=preg_replace('/[^a-z0-9_-]/','',strtolower(isset($_POST['plant'])?$_POST['plant']:''));
    $df='/var/www/vibkaptur/private/data/'.$c.'.json';
    if($c==='' || !is_file($df)) out(array('ok'=>false,'e'=>'cliente'));
    if($pl!==''){
      $d=json_decode(@file_get_contents($df),true); $okp=false;
      if(is_array($d) && isset($d['plants'])) foreach($d['plants'] as $x){ if(isset($x['id']) && $x['id']===$pl) $okp=true; }
      if(!$okp) out(array('ok'=>false,'e'=>'planta'));
    }
    $u=array('role'=>'client','c'=>$c,'name'=>$name,'puesto'=>$puesto,'dl'=>true,'up'=>false);
    if($pl!=='') $u['plant']=$pl;
  } else if($role==='tecnico'){
    // se copia la configuracion de un tecnico que ya exista, para que tenga exactamente los mismos permisos
    $tpl=null; foreach($users as $x){ if(isset($x['role']) && $x['role']==='tecnico'){ $tpl=$x; break; } }
    if($tpl===null) out(array('ok'=>false,'e'=>'sintecnico'));
    $u=$tpl; $u['name']=$name; $u['puesto']=$puesto;
  } else out(array('ok'=>false,'e'=>'rol'));
  $newpass=isset($_POST['newpass'])?trim($_POST['newpass']):'';
  if($newpass!=='' && strlen($newpass)<10) out(array('ok'=>false,'e'=>'clavecorta'));
  if($newpass===''){
    $cs='ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#%+=._-';
    for($i=0;$i<14;$i++){$newpass.=$cs[random_int(0,strlen($cs)-1)];}
  }
  $u['p']=password_hash($newpass,PASSWORD_BCRYPT);
  $users[$email]=$u;
  if(!guardar($uf,$users)) out(array('ok'=>false,'e'=>'write'));
  out(array('ok'=>true,'email'=>$email,'newpass'=>$newpass,'user'=>publico($email,$u)));
}
out(array('ok'=>false,'e'=>'op'));
