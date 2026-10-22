"""Capture concise, real terminal checks for a report stage."""
import sys,json,subprocess,time
from pathlib import Path
from remote import connect,execute,ROOT
sys.stdout.reconfigure(encoding='utf-8')
spec=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
c,a=connect('devops');s=c.open_sftp()
execute(c,a,'font=$(find /usr/share/consolefonts -name "Lat15-TerminusBold24x12.psf.gz" -print -quit); if [ -n "$font" ]; then setfont -C /dev/tty1 "$font"; fi',True)
for name,body in spec.items():
    with s.open('/tmp/lab-console-check.sh','w') as f:f.write('set -x\n'+body+'\n')
    rc,out,err=execute(c,a,"chvt 1; printf '\\033c' > /dev/tty1; bash /tmp/lab-console-check.sh 2>&1 | tee /dev/tty1",True)
    (ROOT/f'reports/practices-5-8/evidence/{name}.txt').write_text(out+err,encoding='utf-8')
    time.sleep(.3)
    subprocess.run([r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe','controlvm','DevOps','screenshotpng',str(ROOT/f'reports/practices-5-8/evidence/{name}.png')],check=True)
    print(name,'captured',flush=True)
s.close();c.close()
