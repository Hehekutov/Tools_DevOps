"""Create a consistent disk snapshot while the teaching VM is shut down."""
import subprocess,time,argparse
from remote import connect,execute
p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args()
vbox=r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
c,auth=connect('devops');execute(c,auth,'systemctl poweroff',True);c.close()
for _ in range(30):
    info=subprocess.check_output([vbox,'showvminfo','DevOps','--machinereadable'],text=True,encoding='utf-8')
    if 'VMState="poweroff"' in info:break
    time.sleep(1)
else:raise RuntimeError('Guest did not shut down normally; snapshot was not taken')
subprocess.run([vbox,'snapshot','DevOps','take',a.name,'--description','Consistent disk snapshot of the powered-off lab VM'],check=True)
subprocess.run([vbox,'startvm','DevOps','--type','headless'],check=True)
# Give systemd time to start SSH; TCP polling would consume the UFW rate limit.
time.sleep(30)
print('VM restarted and boot grace period completed',flush=True)
