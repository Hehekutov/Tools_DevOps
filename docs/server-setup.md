# Конфигурация виртуальной машины devops-vm

## 1. Параметры машины

VirtualBox 7.2.20, имя машины в менеджере DevOps. Внутреннее имя узла devops-vm.
Ubuntu Server 24.04 LTS amd64, без графической оболочки. Оперативная память 2048 МБ,
2 виртуальных процессора. Динамический диск VDI 25,1 ГиБ.
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

1. Уточнить адреса и подключиться начальной учётной записью к 127.0.0.1:2222.
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
