# Ansible

Управляющий узел — отдельный Linux/WSL, управляемый — учебная Ubuntu Server 24.04 amd64 в сети Host-only. Адрес 192.168.56.101 взят из существующей документации, его нужно сверить с фактическим адресом до запуска. Inventory bootstrap.ini использует student, prod.ini — devops с ключом ~/.ssh/devops_vm. Подлинность ключа хоста сверяется с VM и проверяется через known_hosts.

Роли выполняются в порядке base → ssh → nginx → app. Base устанавливает Docker, ssh настраивает доступ и UFW, nginx настраивает reverse proxy, app обновляет контейнер. Образ ghcr.io/hehekutov/devops-ci-app разворачивается по полному SHA. До первого запуска задайте DEVOPS_APP_SHA равным опубликованному SHA из ГХСР. Для контрольной работы значение передаётся автоматически как app_tag из GITHUB_SHA.

```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
ansible-inventory -i inventory/bootstrap.ini --graph
ansible-inventory --graph
ansible-playbook -i inventory/bootstrap.ini site.yml --syntax-check
ansible-playbook site.yml --syntax-check
ansible-playbook -i inventory/bootstrap.ini site.yml --ask-pass --ask-become-pass
ansible-playbook site.yml
ansible-playbook verify.yml
curl --fail --silent --show-error http://192.168.56.101/health
```

Nginx публикует порт 80. Контейнер доступен на 127.0.0.1:5000, контрольный маршрут — /health. Во время контрольной запуск site.yml для выполнения заданий производится только через CI. Ключ SSH и регистрационный токен runner остаются на управляющем узле.
