"""Fetch stalled installer packages over HTTPS and verify repository checksums."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import re,hashlib,urllib.request,sys
from remote import connect,execute
sys.stdout.reconfigure(encoding='utf-8')
c,a=connect('ubuntu-server')
rc,text,err=execute(c,a,"chroot /target apt-get --print-uris --yes install linux-generic 2>/dev/null",True)
_,names,_=execute(c,a,"find /target/var/cache/apt/archives/partial -name '*.deb' -printf '%f\\n'",True)
stalled=set(names.splitlines());jobs=[]
for url,name,size,md5 in re.findall(r"^'(http[^']+)' (\S+) (\d+) MD5Sum:(\w+)",text,re.M):
    if name in stalled:jobs.append((url.replace('http://nl.archive.ubuntu.com','https://archive.ubuntu.com'),name,int(size),md5))
p=Path('tmp/packages');p.mkdir(parents=True,exist_ok=True)
def fetch(job):
    url,name,size,md5=job;path=p/name
    with urllib.request.urlopen(url,timeout=45) as r,path.open('wb') as f:
        while data:=r.read(1024*1024):f.write(data)
    if path.stat().st_size!=size or hashlib.md5(path.read_bytes()).hexdigest()!=md5:raise ValueError('Checksum mismatch '+name)
    return path
with ThreadPoolExecutor(max_workers=3) as pool:
    paths=list(pool.map(fetch,jobs))
for path in paths:
    s=c.open_sftp();s.put(str(path),'/tmp/'+path.name);s.close()
    rc,out,err=execute(c,a,f"cp '/tmp/{path.name}' '/target/var/cache/apt/archives/{path.name}'; cp '/tmp/{path.name}' '/target/var/cache/apt/archives/partial/{path.name}'; chmod 644 '/target/var/cache/apt/archives/partial/{path.name}'",True)
    print('Verified and supplied',path.name,flush=True)
c.close()
