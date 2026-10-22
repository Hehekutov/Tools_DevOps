const { chromium } = require('C:/Users/денис/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const root = path.resolve(__dirname, '..');
  const output = path.join(root, 'reports/practices-5-8/evidence');
  const browser = await chromium.launch({channel:'msedge', headless:true,args:['--host-resolver-rules=MAP devops.local 127.0.0.1']});
  // Lab certificate is self-signed. Certificate validation is tested separately by curl --cacert.
  const context = await browser.newContext({ignoreHTTPSErrors:true, viewport:{width:1280,height:800}});
  const page = await context.newPage();
  for (const [name,url] of [['p6-browser-site','http://devops.local/'],['p6-browser-404','https://devops.local/no-such-page'],['p7-browser-app','https://devops.local/app/']]) {
    if (process.argv[2] && !name.startsWith(process.argv[2])) continue;
    const response = await page.goto(url,{waitUntil:'networkidle',timeout:30000});
    await page.screenshot({path:path.join(output,name+'.png'),fullPage:true});
    fs.writeFileSync(path.join(output,name+'.txt'),`Requested: ${url}\nFinal URL: ${page.url()}\nHTTP status: ${response.status()}\nTitle: ${await page.title()}\n\n${await page.locator('body').innerText()}`);
  }
  await browser.close();
})();
