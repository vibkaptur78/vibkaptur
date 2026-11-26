import subprocess,shutil,time,sys,os,base64
API='/var/www/vibkaptur/public/api'
if len(sys.argv)>1: API=sys.argv[1]
NEW=base64.b64decode('PD9waHAKLy8gVklCS0FQVFVSIMK3IGxpc3RhIGRlIGluZm9ybWVzIGVuIFBERiBxdWUgZXhpc3RlbiBkZSB2ZXJkYWQgZW4gZWwgc2Vydmlkb3IgKHBvciBwbGFudGEgeSBtZXMpCmhlYWRlcignQ29udGVudC1UeXBlOiBhcHBsaWNhdGlvbi9qc29uJyk7CiRpbj1qc29uX2RlY29kZSgoc3RyaW5nKWZpbGVfZ2V0X2NvbnRlbnRzKCdwaHA6Ly9pbnB1dCcpLHRydWUpOyBpZighaXNfYXJyYXkoJGluKSkgJGluPWFycmF5KCk7CiR0PWlzc2V0KCRpblsndCddKT8oc3RyaW5nKSRpblsndCddOicnOwokYz1wcmVnX3JlcGxhY2UoJy9bXmEtejAtOV8tXS8nLCcnLHN0cnRvbG93ZXIoaXNzZXQoJGluWydjJ10pPyhzdHJpbmcpJGluWydjJ106JycpKTsKJHNlY3JldD10cmltKChzdHJpbmcpQGZpbGVfZ2V0X2NvbnRlbnRzKCcvdmFyL3d3dy92aWJrYXB0dXIvcHJpdmF0ZS9zZWNyZXQua2V5JykpOwokcD1leHBsb2RlKCcuJywkdCk7CmlmKGNvdW50KCRwKSE9MiB8fCAkc2VjcmV0PT09JycgfHwgIWhhc2hfZXF1YWxzKGhhc2hfaG1hYygnc2hhMjU2JywkcFswXSwkc2VjcmV0KSwkcFsxXSkpe2h0dHBfcmVzcG9uc2VfY29kZSg0MDMpO2VjaG8ganNvbl9lbmNvZGUoYXJyYXkoJ29rJz0+ZmFsc2UsJ2UnPT4ndG9rZW4nKSk7ZXhpdDt9CiRhPWFycmF5X3BhZChleHBsb2RlKCd8Jywoc3RyaW5nKWJhc2U2NF9kZWNvZGUoc3RydHIoJHBbMF0sJy1fJywnKy8nKSkpLDYsJycpOwppZih0aW1lKCk+aW50dmFsKCRhWzJdKSl7aHR0cF9yZXNwb25zZV9jb2RlKDQwMyk7ZWNobyBqc29uX2VuY29kZShhcnJheSgnb2snPT5mYWxzZSwnZSc9PidleHAnKSk7ZXhpdDt9CmlmKCRhWzBdIT09J2FkbWluJyAmJiAkYVswXSE9PSd0ZWNuaWNvJyAmJiAkYVsxXSE9PSRjKXtodHRwX3Jlc3BvbnNlX2NvZGUoNDAzKTtlY2hvIGpzb25fZW5jb2RlKGFycmF5KCdvayc9PmZhbHNlLCdlJz0+J2NsaWVudGUnKSk7ZXhpdDt9CmlmKCRjPT09Jycpe2VjaG8ganNvbl9lbmNvZGUoYXJyYXkoJ29rJz0+ZmFsc2UsJ2UnPT4nbm9jbGllbnRlJykpO2V4aXQ7fQokdXA9Jyc7CmlmKCRhWzBdPT09J2NsaWVudCcpeyAkdXM9QGluY2x1ZGUgJy92YXIvd3d3L3ZpYmthcHR1ci9wcml2YXRlL3VzZXJzLnBocCc7IGlmKGlzX2FycmF5KCR1cykmJmlzc2V0KCR1c1skYVs0XV1bJ3BsYW50J10pKSAkdXA9KHN0cmluZykkdXNbJGFbNF1dWydwbGFudCddOyB9CiRiYXNlPShpc3NldCgkR0xPQkFMU1snVktfUkVQT1JUUyddKT8kR0xPQkFMU1snVktfUkVQT1JUUyddOicvdmFyL3d3dy92aWJrYXB0dXIvcmVwb3J0cycpLicvJy4kYzsKZnVuY3Rpb24gdmtfbWVzZXMoJGQpewogICRvPWFycmF5KCk7CiAgZm9yZWFjaCgoYXJyYXkpZ2xvYigkZC4nL2hpc3QvKi5wZGYnKSBhcyAkZil7ICRtPWJhc2VuYW1lKCRmLCcucGRmJyk7IGlmKHByZWdfbWF0Y2goJy9eW2EtejAtOS1dKyQvJywkbSkpICRvW109JG07IH0KICAkcGVyPXRyaW0oKHN0cmluZylAZmlsZV9nZXRfY29udGVudHMoJGQuJy9wZXJpb2RvLnR4dCcpKTsKICAkaGFzPWlzX2ZpbGUoJGQuJy9pbmZvcm1lLnBkZicpOwogIGlmKCRoYXMgJiYgJHBlciE9PScnICYmIHByZWdfbWF0Y2goJy9eW2EtejAtOS1dKyQvJywkcGVyKSAmJiAhaW5fYXJyYXkoJHBlciwkbykpICRvW109JHBlcjsKICByZXR1cm4gYXJyYXkoJG8sKCRoYXMgJiYgIWNvdW50KCRvKSkpOwp9CmZ1bmN0aW9uIHZrX2VudHJhZGEoJGQpewogIGxpc3QoJHYsJHZjKT12a19tZXNlcygkZCk7IGxpc3QoJHQsJHRjKT12a19tZXNlcygkZC4nL3Rlcm1vJyk7CiAgaWYoIWNvdW50KCR2KSAmJiAhJHZjICYmICFjb3VudCgkdCkpIHJldHVybiBudWxsOwogIHJldHVybiBhcnJheSgndic9PiR2LCd2Yyc9PiR2YywndCc9PiR0KTsKfQokcj1hcnJheSgpOwppZigkdXA9PT0nJyl7ICRlPXZrX2VudHJhZGEoJGJhc2UpOyBpZigkZSkgJHJbJyddPSRlOyB9CmZvcmVhY2goKGFycmF5KWdsb2IoJGJhc2UuJy8qJyxHTE9CX09OTFlESVIpIGFzICRkKXsKICAkbj1iYXNlbmFtZSgkZCk7IGlmKGluX2FycmF5KCRuLGFycmF5KCdmaWNoYXMnLCdoaXN0JywndGVybW8nKSkpIGNvbnRpbnVlOwogIGlmKCR1cCE9PScnICYmICRuIT09JHVwKSBjb250aW51ZTsKICAkZT12a19lbnRyYWRhKCRkKTsgaWYoJGUpICRyWyRuXT0kZTsKfQplY2hvIGpzb25fZW5jb2RlKGFycmF5KCdvayc9PnRydWUsJ3InPT4ob2JqZWN0KSRyKSk7Cg==').decode('utf-8'); TAIL=base64.b64decode('aWYoJHJvbGU9PT0nY2xpZW50Jyl7CiAgJHVzPUBpbmNsdWRlICcvdmFyL3d3dy92aWJrYXB0dXIvcHJpdmF0ZS91c2Vycy5waHAnOyAkdXA9KGlzX2FycmF5KCR1cykmJmlzc2V0KCRhWzRdKSYmaXNzZXQoJHVzWyRhWzRdXVsncGxhbnQnXSkpPyhzdHJpbmcpJHVzWyRhWzRdXVsncGxhbnQnXTonJzsKICBpZigkdXAhPT0nJykgJHBsPSR1cDsKfQokYmFzZT0nL3Zhci93d3cvdmlia2FwdHVyL3JlcG9ydHMvJy4kYzsKJGQ9JGJhc2U7ICRuYW1lPSdJbmZvcm1lXycuJGM7CmlmKCRwbCE9PScnKXsKICBpZihpc19maWxlKCRiYXNlLicvJy4kcGwuJy9pbmZvcm1lLnBkZicpIHx8IGlzX2RpcigkYmFzZS4nLycuJHBsLicvaGlzdCcpKXsgJGQ9JGJhc2UuJy8nLiRwbDsgJG5hbWUuPSdfJy4kcGw7IH0KICBlbHNlIHsKICAgICRvdHJhcz1mYWxzZTsKICAgIGZvcmVhY2goKGFycmF5KWdsb2IoJGJhc2UuJy8qL2luZm9ybWUucGRmJykgYXMgJHgpeyBpZighaW5fYXJyYXkoYmFzZW5hbWUoZGlybmFtZSgkeCkpLGFycmF5KCd0ZXJtbycsJ2hpc3QnLCdmaWNoYXMnKSkpeyAkb3RyYXM9dHJ1ZTsgYnJlYWs7IH0gfQogICAgaWYoJG90cmFzKXsgaHR0cF9yZXNwb25zZV9jb2RlKDQwNCk7ZWNobyAnSW5mb3JtZSBubyBkaXNwb25pYmxlJztleGl0OyB9CiAgfQp9CiRtPXByZWdfcmVwbGFjZSgnL1teYS16MC05LV0vJywnJyxzdHJ0b2xvd2VyKGlzc2V0KCRfR0VUWydtJ10pPyRfR0VUWydtJ106JycpKTsKJGZpbGU9JGQuJy9pbmZvcm1lLnBkZic7CmlmKCRtIT09JycpewogIC8qIHVuIG1lcyBjb25jcmV0bzogc29sbyBzaSBlc2UgbWVzIGVzdGEgZ3VhcmRhZG87IG51bmNhIHNlIGVudHJlZ2Egb3RybyBpbmZvcm1lIGVuIHN1IGx1Z2FyICovCiAgJGhmPSRkLicvaGlzdC8nLiRtLicucGRmJzsKICBpZihpc19maWxlKCRoZikpICRmaWxlPSRoZjsKICBlbHNlIGlmKHRyaW0oKHN0cmluZylAZmlsZV9nZXRfY29udGVudHMoJGQuJy9wZXJpb2RvLnR4dCcpKSE9PSRtKXsgaHR0cF9yZXNwb25zZV9jb2RlKDQwNCk7ZWNobyAnSW5mb3JtZSBubyBkaXNwb25pYmxlJztleGl0OyB9CiAgJG5hbWUuPSdfJy4kbTsKfQppZighaXNfZmlsZSgkZmlsZSkpe2h0dHBfcmVzcG9uc2VfY29kZSg0MDQpO2VjaG8gJ0luZm9ybWUgbm8gZGlzcG9uaWJsZSc7ZXhpdDt9CmhlYWRlcignQ29udGVudC1UeXBlOiBhcHBsaWNhdGlvbi9wZGYnKTsKaGVhZGVyKCdDb250ZW50LURpc3Bvc2l0aW9uOiBhdHRhY2htZW50OyBmaWxlbmFtZT0iJy4kbmFtZS4nLnBkZiInKTsKaGVhZGVyKCdDb250ZW50LUxlbmd0aDogJy5maWxlc2l6ZSgkZmlsZSkpOwpyZWFkZmlsZSgkZmlsZSk7Cg==').decode('utf-8')
F=API+'/informe.php'; s=open(F,encoding='utf-8').read()
A="$base='/var/www/vibkaptur/reports/'.$c;"
if 'un mes concreto' in s: n=None
elif s.count(A)!=1 or "$role=$a[0]" not in s or "$p=explode('.',$t);" not in s: print('NO HE TOCADO NADA: informe.php no es como esperaba'); sys.exit()
else: n=s[:s.index(A)]+TAIL
def lint(txt,name):
    T=API+'/'+name+'.nuevo.php'; open(T,'w',encoding='utf-8').write(txt)
    r=subprocess.run(['php','-l',T],capture_output=True,text=True)
    if r.returncode!=0: os.remove(T); print('NO HE TOCADO NADA: error de sintaxis en',name,r.stdout); sys.exit()
    return T
