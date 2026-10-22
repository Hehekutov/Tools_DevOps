"""Check exported documents and create contact sheets for visual inspection."""
from pathlib import Path
import json,re,sys,tempfile,zipfile
from PIL import Image,ImageDraw
from pypdf import PdfReader
from docx import Document

ROOT=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8')
secret=json.loads((Path(tempfile.gettempdir())/'codex-devops-auth.json').read_text(encoding='utf-8'))['password']
result={}
for n,question_count in [(5,14),(6,14),(7,8)]:
    stem=f'Практическая работа {n}';pdf=ROOT/'output/reports'/(stem+'.pdf');docx=pdf.with_suffix('.docx')
    reader=PdfReader(pdf);texts=[p.extract_text() or '' for p in reader.pages];compact=re.sub(r'\s+','',''.join(texts))
    for needle in ['Кудояров Денис Рустемович','ЭФБО-18-24','https://github.com/Hehekutov/Tools_DevOps/pull/3','Ответы на контрольные вопросы']:
        assert re.sub(r'\s+','',needle) in compact,(n,needle)
    assert secret not in ''.join(texts)
    document=Document(docx)
    assert sum(p.style.name=='Heading 2' for p in document.paragraphs)==question_count
    with zipfile.ZipFile(docx) as archive:
        assert all(secret.encode() not in archive.read(f) for f in archive.namelist())
    folder=ROOT/'tmp/report-qa'/stem
    for start in range(0,len(reader.pages),6):
        sheet=Image.new('RGB',(1260,1800),'#b5bac0');draw=ImageDraw.Draw(sheet)
        for j,i in enumerate(range(start,min(start+6,len(reader.pages)))):
            im=Image.open(folder/f'page-{i+1}.png');im.thumbnail((600,555))
            x=(j%2)*630+(630-im.width)//2;y=(j//2)*600+30
            sheet.paste(im,(x,y));draw.text((x,y-20),f'Practice {n} / page {i+1}',fill='black')
        sheet.save(folder/f'final-contact-{start//6+1}.jpg',quality=90)
    result[n]={'pages':len(reader.pages),'questions':question_count,'text_and_secret_checks':'passed'}
(ROOT/'tmp/report-qa/validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
