"""Package only the three verified PDF/DOCX pairs, never server credentials."""
from pathlib import Path
import json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
validation=json.loads((ROOT/'tmp/report-qa/validation.json').read_text(encoding='utf-8'))
index=ROOT/'reports/practices-5-7.md'
text=index.read_text(encoding='utf-8')
import re
for n in (5,6,7):
    rows=text.splitlines()
    for i,line in enumerate(rows):
        if line.startswith(f'| №{n}.'):
            rows[i]=re.sub(r'\d+ страниц[а-я]*,',str(validation[str(n)]['pages'])+' страниц,',line)
    text='\n'.join(rows)+'\n'
index.write_text(text,encoding='utf-8')
files=[]
for n in (5,6,7):
    dst=ROOT/f'reports/practice-{n}';dst.mkdir(exist_ok=True)
    for ext in ('pdf','docx'):
        source=ROOT/f'output/reports/Практическая работа {n}.{ext}'
        target=dst/source.name;shutil.copy2(source,target);files.append(target)
shutil.copy2(ROOT/'tmp/report-qa/validation.json',ROOT/'reports/report-validation.json')
archive=ROOT/'reports/Практические работы 5–7.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for path in files:z.write(path,path.relative_to(ROOT/'reports').as_posix())
    z.write(ROOT/'reports/practices-5-7.md','README.md')
    guide=ROOT/'reports/Как сдавать практики 5–7.md'
    if guide.exists():z.write(guide,guide.name)
print('Packaged 3 PDF and 3 DOCX files; archive size:',archive.stat().st_size)
