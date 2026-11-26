import subprocess,shutil,time,sys,os,base64
ROOT='/var/www/vibkaptur'; TEST=len(sys.argv)>1
if TEST: ROOT=sys.argv[1]
API=ROOT+'/public/api' if not TEST else ROOT+'/api'; PRIV=ROOT+'/private'
def fx(t): return t.replace('/var/www/vibkaptur',ROOT) if TEST else t
LOG=fx(base64.b64decode('PD9waHAKLy8gVklCS0FQVFVSIMK3IHJlZ2lzdHJvIGRlIGRlc2NhcmdhcyBkZSBpbmZvcm1lcyAoc29sbyBjbGllbnRlcyB5IGVubGFjZXMgZGVsIGNvcnJlbzsgbm8gZWwgcGVyc29uYWwgZGUgSW5nZW5vcikKZnVuY3Rpb24gdmtfZGxfbG9nKCRjLCRwbCwkbSwka2luZCwkcm9sZSwkd2hvLCR2aWEpewogIGlmKCRyb2xlPT09J2FkbWluJyB8fCAkcm9sZT09PSd0ZWNuaWNvJykgcmV0dXJuOwogIGlmKGlzc2V0KCRfU0VSVkVSWydSRVFVRVNUX01FVEhPRCddKSAmJiAkX1NFUlZFUlsnUkVRVUVTVF9NRVRIT0QnXSE9PSdHRVQnKSByZXR1cm47CiAgJGY9Jy92YXIvd3d3L3ZpYmthcHR1ci9wcml2YXRlL2Rlc2Nhcmdhcy5sb2cnOwogICRzZWM9dHJpbSgoc3RyaW5nKUBmaWxlX2dldF9jb250ZW50cygnL3Zhci93d3cvdmlia2FwdHVyL3ByaXZhdGUvc2VjcmV0LmtleScpKTsKICAvLyBodWVsbGEgY29ydGEgeSBubyByZXZlcnNpYmxlIGRlbCBvcmlnZW46IHNvbG8gcGFyYSBubyBjb250YXIgZG9zIHZlY2VzIGxhIG1pc21hIGRlc2NhcmdhCiAgJGg9c3Vic3RyKGhhc2hfaG1hYygnc2hhMjU2Jyxpc3NldCgkX1NFUlZFUlsnUkVNT1RFX0FERFInXSk/KHN0cmluZykkX1NFUlZFUlsnUkVNT1RFX0FERFInXTonJywkc2VjKSwwLDEwKTsKICAkbm93PXRpbWUoKTsgJHRhaWw9Jyc7CiAgJGZwPUBmb3BlbigkZiwncicpOyBpZigkZnApeyAkc3o9KGludClAZmlsZXNpemUoJGYpOyBAZnNlZWsoJGZwLG1heCgwLCRzei02MDAwKSk7ICR0YWlsPShzdHJpbmcpQGZyZWFkKCRmcCw2MDAwKTsgQGZjbG9zZSgkZnApOyB9CiAgZm9yZWFjaChhcnJheV9yZXZlcnNlKGV4cGxvZGUoIlxuIix0cmltKCR0YWlsKSkpIGFzICRsbil7CiAgICAkaj1qc29uX2RlY29kZSgkbG4sdHJ1ZSk7IGlmKCFpc19hcnJheSgkaikgfHwgIWlzc2V0KCRqWyd0J10pKSBjb250aW51ZTsKICAgIGlmKCRub3ctaW50dmFsKCRqWyd0J10pPjEyMCkgYnJlYWs7CiAgICBpZigkalsnaCddPT09JGggJiYgJGpbJ2MnXT09PSRjICYmICRqWydwJ109PT0kcGwgJiYgJGpbJ20nXT09PSRtICYmICRqWydrJ109PT0ka2luZCAmJiAkalsndyddPT09JHdobykgcmV0dXJuOwogIH0KICBAZmlsZV9wdXRfY29udGVudHMoJGYsanNvbl9lbmNvZGUoYXJyYXkoJ3QnPT4kbm93LCdjJz0+KHN0cmluZykkYywncCc9PihzdHJpbmcpJHBsLCdtJz0+KHN0cmluZykkbSwnayc9PihzdHJpbmcpJGtpbmQsJ3cnPT4oc3RyaW5nKSR3aG8sJ3YnPT4oc3RyaW5nKSR2aWEsJ2gnPT4kaCkpLiJcbiIsRklMRV9BUFBFTkR8TE9DS19FWCk7Cn0K').decode('utf-8')); DES=fx(base64.b64decode('PD9waHAKLy8gVklCS0FQVFVSIMK3IGRlc2NhcmdhcyBkZSBpbmZvcm1lcyBkZSB1biBjbGllbnRlIChzb2xvIGFkbWluaXN0cmFkb3IpCmhlYWRlcignQ29udGVudC1UeXBlOiBhcHBsaWNhdGlvbi9qc29uJyk7CiRpbj1qc29uX2RlY29kZSgoc3RyaW5nKWZpbGVfZ2V0X2NvbnRlbnRzKCdwaHA6Ly9pbnB1dCcpLHRydWUpOyBpZighaXNfYXJyYXkoJGluKSkgJGluPWFycmF5KCk7CiR0PWlzc2V0KCRpblsndCddKT8oc3RyaW5nKSRpblsndCddOicnOwokYz1wcmVnX3JlcGxhY2UoJy9bXmEtejAtOV8tXS8nLCcnLHN0cnRvbG93ZXIoaXNzZXQoJGluWydjJ10pPyhzdHJpbmcpJGluWydjJ106JycpKTsKJHNlY3JldD10cmltKChzdHJpbmcpQGZpbGVfZ2V0X2NvbnRlbnRzKCcvdmFyL3d3dy92aWJrYXB0dXIvcHJpdmF0ZS9zZWNyZXQua2V5JykpOwokcD1leHBsb2RlKCcuJywkdCk7CmlmKGNvdW50KCRwKSE9MiB8fCAkc2VjcmV0PT09JycgfHwgIWhhc2hfZXF1YWxzKGhhc2hfaG1hYygnc2hhMjU2JywkcFswXSwkc2VjcmV0KSwkcFsxXSkpe2h0dHBfcmVzcG9uc2VfY29kZSg0MDMpO2VjaG8ganNvbl9lbmNvZGUoYXJyYXkoJ29rJz0+ZmFsc2UsJ2UnPT4ndG9rZW4nKSk7ZXhpdDt9CiRhPWFycmF5X3BhZChleHBsb2RlKCd8Jywoc3RyaW5nKWJhc2U2NF9kZWNvZGUoc3RydHIoJHBbMF0sJy1fJywnKy8nKSkpLDYsJycpOwppZih0aW1lKCk+aW50dmFsKCRhWzJdKSl7aHR0cF9yZXNwb25zZV9jb2RlKDQwMyk7ZWNobyBqc29uX2VuY29kZShhcnJheSgnb2snPT5mYWxzZSwnZSc9PidleHAnKSk7ZXhpdDt9CmlmKCRhWzBdIT09J2FkbWluJyl7aHR0cF9yZXNwb25zZV9jb2RlKDQwMyk7ZWNobyBqc29uX2VuY29kZShhcnJheSgnb2snPT5mYWxzZSwnZSc9Pidub2FkbWluJykpO2V4aXQ7fQppZigkYz09PScnKXtlY2hvIGpzb25fZW5jb2RlKGFycmF5KCdvayc9PmZhbHNlLCdlJz0+J25vY2xpZW50ZScpKTtleGl0O30KJHVzPUBpbmNsdWRlICcvdmFyL3d3dy92aWJrYXB0dXIvcHJpdmF0ZS91c2Vycy5waHAnOyBpZighaXNfYXJyYXkoJHVzKSkgJHVzPWFycmF5KCk7CiR0b3Q9MDsgJGxhc3Q9MDsgJHBlcj1hcnJheSgpOyAkaW5mPWFycmF5KCk7CiRmcD1AZm9wZW4oJy92YXIvd3d3L3ZpYmthcHR1ci9wcml2YXRlL2Rlc2Nhcmdhcy5sb2cnLCdyJyk7CmlmKCRmcCl7IHdoaWxlKCgkbG49ZmdldHMoJGZwKSkhPT1mYWxzZSl7CiAgJGo9anNvbl9kZWNvZGUoJGxuLHRydWUpOyBpZighaXNfYXJyYXkoJGopIHx8ICFpc3NldCgkalsnYyddKSB8fCAkalsnYyddIT09JGMpIGNvbnRpbnVlOwogICR0b3QrKzsgJHRzPWludHZhbCgkalsndCddKTsgaWYoJHRzPiRsYXN0KSAkbGFzdD0kdHM7CiAgJHc9KCRqWyd2J109PT0nZW5sYWNlJyB8fCAkalsndyddPT09JycpPycnOiRqWyd3J107CiAgaWYoIWlzc2V0KCRwZXJbJHddKSkgJHBlclskd109YXJyYXkoJ3cnPT4kdywnbic9PjAsJ2xhc3QnPT4wLCduYW1lJz0+KCR3IT09JycgJiYgaXNzZXQoJHVzWyR3XVsnbmFtZSddKSk/JHVzWyR3XVsnbmFtZSddOicnLCdiYWphJz0+KCR3IT09JycgJiYgIWlzc2V0KCR1c1skd10pKSk7CiAgJHBlclskd11bJ24nXSsrOyBpZigkdHM+JHBlclskd11bJ2xhc3QnXSkgJHBlclskd11bJ2xhc3QnXT0kdHM7CiAgJGs9JGpbJ3AnXS4nfCcuJGpbJ20nXS4nfCcuJGpbJ2snXTsKICBpZighaXNzZXQoJGluZlska10pKSAkaW5mWyRrXT1hcnJheSgncCc9PiRqWydwJ10sJ20nPT4kalsnbSddLCdrJz0+JGpbJ2snXSwnbic9PjAsJ2xhc3QnPT4wKTsKICAkaW5mWyRrXVsnbiddKys7IGlmKCR0cz4kaW5mWyRrXVsnbGFzdCddKSAkaW5mWyRrXVsnbGFzdCddPSR0czsKfSBmY2xvc2UoJGZwKTsgfQokcGVyPWFycmF5X3ZhbHVlcygkcGVyKTsgdXNvcnQoJHBlcixmdW5jdGlvbigkeCwkeSl7cmV0dXJuICR5WydsYXN0J10tJHhbJ2xhc3QnXTt9KTsKJGluZj1hcnJheV92YWx1ZXMoJGluZik7IHVzb3J0KCRpbmYsZnVuY3Rpb24oJHgsJHkpe3JldHVybiAkeVsnbGFzdCddLSR4WydsYXN0J107fSk7CmVjaG8ganNvbl9lbmNvZGUoYXJyYXkoJ29rJz0+dHJ1ZSwndG90YWwnPT4kdG90LCdsYXN0Jz0+JGxhc3QsJ3BlcnNvbmFzJz0+JHBlciwnaW5mb3JtZXMnPT5hcnJheV9zbGljZSgkaW5mLDAsMjQpLCdkZXNkZSc9PihpbnQpQGZpbGVjdGltZSgnL3Zhci93d3cvdmlia2FwdHVyL3ByaXZhdGUvZGVzY2FyZ2FzLmxvZycpKSk7Cg==').decode('utf-8'))
INC="@include_once '/var/www/vibkaptur/private/vk_log.php'; if(function_exists('vk_dl_log')) "
INC=fx(INC)
out={}
# informe.php
F=API+'/informe.php'; s=open(F,encoding='utf-8').read()
A1="  header('Content-Type: application/pdf');\n  header('Content-Disposition: attachment; filename=\"Informe_'"
A2="\nheader('Content-Type: application/pdf');\nheader('Content-Disposition: attachment; filename=\"'.$name.'.pdf\"');"
if 'vk_dl_log' in s: pass
elif 'un mes concreto' not in s or s.count(A1)!=1 or s.count(A2)!=1: print('NO HE TOCADO NADA: informe.php no es como esperaba'); sys.exit()
else:
    s=s.replace(A1,"  "+INC+"vk_dl_log($c,$pl,$m,'vib','','','enlace');\n"+A1)
    s=s.replace(A2,"\n$pm=($m!=='')?$m:trim((string)@file_get_contents($d.'/periodo.txt'));\n"+INC+"vk_dl_log($c,($d!==$base)?$pl:'',$pm,'vib',$role,isset($a[4])?$a[4]:'','sesion');"+A2)
    out[F]=s
