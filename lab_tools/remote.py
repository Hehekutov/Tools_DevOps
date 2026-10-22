"""Run laboratory commands against the local VirtualBox VM; never logs credentials."""
from pathlib import Path
import argparse, json, sys, tempfile, time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
AUTH = Path(tempfile.gettempdir()) / 'codex-devops-auth.json'

def connect(user=None, port=2222):
    auth=json.loads(AUTH.read_text(encoding='utf-8'))
    client=paramiko.SSHClient()
    known=Path(tempfile.gettempdir())/'codex-devops-known-hosts'
    if known.exists(): client.load_host_keys(str(known))
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    username=user or auth['user']
    kwargs={'password':auth['password'],'key_filename':str(Path.home()/'.ssh/devops_vm')}
    if username in ('devops','ubuntu-server'):
        kwargs={'key_filename':str(Path.home()/'.ssh/devops_vm')}
    client.connect('127.0.0.1',port=port,username=username,timeout=10,allow_agent=False,look_for_keys=False,**kwargs)
    client.save_host_keys(str(known))
    return client,auth

def execute(client, auth, script, sudo=False, timeout=1800):
    need_password=False
    if sudo:
        _,probe,_=client.exec_command('sudo -n true')
        need_password=probe.channel.recv_exit_status()!=0
    cmd='sudo -S -p "" bash -s' if sudo else 'bash -s'
    stdin,stdout,stderr=client.exec_command(cmd,timeout=timeout)
    if need_password: stdin.write(auth['password']+'\n');stdin.flush()
    stdin.write(script+'\n');stdin.channel.shutdown_write()
    # Drain both streams together to avoid blocking on large apt/build logs.
    channel=stdout.channel;out=[];err=[]
    while not channel.exit_status_ready() or channel.recv_ready() or channel.recv_stderr_ready():
        if channel.recv_ready(): out.append(channel.recv(65536).decode('utf-8','replace'))
        if channel.recv_stderr_ready(): err.append(channel.recv_stderr(65536).decode('utf-8','replace'))
        time.sleep(.05)
    return channel.recv_exit_status(),''.join(out),''.join(err)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser();p.add_argument('--script');p.add_argument('--command');p.add_argument('--sudo',action='store_true');p.add_argument('--log');p.add_argument('--user');p.add_argument('--port',type=int,default=2222);p.add_argument('--upload',nargs=2);p.add_argument('--download',nargs=2)
    a=p.parse_args();c,auth=connect(a.user,a.port)
    if a.upload:
        s=c.open_sftp();s.put(*a.upload);s.close();code=0
    elif a.download:
        s=c.open_sftp();s.get(*a.download);s.close();code=0
    else:
        script=Path(a.script).read_text(encoding='utf-8') if a.script else a.command or sys.stdin.read()
        code,out,err=execute(c,auth,script,a.sudo)
        result=out+('\nSTDERR\n'+err if err else '')+f'\nEXIT STATUS: {code}\n'
        if a.log: Path(a.log).write_text(result,encoding='utf-8')
        print(result)
    c.close();sys.exit(code)
