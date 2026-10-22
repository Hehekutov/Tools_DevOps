"""Export with the installed Microsoft Word, using a private COM instance."""
from pathlib import Path
import sys
import pythoncom,win32com.client
from pdf2image import convert_from_path
sys.stdout.reconfigure(encoding='utf-8')
pythoncom.CoInitialize()
app=win32com.client.DispatchEx('Word.Application');app.Visible=False;app.DisplayAlerts=0
try:
    paths=[Path(x).resolve() for x in sys.argv[1:]]
    for path in paths:
        doc=app.Documents.Open(str(path),ReadOnly=True,AddToRecentFiles=False)
        pdf=path.with_suffix('.pdf')
        try:doc.ExportAsFixedFormat(str(pdf),17,OpenAfterExport=False)
        finally:doc.Close(0)
        qa=path.parents[2]/'tmp'/'report-qa'/path.stem;qa.mkdir(parents=True,exist_ok=True)
        pages=convert_from_path(str(pdf),dpi=120)
        for i,page in enumerate(pages,1):page.save(qa/f'page-{i}.png')
        print(f'{pdf} pages={len(pages)}',flush=True)
finally:
    app.Quit();pythoncom.CoUninitialize()
