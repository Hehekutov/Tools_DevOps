"""Check exported documents and create contact sheets for visual inspection."""
from pathlib import Path
import json,re,sys,tempfile,zipfile
from PIL import Image,ImageDraw
from pypdf import PdfReader
from docx import Document
from docx.shared import Cm,Pt

ROOT=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8')
auth=Path(tempfile.gettempdir())/'codex-devops-auth.json'
secret=json.loads(auth.read_text(encoding='utf-8'))['password'] if auth.exists() else None
result={}
for n,question_count in [(5,14),(6,14),(7,8)]:
    stem=f'Практическая работа {n}';pdf=ROOT/'output/reports'/(stem+'.pdf');docx=pdf.with_suffix('.docx')
    reader=PdfReader(pdf);texts=[p.extract_text() or '' for p in reader.pages];compact=re.sub(r'\s+','',''.join(texts))
    for needle in ['Кудояров Денис Рустемович','ЭФБО-18-24','https://github.com/Hehekutov/Tools_DevOps/pull/3','Ответы на контрольные вопросы']:
        assert re.sub(r'\s+','',needle) in compact,(n,needle)
    if secret:assert secret not in ''.join(texts)
    assert 'Проверяющий' not in ''.join(texts) and 'Проверил:' not in ''.join(texts)
    assert not re.search(r'Error!|Ошибка!|Bookmark not defined', ''.join(texts),re.I)
    document=Document(docx)
    assert sum(p.style.name=='Heading 2' and re.match(r'^3[.]\d+ ',p.text) is not None for p in document.paragraphs)==question_count
    normal=document.styles['Normal'];assert normal.font.name=='Times New Roman' and normal.font.size==Pt(14)
    assert normal.paragraph_format.line_spacing==1.5 and abs(normal.paragraph_format.first_line_indent-Cm(1.25))<1000
    section=document.sections[0]
    for actual,expected in [(section.left_margin,3),(section.right_margin,1.5),(section.top_margin,2),(section.bottom_margin,2)]:
        assert abs(actual-Cm(expected))<1000
    assert 'СОДЕРЖАНИЕ' in compact and 'СПИСОКИСПОЛЬЗОВАННЫХИСТОЧНИКОВ' in compact
    assert compact.count('ВВЕДЕНИЕ')>=2,'TOC was not populated'
    with zipfile.ZipFile(docx) as archive:
        if secret:assert all(secret.encode() not in archive.read(f) for f in archive.namelist())
    folder=ROOT/'tmp/report-qa'/stem
    for start in range(0,len(reader.pages),6):
        sheet=Image.new('RGB',(1260,1800),'#b5bac0');draw=ImageDraw.Draw(sheet)
        for j,i in enumerate(range(start,min(start+6,len(reader.pages)))):
            im=Image.open(folder/f'page-{i+1}.png');im.thumbnail((600,555))
            x=(j%2)*630+(630-im.width)//2;y=(j//2)*600+30
            sheet.paste(im,(x,y));draw.text((x,y-20),f'Practice {n} / page {i+1}',fill='black')
        sheet.save(folder/f'final-contact-{start//6+1}.jpg',quality=90)
    result[n]={'pages':len(reader.pages),'questions':question_count,'text_and_secret_checks':'passed','format':'ГОСТ 7.32-2017, учебный отчёт','body_font':'Times New Roman 14','line_spacing':1.5,'paragraph_indent_cm':1.25,'margins_mm':{'left':30,'right':15,'top':20,'bottom':20},'reviewer_field':'absent','toc':'updated and saved'}
(ROOT/'tmp/report-qa/validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
