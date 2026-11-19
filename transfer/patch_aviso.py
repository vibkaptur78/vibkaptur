import sys,shutil,time
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
if 'VIBK_AUTH' in s: print('aviso.php ya estaba protegido'); sys.exit(0)
blk = r"""<?php
/* VIBK_AUTH: solo envia si la peticion trae un token de sesion valido de personal de Ingenor */
$__in=json_decode(file_get_contents('php://input'),true);
$__t=(is_array($__in)&&isset($__in['t']))?(string)$__in['t']:'';
$__sec=trim(@file_get_contents('/var/www/vibkaptur/private/secret.key'));
$__p=explode('.',$__t); $__ok=false;
if(count($__p)==2 && $__sec && hash_equals(hash_hmac('sha256',$__p[0],$__sec),$__p[1])){
  $__a=array_pad(explode('|',base64_decode(strtr($__p[0],'-_','+/'))),4,'');
  if(time()<=intval($__a[2]) && ($__a[0]==='admin' || strpos($__a[3],'u')!==false)) $__ok=true;
}
if(!$__ok){ http_response_code(403); header('Content-Type: application/json'); echo json_encode(array('ok'=>false,'error'=>'auth')); exit; }
"""
i=s.find('<?php')
if i!=0: print('ERROR: aviso.php no empieza por <?php'); sys.exit(1)
shutil.copy(p,p+'.bak-'+time.strftime('%Y%m%d-%H%M%S'))
open(p,'w',encoding='utf-8').write(blk+s[5:])
print('aviso.php protegido')
