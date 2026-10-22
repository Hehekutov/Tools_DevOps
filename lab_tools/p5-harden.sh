#!/usr/bin/env bash
set -euo pipefail
cp -n /etc/ssh/sshd_config /etc/ssh/sshd_config.backup || true
find /etc/ssh/sshd_config.d -type f -name '*.conf' -exec sed -i -E 's/^([[:space:]]*PasswordAuthentication[[:space:]]+yes)/# Disabled for key-only lab: \1/' {} +
cat > /etc/ssh/sshd_config.d/99-hardening.conf <<'EOF'
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
EOF
/usr/sbin/sshd -t
/usr/sbin/sshd -T | grep -E '^(port|permitrootlogin|passwordauthentication|maxauthtries|allowusers|kbdinteractiveauthentication) '
systemctl disable --now ssh.socket || true
systemctl enable --now ssh.service
systemctl restart ssh.service
ss -tlnp | grep sshd
ufw default deny incoming
ufw default allow outgoing
ufw allow 2222/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
ufw delete allow 2222/tcp
ufw limit 2222/tcp comment 'SSH rate-limited'
ufw logging medium
ufw status verbose
hostname -f