T1=lint(NEW,'informes'); T2=lint(n,'informe') if n else None
st=os.stat(F)
if T2:
    os.makedirs('/root/vibk_api_antes',exist_ok=True)
    shutil.copy2(F,'/root/vibk_api_antes/informe.php.'+time.strftime('%Y%m%d_%H%M'))
    os.replace(T2,F); os.chown(F,st.st_uid,st.st_gid); os.chmod(F,st.st_mode)
G=API+'/informes.php'; os.replace(T1,G); os.chown(G,st.st_uid,st.st_gid); os.chmod(G,st.st_mode)
print('INFORMES POR MES INSTALADO')
R='/var/www/vibkaptur/reports'
if os.path.isdir(R) and len(sys.argv)==1:
    print('--- PDF guardados por cliente ---')
    for c in sorted(os.listdir(R)):
        for root,ds,fs in os.walk(os.path.join(R,c)):
            if os.path.basename(root) in ('fichas','incoming','done','img'): ds[:]=[]; continue
            rel=os.path.relpath(root,R)
            if 'informe.pdf' in fs:
                per=''
                try: per=open(os.path.join(root,'periodo.txt')).read().strip()
                except Exception: pass
                print(' ',rel,'| actual:',per or '(mes sin apuntar)')
            if os.path.basename(root)=='hist':
                ms=sorted(f[:-4] for f in fs if f.endswith('.pdf'))
                if ms: print(' ',rel,'|',', '.join(ms))
