"""Capture real VirtualBox console output after executing a short verification script."""
from pathlib import Path
import argparse,subprocess,time,sys
from remote import connect,execute,ROOT
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--script');p.add_argument('--command');a=p.parse_args()
sys.stdout.reconfigure(encoding='utf-8')
body=Path(a.script).read_text(encoding='utf-8') if a.script else a.command
c,auth=connect('devops');s=c.open_sftp()
with s.open('/tmp/lab-console-check.sh','w') as f:f.write('set -x\n'+body+'\n')
s.close()
rc,out,err=execute(c,auth,"chvt 1; printf '\\033c' > /dev/tty1; bash /tmp/lab-console-check.sh 2>&1 | tee /dev/tty1",True)
e=ROOT/'reports/practices-5-8/evidence'
(e/(a.name+'.txt')).write_text(out+err,encoding='utf-8')
time.sleep(.5)
subprocess.run([r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe','controlvm','DevOps','screenshotpng',str(e/(a.name+'.png'))],check=True)
print(out);c.close()
