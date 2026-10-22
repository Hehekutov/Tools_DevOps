"""Exercise the five required deployment scenarios against the real lab VM."""
from pathlib import Path
import subprocess,sys,time,json
from remote import ROOT,connect,execute
sys.stdout.reconfigure(encoding='utf-8')
clone=ROOT/'tmp/deploy-client';evid=ROOT/'reports/practices-5-8/evidence'
c,a=connect('devops');results=[]
def git(*args):
    return subprocess.run(['git','-C',str(clone),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8').stdout
def run(label,args='',expected=0):
    script=ROOT/'tmp/deploy-case.sh'
    location=str(clone).replace('\\','/')
    script.write_text(f'#!/usr/bin/env bash\ncd "{location}"\nbash scripts/deploy.sh {args}\n',encoding='utf-8',newline='\n')
    r=subprocess.run([sys.executable,str(ROOT/'lab_tools/run_client.py'),str(script)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8')
    text=f'SCENARIO: {label}\n'+r.stdout+f'\nEXIT STATUS: {r.returncode}\n'
    (evid/f'p6-deploy-{len(results)+1}.txt').write_text(text,encoding='utf-8')
    results.append({'scenario':label,'expected':expected,'actual':r.returncode})
    print(text,flush=True)
    assert r.returncode==expected,label
index=clone/'site/index.html';original=index.read_text(encoding='utf-8')
try:
    run('dry-run','--dry-run',0)
    updated=original.replace('Содержимое доставлено средствами rsync.','Содержимое доставлено средствами rsync. Версия 2.')
    index.write_text(updated,encoding='utf-8',newline='\n')
    git('add','site/index.html');git('commit','-m','feat: publish second static site revision')
    run('committed update','',0)
    index.write_text(updated+'\n<!-- uncommitted test -->\n',encoding='utf-8',newline='\n')
    run('uncommitted update','',1)
    index.write_text(updated,encoding='utf-8',newline='\n')
    rc,out,err=execute(c,a,'systemctl stop nginx',True);assert rc==0
    run('nginx stopped','',1)
    execute(c,a,'systemctl start nginx',True)
    git('mv','site/index.html','site/index.missing');git('commit','-m','test: verify deployment refuses missing index')
    run('committed missing index','',1)
    git('mv','site/index.missing','site/index.html');git('commit','-m','fix: restore static index after deployment check')
    run('restored final state','',0)
finally:
    execute(c,a,'systemctl start nginx',True);c.close()
    (evid/'p6-deploy-cases.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
