#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get install -y nginx rsync openssl
systemctl enable --now nginx
ps -o user,pid,ppid,cmd -C nginx
mkdir -p /var/www/devops-site
chown devops:devops /var/www/devops-site
chmod 755 /var/www/devops-site
sudo -u devops sh -c 'echo "<h1>devops.local: placeholder</h1>" > /var/www/devops-site/index.html'
chmod 644 /var/www/devops-site/index.html
namei -l /var/www/devops-site/index.html
sudo -u www-data cat /var/www/devops-site/index.html
sudo -u www-data touch /var/www/devops-site/test.html || true
cat > /etc/nginx/sites-available/devops-site <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name devops.local;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name devops.local;
    root /var/www/devops-site;
    index index.html;
    ssl_certificate /etc/ssl/certs/devops.crt;
    ssl_certificate_key /etc/ssl/private/devops.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    location / { try_files $uri $uri/ =404; }
    error_page 404 /404.html;
    access_log /var/log/nginx/devops-site.access.log;
    error_log /var/log/nginx/devops-site.error.log;
}
EOF
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/devops.key -out /etc/ssl/certs/devops.crt \
  -subj '/CN=devops.local' -addext 'subjectAltName=DNS:devops.local' 2>/dev/null
chmod 600 /etc/ssl/private/devops.key
chmod 644 /etc/ssl/certs/devops.crt
ln -sfn /etc/nginx/sites-available/devops-site /etc/nginx/sites-enabled/devops-site
if [[ -L /etc/nginx/sites-enabled/default ]]; then unlink /etc/nginx/sites-enabled/default; fi
nginx -t && systemctl reload nginx
ls -l /etc/ssl/private/devops.key /etc/ssl/certs/devops.crt
sudo -u www-data cat /etc/ssl/certs/devops.crt >/dev/null && echo 'Certificate readable by www-data'
sudo -u www-data cat /etc/ssl/private/devops.key >/dev/null || echo 'Private key unreadable by www-data'
ss -tlnp | grep nginx
openssl x509 -in /etc/ssl/certs/devops.crt -noout -subject -issuer -dates -ext subjectAltName
