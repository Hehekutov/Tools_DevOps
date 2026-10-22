#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
if [[ ${SKIP_PACKAGES:-0} != 1 ]]; then
  sed -i -E '/^[[:space:]]*deb.*(cdrom|file:)/s/^/# Disabled installation medium: /' /etc/apt/sources.list
  sed -i -E 's@http://[^ ]*archive.ubuntu.com/ubuntu@https://archive.ubuntu.com/ubuntu@g; s@http://security.ubuntu.com/ubuntu@https://security.ubuntu.com/ubuntu@g' /etc/apt/sources.list.d/ubuntu.sources
  apt-get update
  apt-get upgrade -y
  apt-get install -y openssh-server ufw rsync curl git
fi
if [[ ${PREPARE_ONLY:-0} == 1 ]]; then exit 0; fi
id devops >/dev/null 2>&1 || useradd -m -s /bin/bash devops
usermod -aG sudo devops
# Keep the student's existing password without writing it into project files.
usermod -p "$(getent shadow hehekutov09 | cut -d: -f2)" devops
hostnamectl set-hostname devops-vm
sed -i '/^127\.0\.1\.1/d' /etc/hosts
printf '127.0.1.1 devops-vm.devops.local devops-vm\n' >> /etc/hosts
mkdir -p /home/devops/.ssh
cp /tmp/devops_vm.pub /home/devops/.ssh/authorized_keys
chown -R devops:devops /home/devops/.ssh
chmod 700 /home/devops/.ssh
chmod 600 /home/devops/.ssh/authorized_keys
cat /etc/os-release
ip -brief address
groups devops
stat -c '%a %n' /home/devops/.ssh /home/devops/.ssh/authorized_keys
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
