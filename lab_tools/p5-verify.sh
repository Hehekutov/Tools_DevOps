#!/usr/bin/env bash
set -u
echo 'EFFECTIVE SSH CONFIGURATION'
sshd -T | grep -E '^(port|permitrootlogin|passwordauthentication|maxauthtries|allowusers) '
ss -tlnp | grep sshd
stat -c '%a %n' /home/devops/.ssh /home/devops/.ssh/authorized_keys
echo 'FIREWALL'
ufw status verbose
echo 'FQDN'
hostname -f
echo 'AUDIT NORMAL CONFIGURATION'
bash /tmp/audit.sh; echo "audit_exit=$?"
echo 'AUDIT INCORRECT MAXAUTHTRIES'
sed -i 's/MaxAuthTries 3/MaxAuthTries 10/' /etc/ssh/sshd_config.d/99-hardening.conf
bash /tmp/audit.sh; echo "audit_exit=$?"
sed -i 's/MaxAuthTries 10/MaxAuthTries 3/' /etc/ssh/sshd_config.d/99-hardening.conf
sshd -t
echo 'AUDIT RESTORED CONFIGURATION'
bash /tmp/audit.sh; echo "audit_exit=$?"
echo 'AUTHENTICATION JOURNAL'
journalctl -u ssh --since '20 min ago' --no-pager | grep -Ei 'invalid|failed|denied|not allowed' | tail -8 || true
echo 'BLOCKED TRAFFIC'
grep 'UFW BLOCK' /var/log/ufw.log | tail -3 || true
