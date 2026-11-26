import subprocess,shutil,time,sys,os
API='/var/www/vibkaptur/public/api'
if len(sys.argv)>1: API=sys.argv[1]
FN='''function vk_texto($h){ $h=preg_replace('#<(style|script|head)[^>]*>.*?</\\\\1>#is','',(string)$h); $h=preg_replace('#<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>#is','$2: $1',$h); $h=preg_replace('#<(br|/p|/div|/tr|/h[1-6]|/li|/table)[^>]*>#i',"\\n",$h); $h=html_entity_decode(strip_tags($h),ENT_QUOTES,'UTF-8'); $h=preg_replace('/[ \\t\\x{00A0}]+/u',' ',$h); $h=preg_replace('/ *\\n */',"\\n",$h); return trim(preg_replace('/\\n{3,}/',"\\n\\n",$h)); }
'''
A="'subject'=>$subject,'htmlContent'=>$html);"
B="'subject'=>$subject,'htmlContent'=>$html,'textContent'=>vk_texto($html));"
F=API+'/resumen.php'; s=open(F,encoding='utf-8').read()
if 'vk_texto' in s: print('YA ESTABA, no he tocado nada'); sys.exit()
if s.count(A)!=1 or not s.startswith('<?php'): print('NO HE TOCADO NADA: resumen.php no es como esperaba'); sys.exit()
i=s.index('\n')+1
n=s[:i]+FN+s[i:].replace(A,B)
T=F+'.nuevo.php'; open(T,'w',encoding='utf-8').write(n)
r=subprocess.run(['php','-l',T],capture_output=True,text=True)
if r.returncode!=0: os.remove(T); print('NO HE TOCADO NADA: error de sintaxis',r.stdout); sys.exit()
if len(sys.argv)==1:
    os.makedirs('/root/vibk_api_antes',exist_ok=True); shutil.copy2(F,'/root/vibk_api_antes/resumen.php.'+time.strftime('%Y%m%d_%H%M'))
st=os.stat(F); os.replace(T,F); os.chown(F,st.st_uid,st.st_gid); os.chmod(F,st.st_mode)
print('RESUMEN: VERSION EN TEXTO ANADIDA')
