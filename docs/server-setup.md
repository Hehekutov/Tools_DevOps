# Конфигурация виртуальной машины devops-vm

## 1. Параметры машины

VirtualBox 7.2.20, имя машины в менеджере DevOps. Внутреннее имя узла devops-vm.
Ubuntu Server 24.04 LTS amd64, без графической оболочки. Рабочая конфигурация:
оперативная память 3072 МБ, 1 виртуальный процессор. Динамический диск VDI 25,1 ГиБ.
Вариант методички с 2048 МБ и 2 процессорами проверен, но на данном Windows-хосте
VirtualBox работает через Hyper-V/NEM. Наблюдались soft lockup и зависание живого
снимка. Поэтому для стенда выбран один процессор, а снимки создаются после штатного
выключения гостя. Настройки Hyper-V и защиты Windows не изменялись.
До лабораторной работы сохранён исходный снимок `00-before-practices-5-8`.

## 2. Сетевые интерфейсы

Адаптер 1 NAT, интерфейс enp0s3, адрес 10.0.2.15/24: выход в Интернет.
Адаптер 2 Host-only, интерфейс enp0s8, DHCP-адрес 192.168.56.101/24:
доступ с Windows к учебному серверу. Адрес хостового адаптера 192.168.56.1.
Перед восстановлением уточнить адреса командой `ip -brief address`.

## 3. Правило проброса портов

До усиления SSH: 127.0.0.1:2222 компьютера -> 22/tcp гостевой системы.
После усиления: 127.0.0.1:2222 компьютера -> 2222/tcp гостевой системы.
Имя правила VirtualBox `devops-ssh`, протокол TCP.
Windows использует ~/.ssh/config: Host devops, HostName 127.0.0.1,
Port 2222, User devops, IdentityFile ~/.ssh/devops_vm, IdentitiesOnly yes.

## 4. Учётные записи

Начальная учётная запись hehekutov09, группа sudo. Учебная учётная запись devops,
группа sudo. Для SSH используется отдельный ключ Ed25519 devops_vm.
Закрытый ключ находится только на компьютере пользователя, открытый ключ
в /home/devops/.ssh/authorized_keys. В репозитории закрытого ключа нет.
Права каталога .ssh 700, authorized_keys 600; владелец devops:devops.

## 5. Служба SSH

Конфигурация /etc/ssh/sshd_config.d/99-hardening.conf:

```text
Port 2222
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
MaxAuthTries 3
LoginGraceTime 30
AllowUsers devops
X11Forwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
```

Резервная копия основного файла /etc/ssh/sshd_config.backup. Конфликтующие
PasswordAuthentication yes в более ранних файлах закомментированы.
Проверки перед применением: `sudo sshd -t` и `sudo sshd -T`.
Отключён ssh.socket, включён ssh.service; после изменения Port выполнен restart ssh.
Старую сессию сохранять до проверки нового входа. Слушатель проверять `sudo ss -tlnp`.

## 6. Правила межсетевого экрана

Политики: deny incoming, allow outgoing. Разрешены 80/tcp и 443/tcp.
Для 2222/tcp используется LIMIT. Правила создаются до `ufw enable`.
Журналирование medium, журнал /var/log/ufw.log. Проверка `sudo ufw status verbose`.
В Windows hosts добавлена запись `192.168.56.101 devops.local`.
На сервере /etc/hosts содержит `127.0.1.1 devops-vm.devops.local devops-vm`.

## 7. Снимки состояния и восстановление

01-clean-install: после установки и первичной проверки SSH, до учебных изменений.
02-keys-configured: после создания devops и проверки ключа, до усиления SSH.
03-ssh-hardened: после усиления SSH и проверки входа.
04-nginx-https: после настройки Nginx и сертификата.
05-docker-compose: после запуска приложения и базы данных.

Для восстановления со снимка 01-clean-install:

1. После отката 01-clean-install выключить машину, установить 3072 МБ и 1 процессор,
   запустить её. Уточнить адреса и подключиться начальной учётной записью к 127.0.0.1:2222.
2. Создать devops, добавить в sudo, перенести открытый devops_vm.pub в authorized_keys,
   назначить владельца и права из раздела 4. Проверить вход ключом в новой сессии.
3. Создать файл из раздела 5, устранить конфликт PasswordAuthentication,
   выполнить sshd -t и sshd -T, отключить ssh.socket и включить ssh.service.
4. Перезапустить SSH, изменить гостевой порт правила VirtualBox на 2222.
   Проверить ssh devops, отказ root и отказ парольной аутентификации.
5. Применить политики и правила UFW из раздела 6, включить экран,
   проверить подключение в новом терминале и установить hostname.
6. Запустить scripts/audit.sh. Нормальный код завершения 0.

Для воспроизводимости сохранены lab_tools/p5-setup.sh и p5-harden.sh. Первый
запускается от root с предварительно доставленным /tmp/devops_vm.pub. Установка
обновлений относится к первичной подготовке, а при восстановлении актуального
снимка повторная загрузка обновлений не нужна.

