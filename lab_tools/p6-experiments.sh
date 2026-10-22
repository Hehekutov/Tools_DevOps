#!/usr/bin/env bash
set -u
url=https://devops.local
curlit() { curl -sk --resolve devops.local:443:127.0.0.1 -o /dev/null -w '%{http_code}\n' "$url/"; }
echo 'FILE MODE 600'
chmod 600 /var/www/devops-site/index.html
curlit
sudo -u www-data cat /var/www/devops-site/index.html
tail -n 2 /var/log/nginx/devops-site.error.log
chmod 644 /var/www/devops-site/index.html
echo 'DIRECTORY PERMISSION MATRIX'
for mode in 755 750 744 711; do
  chmod "$mode" /var/www/devops-site
  printf 'mode=%s HTTP=' "$mode"; curlit
  sudo -u www-data ls /var/www/devops-site
  sudo -u www-data cat /var/www/devops-site/index.html >/dev/null
done
chmod 755 /var/www/devops-site
tail -n 8 /var/log/nginx/devops-site.error.log
echo 'INSECURE CONTENT PERMISSIONS'
chmod 666 /var/www/devops-site/index.html
find /var/www/devops-site -perm -o+w
sudo -u www-data sh -c 'echo "<h1>defaced</h1>" > /var/www/devops-site/index.html'
curl -sk --resolve devops.local:443:127.0.0.1 "$url/"
echo 'Content and mode will be restored by deploy.sh from the client'
