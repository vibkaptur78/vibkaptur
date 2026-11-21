# Seguridad: retira las copias de seguridad de la carpeta publica y bloquea ese tipo de archivos. Uso: python3 fix10.py
import os,glob,shutil,subprocess,sys
API='/var/www/vibkaptur/public/api'; DST='/var/www/vibkaptur/private/api_bak'
os.makedirs(DST,exist_ok=True); os.chmod(DST,0o700); os.chown(DST,0,0)
n=0
for f in glob.glob(API+'/*'):
    b=os.path.basename(f)
    if os.path.isfile(f) and not b.endswith('.php') and b!='.user.ini':
        shutil.move(f,os.path.join(DST,b)); n+=1
for f in glob.glob('/var/www/vibkaptur/public/t_*.txt'):
    os.remove(f)
for d in ('/var/www/vibkaptur/scripts','/var/www/vibkaptur/private'):
    for f in glob.glob(d+'/*.bak*'):
        try: os.chmod(f,0o600)
        except Exception: pass
print('copias retiradas de la carpeta publica:',n)
cf=os.path.realpath('/etc/nginx/sites-enabled/vibkaptur'); s=open(cf).read()
RULE='  location ~* \\.(bak|old|orig|swp|sql|key|log|tmp|py|ini)([.0-9a-z_-]*)$ { deny all; }\n  location ~ ^/api/(?!.*\\.php$) { deny all; }\n'
if 'bak|old|orig' in s: print('nginx ya tenia el bloqueo')
else:
    k='  location ~ /\\.(?!well-known) { deny all; }\n'
    if s.count(k)!=1: print('AVISO: no encuentro donde poner el bloqueo en nginx; las copias ya estan retiradas, pero el bloqueo NO se ha puesto'); sys.exit(1)
    shutil.copy2(cf,'/root/nginx_vibkaptur.antes_fix10')
    open(cf,'w').write(s.replace(k,k+RULE))
    if subprocess.run(['nginx','-t'],capture_output=True).returncode!=0:
        shutil.copy2('/root/nginx_vibkaptur.antes_fix10',cf); print('AVISO: nginx no acepta el bloqueo; lo he dejado como estaba. Las copias ya estan retiradas'); sys.exit(1)
    subprocess.run(['systemctl','reload','nginx'])
print('COPIAS RETIRADAS Y BLOQUEADAS')
