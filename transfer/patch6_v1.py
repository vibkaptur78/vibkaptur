# Punto 6: la sesion se comprueba contra la lista de usuarios en cada llamada. Uso: python3 patch6.py
import os,shutil,subprocess,sys,base64
API='/var/www/vibkaptur/public/api'; PRIV='/var/www/vibkaptur/private'
GUARD=base64.b64decode('PD9waHAKLy8gVklCS0FQVFVSIMK3IGNvbXByb2JhY2lvbiBkZSBzZXNpb24gZW4gY2FkYSBsbGFtYWRhIGEgL2FwaSAoc2UgY2FyZ2Egc29sYSBhbnRlcyBkZSBjYWRhIHNjcmlwdCkuCi8vIENvcnRhIGFsIGluc3RhbnRlIGVsIGFjY2VzbyBkZSB1biB1c3VhcmlvIGRhZG8gZGUgYmFqYSwgY2FtYmlhZG8gZGUgY2xpZW50ZSBvIGNvbiBsYSBjbGF2ZSByZXNldGVhZGEuCihmdW5jdGlvbigpewogIEBoZWFkZXIoJ1gtVmliay1HdWFyZDogMScpOwogICR0PScnOwogIGlmKGlzc2V0KCRfUE9TVFsndCddKSkgJHQ9JF9QT1NUWyd0J107CiAgZWxzZWlmKGlzc2V0KCRfR0VUWyd0J10pKSAkdD0kX0dFVFsndCddOwogIGVsc2UgeyAkcmF3PUBmaWxlX2dldF9jb250ZW50cygncGhwOi8vaW5wdXQnKTsgaWYoaXNfc3RyaW5nKCRyYXcpICYmICRyYXchPT0nJyAmJiAkcmF3WzBdPT09J3snKXsgJGo9anNvbl9kZWNvZGUoJHJhdyx0cnVlKTsgaWYoaXNfYXJyYXkoJGopICYmIGlzc2V0KCRqWyd0J10pKSAkdD0kalsndCddOyB9IH0KICBpZighaXNfc3RyaW5nKCR0KSB8fCAkdD09PScnKSByZXR1cm47CiAgJHA9ZXhwbG9kZSgnLicsJHQpOyBpZihjb3VudCgkcCkhPTIpIHJldHVybjsKICAkc2VjcmV0PXRyaW0oKHN0cmluZylAZmlsZV9nZXRfY29udGVudHMoJy92YXIvd3d3L3ZpYmthcHR1ci9wcml2YXRlL3NlY3JldC5rZXknKSk7IGlmKCRzZWNyZXQ9PT0nJykgcmV0dXJuOwogIGlmKCFoYXNoX2VxdWFscyhoYXNoX2htYWMoJ3NoYTI1NicsJHBbMF0sJHNlY3JldCksJHBbMV0pKSByZXR1cm47ICAgLy8gZmlybWEgbWFsYTogbG8gcmVjaGF6YSBlbCBwcm9waW8gc2NyaXB0CiAgJGE9YXJyYXlfcGFkKGV4cGxvZGUoJ3wnLChzdHJpbmcpYmFzZTY0X2RlY29kZShzdHJ0cigkcFswXSwnLV8nLCcrLycpKSksNiwnJyk7CiAgJHVzZXJzPUBpbmNsdWRlICcvdmFyL3d3dy92aWJrYXB0dXIvcHJpdmF0ZS91c2Vycy5waHAnOyBpZighaXNfYXJyYXkoJHVzZXJzKSB8fCAhY291bnQoJHVzZXJzKSkgcmV0dXJuOwogICRlbWFpbD0kYVs0XTsgJHdoeT0nJzsKICBpZigkZW1haWw9PT0nJykgJHdoeT0ncmVsb2dpbic7CiAgZWxzZWlmKCFpc3NldCgkdXNlcnNbJGVtYWlsXSkpICR3aHk9J2JhamEnOwogIGVsc2UgewogICAgJHU9JHVzZXJzWyRlbWFpbF07CiAgICBpZigoaXNzZXQoJHVbJ3JvbGUnXSk/JHVbJ3JvbGUnXTonJykhPT0kYVswXSB8fCAoc3RyaW5nKShpc3NldCgkdVsnYyddKT8kdVsnYyddOicnKSE9PShzdHJpbmcpJGFbMV0pICR3aHk9J2NhbWJpbyc7CiAgICBlbHNlaWYoc3Vic3RyKGhhc2goJ3NoYTI1NicsKHN0cmluZykoaXNzZXQoJHVbJ3AnXSk/JHVbJ3AnXTonJykpLDAsMTApIT09JGFbNV0pICR3aHk9J2NsYXZlJzsKICB9CiAgaWYoJHdoeT09PScnKSByZXR1cm47CiAgaHR0cF9yZXNwb25zZV9jb2RlKDQwMyk7IGhlYWRlcignQ29udGVudC1UeXBlOiBhcHBsaWNhdGlvbi9qc29uJyk7CiAgZWNobyBqc29uX2VuY29kZShhcnJheSgnb2snPT5mYWxzZSwnZSc9PidzZXNpb24nLCd3aHknPT4kd2h5KSk7IGV4aXQ7Cn0pKCk7Cg==').decode()
tp=os.path.join(API,'token.php'); s=open(tp,encoding='utf-8').read()
OLD="$payload=$u['role'].'|'.$u['c'].'|'.$exp.'|'.$flags;"
NEW="$payload=$u['role'].'|'.$u['c'].'|'.$exp.'|'.$flags.'|'.$email.'|'.substr(hash('sha256',$u['p']),0,10);"
if NEW in s: print('token.php ya estaba actualizado')
else:
    if s.count(OLD)!=1: print('FALLO: token.php no es como se esperaba. NO SE HA TOCADO NADA'); sys.exit(1)
    tmp='/tmp/token_new.php'; open(tmp,'w',encoding='utf-8').write(s.replace(OLD,NEW))
    if subprocess.run(['php','-l',tmp],capture_output=True).returncode!=0: print('FALLO de sintaxis. NO SE HA TOCADO NADA'); sys.exit(1)
    shutil.copy2(tp,tp+'.bak6'); st=os.stat(tp); shutil.copyfile(tmp,tp); os.chmod(tp,st.st_mode&0o7777); os.chown(tp,st.st_uid,st.st_gid)
gp=os.path.join(PRIV,'guard.php'); open('/tmp/guard_new.php','w',encoding='utf-8').write(GUARD)
if subprocess.run(['php','-l','/tmp/guard_new.php'],capture_output=True).returncode!=0: print('FALLO de sintaxis en guard'); sys.exit(1)
shutil.copyfile('/tmp/guard_new.php',gp); ref=os.stat(os.path.join(PRIV,'users.php')); os.chown(gp,ref.st_uid,ref.st_gid); os.chmod(gp,0o644)
ui=os.path.join(API,'.user.ini'); cur=open(ui).read() if os.path.exists(ui) else ''
if 'auto_prepend_file' not in cur:
    open(ui,'a').write(('\n' if cur and not cur.endswith('\n') else '')+'auto_prepend_file=/var/www/vibkaptur/private/guard.php\n')
r=os.stat(os.path.join(API,'clave.php')); os.chown(ui,r.st_uid,r.st_gid); os.chmod(ui,0o644)
print('SESIONES PROTEGIDAS (activo en 5 minutos como maximo)')
