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
        doc=app.Documents.Open(str(path),ReadOnly=False,AddToRecentFiles=False)
        pdf=path.with_suffix('.pdf')
        try:
            assert doc.TablesOfContents.Count==1,'Expected an automatic table of contents'
            for _ in range(3):
                doc.Fields.Update()
                for toc in doc.TablesOfContents:
                    toc.Update()
                    toc.Range.Font.Name='Times New Roman';toc.Range.Font.Size=12;toc.Range.Font.Color=0
                    toc.Range.ParagraphFormat.LineSpacingRule=0
                    toc.Range.ParagraphFormat.SpaceBefore=0;toc.Range.ParagraphFormat.SpaceAfter=3
                doc.Repaginate()
            doc.Repaginate()
            for toc in doc.TablesOfContents:
                toc.UpdatePageNumbers();toc.Range.Font.Color=0
            doc.Save()
            doc.ExportAsFixedFormat(str(pdf),17,OpenAfterExport=False,CreateBookmarks=1)
        finally:doc.Close(0)
        qa=path.parents[2]/'tmp'/'report-qa'/path.stem;qa.mkdir(parents=True,exist_ok=True)
        pages=convert_from_path(str(pdf),dpi=120)
        for i,page in enumerate(pages,1):page.save(qa/f'page-{i}.png')
        print(f'{pdf} pages={len(pages)}',flush=True)
finally:
    app.Quit();pythoncom.CoUninitialize()
