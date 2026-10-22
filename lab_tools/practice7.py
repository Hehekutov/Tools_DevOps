"""Run measured laboratory stages without copying the server's secret file."""
import argparse, subprocess, time, shutil, json
from pathlib import Path
from remote import ROOT, connect, execute

PY=str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
E=ROOT/'reports/practices-5-8/evidence'
p=argparse.ArgumentParser();p.add_argument('stage',choices=['initial','rebuild','compose','proxy','audit']);args=p.parse_args()

def sync(initial=False):
    stage=ROOT/'tmp/p7-app';stage.mkdir(exist_ok=True)
    for f in (ROOT/'app').iterdir():
        if f.is_file() and f.name!='.env': shutil.copy2(f,stage/f.name)
    if initial:
        f=stage/'app.py';f.write_text(f.read_text(encoding='utf-8').replace('Hello from Docker, Kudoyarov!','Hello from Docker!'),encoding='utf-8')
    shell=ROOT/'tmp/p7-sync.sh'
    shell.write_text('set -euo pipefail\ncd "'+ROOT.as_posix()+'"\nrsync -avz --delete --exclude=.env --chmod=D755,F644 -e "$DEPLOY_SSH_BIN" --dry-run tmp/p7-app/ devops:app/\nrsync -avz --delete --exclude=.env --chmod=D755,F644 -e "$DEPLOY_SSH_BIN" tmp/p7-app/ devops:app/\n',encoding='utf-8',newline='\n')
    subprocess.run([PY,str(ROOT/'lab_tools/run_client.py'),str(shell),'--log',str(E/('p7-sync-initial.txt' if initial else 'p7-sync-final.txt'))],check=True)

def run(name,script,sudo=False,required=0):
    rc,out,err=execute(c,a,script,sudo)
    (E/(name+'.txt')).write_text(out+('\nSTDERR\n'+err if err else '')+f'\nEXIT STATUS: {rc}\n',encoding='utf-8')
    print(name,'exit',rc,flush=True)
    if required is not None and rc!=required:raise RuntimeError(name+' failed; inspect evidence')
    return out

if args.stage in ('initial','rebuild'):sync(args.stage=='initial')
c,a=connect('devops')
try:
    if args.stage=='initial':
        run('p7-docker-ready','id; docker version; docker compose version; docker run --rm hello-world')
        run('p7-build-initial','set -e\ncd ~/app\ndocker build --progress=plain -t devops-app:1.0 .\ndocker image ls devops-app\ndocker history devops-app:1.0')
        run('p7-without-db','''set -e
cd ~/app
docker run -d --name app-test -p 127.0.0.1:5000:5000 devops-app:1.0
sleep 3
docker ps
curl -i http://127.0.0.1:5000/health
curl -i http://127.0.0.1:5000/
docker logs app-test
docker exec app-test id
docker exec app-test stat -c '%a %U:%G %n' /app/app.py
docker rm -f app-test
''')
    elif args.stage=='rebuild':
        run('p7-build-cached','set -e\ncd ~/app\ndocker build --progress=plain -t devops-app:1.0 .\ndocker history devops-app:1.0')
    elif args.stage=='compose':
        run('p7-compose','''set -e
cd ~/app
if [ ! -f .env ]; then
  umask 077
  cp .env.example .env
  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 16)/" .env
fi
chmod 600 .env
stat -c '%a %U:%G %n' .env
docker compose up -d --build --wait
docker compose ps
docker compose exec -T --interactive=false app id
for i in 1 2 3; do curl -sS http://127.0.0.1:5000/; done
docker network ls
docker compose exec -T --interactive=false app getent hosts db
ss -tln | grep -E ':(5000|5432)\\b'
docker inspect -f '{{json .Config.User}}' devops-app:1.0
''')
        run('p7-volumes','''set -e
cd ~/app
echo BEFORE_DOWN
curl -sS http://127.0.0.1:5000/
docker compose down
docker volume ls
docker compose up -d --wait
echo AFTER_DOWN
curl -sS http://127.0.0.1:5000/
docker compose down -v
docker compose up -d --wait
echo AFTER_DOWN_V
curl -sS http://127.0.0.1:5000/
docker volume ls
''')
    elif args.stage=='proxy':
        run('p7-ufw-exposure','''set -e
docker run -d --rm --name exposed -p 5001:5000 devops-app:1.0
sleep 2
ufw status | grep 5001 || true
iptables -t nat -L DOCKER -n | grep 5001
''',True)
        try:
            r=subprocess.run([r'C:\Windows\System32\curl.exe','--max-time','8','-i','http://devops.local:5001/health'],capture_output=True,text=True)
            (E/'p7-host-exposed.txt').write_text(r.stdout+r.stderr+f'\nEXIT STATUS: {r.returncode}\n',encoding='utf-8')
            if r.returncode!=0 or '200 OK' not in r.stdout:raise RuntimeError('exposed health failed')
        finally:run('p7-exposure-stopped','docker stop exposed',True)
        with c.open_sftp() as s:
            with s.open('/tmp/p7-nginx-update.py','w') as f:
                f.write('''from pathlib import Path
p=Path('/etc/nginx/sites-available/devops-site')
t=p.read_text()
fragment='''+repr('''    location /app/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
''')+'''
if 'location /app/' not in t:
    pos=t.rfind('}')
    p.write_text(t[:pos]+fragment+t[pos:])
''')
        run('p7-proxy-config','set -e\npython3 /tmp/p7-nginx-update.py\nnginx -t\nsystemctl reload nginx\ncat /etc/nginx/sites-available/devops-site',True)
        run('p7-https','''set -e
curl --cacert /etc/ssl/certs/devops.crt -i https://devops.local/app/
curl --cacert /etc/ssl/certs/devops.crt -i https://devops.local/app/health
curl --cacert /etc/ssl/certs/devops.crt -I https://devops.local/
''')
        run('p7-502','''set -e
cd ~/app
docker compose stop app
curl --cacert /etc/ssl/certs/devops.crt -I https://devops.local/app/
''')
        try:run('p7-502-log','tail -n 4 /var/log/nginx/devops-site.error.log',True)
        finally:run('p7-app-restored','cd ~/app; docker compose start app; sleep 3; curl --cacert /etc/ssl/certs/devops.crt -i https://devops.local/app/health')
    elif args.stage=='audit':
        with c.open_sftp() as s:s.put(str(ROOT/'scripts/audit.sh'),'/tmp/audit.sh')
        run('p7-audit-good','bash /tmp/audit.sh',True)
        run('p7-audit-bad','''set -e
cd /home/devops/app
cp docker-compose.yml /tmp/p7-compose-backup.yml
sed -i 's/127.0.0.1:5000:5000/5000:5000/' docker-compose.yml
docker compose up -d --wait
ss -tln | grep -E ':(5000|5432)\\b'
set +e
bash /tmp/audit.sh
rc=$?
echo AUDIT_EXIT=$rc
exit $rc
''',True,1)
        run('p7-audit-restored','''set -e
cd /home/devops/app
cp /tmp/p7-compose-backup.yml docker-compose.yml
chown devops:devops docker-compose.yml
docker compose up -d --wait
bash /tmp/audit.sh
stat -c '%a %U:%G %n' .env
''',True)
finally:c.close()