## 8. Веб-сервер

Пакет nginx из репозитория Ubuntu. Конфигурация /etc/nginx/sites-available/devops-site,
активирующая ссылка /etc/nginx/sites-enabled/devops-site. Ссылка default отключена.
Каталог /var/www/devops-site принадлежит devops:devops; каталоги 755, файлы 644.
www-data читает опубликованные файлы и не может изменять их.

Сертификат /etc/ssl/certs/devops.crt, права 644. Закрытый ключ
/etc/ssl/private/devops.key, владелец root, права 600. Создание:

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/devops.key -out /etc/ssl/certs/devops.crt \
  -subj '/CN=devops.local' -addext 'subjectAltName=DNS:devops.local'
```

Разрешены TLSv1.2 и TLSv1.3. HTTP возвращает 301 с Location https://$host$request_uri.
HSTS для самоподписанного учебного сертификата не задаётся. Публичный сертификат
скопирован на компьютер в ~/devops.crt по проверенному SSH-соединению.
Применение изменений: `sudo nginx -t && sudo systemctl reload nginx`.
Журналы HTTPS: /var/log/nginx/devops-site.access.log и devops-site.error.log.
HTTP-перенаправления регистрируются в стандартном /var/log/nginx/access.log.

Доставка: scripts/deploy.sh, предварительная проверка scripts/deploy.sh --dry-run.
На данном Windows-хосте используется изолированный MSYS2-клиент rsync,
запускаемый lab_tools/run_client.py. Исходный Git и существующие дистрибутивы WSL
не изменены. lab_tools/client-env.sh задаёт согласованный SSH-клиент и путь
к открытому сертификату; параметры по умолчанию deploy.sh подходят обычному Linux.
Один запуск deploy.sh открывает одно SSH-соединение для rsync; проверка HTTPS
выполняется отдельно через curl. Перед доставкой проверяются чистота Git и index.html.

В AmneziaVPN адрес 192.168.56.101 исключён из туннеля. Прямой Host-only доступ
проверен по ICMP и HTTPS. Временные правила NAT для HTTP и HTTPS после диагностики
удалены; постоянный проброс NAT используется только для SSH.

## 9. Контейнеризация

Docker Engine Community 29.9.2 и плагин Compose v5.6.1 установлены из официального
APT-репозитория https://download.docker.com/linux/ubuntu (noble, stable), ключ
/etc/apt/keyrings/docker.asc, источник /etc/apt/sources.list.d/docker.sources.
Служба docker включена и активна. Пользователь devops входит в группу docker;
новое членство действует в новой SSH-сессии. Доступ к docker.sock предоставляет
административные возможности, поэтому в группу включается только администратор.

Проект находится в /home/devops/app. Доставка с компьютера:

```bash
rsync -avz --delete --exclude=.env --chmod=D755,F644 --dry-run app/ devops:app/
rsync -avz --delete --exclude=.env --chmod=D755,F644 app/ devops:app/
```

Файл /home/devops/app/.env создаётся только на сервере из .env.example,
пароль заменяется результатом `openssl rand -hex 16`, права 600, владелец devops.
Не копировать этот файл на компьютер и не добавлять в Git. .dockerignore исключает
.env из контекста сборки. Команды запуска: `cd ~/app && docker compose up -d --build --wait`.

Образ devops-app:1.0 запускает Gunicorn от пользователя app (uid 999).
PostgreSQL postgres:16-alpine использует именованный том app_db_data и сеть
app_backend. Имя db разрешается встроенным DNS этой сети. Приложение ждёт healthcheck
базы pg_isready. `docker compose down` сохраняет том; `down -v` удаляет данные.
Проверка с удалением выполнена только на созданной учебной базе.

Публикуется только 127.0.0.1:5000 → 5000 приложения. Порт 5432 базы не публикуется.
Compose v5.6.1 в команде `port db 5432` выводил :0 для отсутствующей публикации;
проверка аудита использует реальные NetworkSettings.Ports из docker inspect.

В HTTPS-блок Nginx добавлено:

```nginx
location /app/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Проверить синтаксис и применить: `sudo nginx -t && sudo systemctl reload nginx`.
Статический ресурс / сохранён. /app/ показывает счётчик, /app/health отвечает ok.
На Windows используются curl --cacert ~/devops.crt и обычное имя devops.local.
На самой VM в /etc/hosts добавлен devops.local как псевдоним 127.0.0.1 для
локальных диагностических запросов; полное имя узла сохранено.

Проверка состояния: `docker compose ps`, `docker compose exec -T --interactive=false app id`,
`sudo ss -tlnp`, `sudo bash ~/devops-course-2026/scripts/audit.sh`.
Ожидаются healthy у db, только loopback у 5000, отсутствие слушателя 5432,
14 успешных проверок аудита и код 0. При публикации 5000 на всех интерфейсах
аудит возвращает 1; после опыта возвращена безопасная конфигурация.
Снимок 05-docker-compose сохраняет проект, базу и Nginx для следующей работы.
