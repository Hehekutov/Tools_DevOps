"""Install an isolated rsync client without changing Git or WSL settings."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,re,hashlib,tarfile,io,shutil,os,sys
import zstandard
sys.stdout.reconfigure(encoding='utf-8')
dest=Path(os.environ['LOCALAPPDATA'])/'CodexDevOps/rsync/bin';dest.mkdir(parents=True,exist_ok=True)
for dll in Path(r'C:/Program Files/Git/usr/bin').glob('*.dll'):shutil.copy2(dll,dest/dll.name)
names=['rsync','libiconv','libidn2','liblz4','libopenssl','libxxhash','libzstd','popt','libunistring','gcc-libs','msys2-runtime']
def fetch(name):
    html=urllib.request.urlopen('https://packages.msys2.org/packages/'+name,timeout=30).read().decode()
    links=re.findall(r'href="(https://mirror.msys2.org/msys/x86_64/[^" ]+\.pkg\.tar\.zst)"',html)
    checksum=re.findall(r'[0-9a-f]{64}',html)[0]
    data=urllib.request.urlopen(links[0],timeout=45).read()
    assert hashlib.sha256(data).hexdigest()==checksum,name
    raw=zstandard.ZstdDecompressor().decompress(data,max_output_size=100_000_000)
    return name,raw
with ThreadPoolExecutor(max_workers=4) as pool:
    archives=list(pool.map(fetch,names))
for name,raw in archives:
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for member in archive:
            if member.isfile() and member.name.startswith('usr/bin/'):
                target=dest/Path(member.name).name
                target.write_bytes(archive.extractfile(member).read())
    print('Verified and installed',name,flush=True)
print(dest)