# termodl.php
F=API+'/termodl.php'; s=open(F,encoding='utf-8').read()
A3="header('Content-Type: application/pdf');"
if 'vk_dl_log' in s: pass
elif s.count(A3)!=1: print('NO HE TOCADO NADA: termodl.php no es como esperaba'); sys.exit()
else: out[F]=s.replace(A3,INC+"vk_dl_log($c,$pl,$m,'termo',isset($a)?$a[0]:'',isset($a)?$a[4]:'',($k!=='')?'enlace':'sesion');\n"+A3)
out[API+'/descargas.php']=DES; out[PRIV+'/vk_log.php']=LOG
tmp={}
for F,txt in out.items():
    T=F+'.nuevo.php'; open(T,'w',encoding='utf-8').write(txt)
    r=subprocess.run(['php','-l',T],capture_output=True,text=True)
    tmp[F]=T
    if r.returncode!=0:
        for x in tmp.values(): os.path.exists(x) and os.remove(x)
        print('NO HE TOCADO NADA: error de sintaxis en',os.path.basename(F),r.stdout); sys.exit()
ref=os.stat(API+'/informe.php'); refp=os.stat(PRIV+'/vk_comun.php') if os.path.exists(PRIV+'/vk_comun.php') else ref
if not TEST: os.makedirs('/root/vibk_api_antes',exist_ok=True)
for F,T in tmp.items():
    if os.path.exists(F) and not TEST: shutil.copy2(F,'/root/vibk_api_antes/'+os.path.basename(F)+'.'+time.strftime('%Y%m%d_%H%M'))
    st=refp if F.startswith(PRIV) else ref
    os.replace(T,F); os.chown(F,st.st_uid,st.st_gid); os.chmod(F,st.st_mode)
L=PRIV+'/descargas.log'
if not os.path.exists(L): open(L,'a').close()
u=os.stat(PRIV+'/users.php'); os.chown(L,u.st_uid,u.st_gid); os.chmod(L,0o640)
print('CONTADOR DE DESCARGAS INSTALADO')
if not TEST:
    r=subprocess.run(['sudo','-u','www-data','sh','-c','test -w '+L+' && echo ESCRITURA: CORRECTA || echo ESCRITURA: FALLA'],capture_output=True,text=True); print((r.stdout or r.stderr).strip())
