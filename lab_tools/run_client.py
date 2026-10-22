"""Run the isolated MSYS2 rsync client with a consistent runtime and path layout."""
from pathlib import Path
import os,sys,subprocess,shutil,argparse
sys.stdout.reconfigure(encoding='utf-8')
p=argparse.ArgumentParser();p.add_argument('script');p.add_argument('--log');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
bindir=Path(os.environ['LOCALAPPDATA'])/'CodexDevOps/rsync/bin'
for name in ['bash','sh','cygpath','env','chmod','ls','stat','grep','awk','sed','cat','cp','mv','rm','mkdir','find','sort','uniq','head','tail','sleep','printf','basename','dirname','uname','touch']:
    src=Path(r'C:/Program Files/Git/usr/bin')/(name+'.exe')
    if src.exists():shutil.copy2(src,bindir/src.name)
env=os.environ.copy()
env['PATH']=str(bindir)+os.pathsep+env['PATH']
env['HOME']=str(Path.home()).replace('\\','/')
script=Path(a.script).resolve()
cmd=[str(bindir/'bash.exe'),'--noprofile','--norc',str(root/'lab_tools/client-env.sh').replace('\\','/'),str(script).replace('\\','/')]
r=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
if a.log:Path(a.log).write_text(r.stdout,encoding='utf-8')
print(r.stdout);sys.exit(r.returncode)
