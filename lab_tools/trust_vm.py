"""Verify the host key against the trusted VirtualBox serial console first."""
from pathlib import Path
import socket,paramiko,tempfile,re,sys
sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parents[1]
serial=(root/'reports/practices-5-8/evidence/install-serial.log').read_text(errors='replace')
expected=re.findall(r'^ssh-ed25519 (\S+) root@devops-vm',serial,re.M)[-1]
t=paramiko.Transport(socket.create_connection(('127.0.0.1',2222),5));t.start_client(timeout=8);key=t.get_remote_server_key();t.close()
assert key.get_base64()==expected,'The network key differs from the VirtualBox console key'
for path in [Path(tempfile.gettempdir())/'codex-devops-known-hosts',Path.home()/'.ssh/known_hosts']:
    keys=paramiko.HostKeys()
    if path.exists():keys.load(str(path))
    for host in ['[127.0.0.1]:2222','[192.168.56.101]:2222','[devops.local]:2222']:
        keys.add(host,key.get_name(),key)
    keys.save(str(path))
print('SSH host key verified against the VirtualBox console and saved')
