"""Verify reconstruction of the documented SSH/UFW state from the clean snapshot."""
from pathlib import Path
import subprocess,time
from remote import connect,execute,ROOT
vbox=r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
started=time.monotonic()
c,a=connect('devops');execute(c,a,'systemctl poweroff',True);c.close()
for _ in range(30):
    info=subprocess.check_output([vbox,'showvminfo','DevOps','--machinereadable'],encoding='utf-8')
    if 'VMState="poweroff"' in info:break
    time.sleep(1)
else:raise RuntimeError('Shutdown failed')
subprocess.run([vbox,'snapshot','DevOps','restore','01-clean-install'],check=True)
subprocess.run([vbox,'modifyvm','DevOps','--cpus','1','--memory','3072'],check=True)
subprocess.run([vbox,'startvm','DevOps','--type','headless'],check=True)
time.sleep(35)
c,a=connect();s=c.open_sftp();s.put(str(Path.home()/'.ssh/devops_vm.pub'),'/tmp/devops_vm.pub');s.put(str(ROOT/'scripts/audit.sh'),'/tmp/audit.sh');s.close()
script='export SKIP_PACKAGES=1\n'+(ROOT/'lab_tools/p5-setup.sh').read_text()+'\n'+(ROOT/'lab_tools/p5-harden.sh').read_text()
rc,out,err=execute(c,a,script,True);c.close()
if rc:raise RuntimeError(out+err)
subprocess.run([vbox,'controlvm','DevOps','natpf1','delete','devops-ssh'],check=True)
subprocess.run([vbox,'controlvm','DevOps','natpf1','devops-ssh,tcp,127.0.0.1,2222,,2222'],check=True)
c,a=connect('devops');rc,checks,errors=execute(c,a,'bash /tmp/audit.sh',True);c.close()
elapsed=time.monotonic()-started
text=out+'\n'+err+'\nVERIFICATION AFTER RESTORE\n'+checks+errors+f'\naudit_exit={rc}\nrestore_seconds={elapsed:.1f}\n'
(ROOT/'reports/practices-5-8/evidence/p6-restoration.txt').write_text(text,encoding='utf-8')
print(checks);print(f'audit_exit={rc}; restore_seconds={elapsed:.1f}',flush=True)
if rc or elapsed>=600:raise RuntimeError('Restore acceptance check failed')
