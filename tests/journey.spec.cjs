const {test,expect}=require('@playwright/test'),fs=require('node:fs/promises');
const screenshot=async(page,name)=>{await fs.mkdir('verification/screenshots',{recursive:true});await page.screenshot({path:'verification/screenshots/'+name+'.jpg',type:'jpeg',quality:85,fullPage:true});};
async function reset(page){await page.getByRole('button',{name:'Reset demo data ↺',exact:true}).click();await page.getByRole('button',{name:'Reset sample data',exact:true}).click();await expect(page.locator('#confirm')).not.toBeVisible();}
for(const [mode,base] of [['flask','http://127.0.0.1:5000'],['static','http://127.0.0.1:8088']]){
 test(mode+' complete record workflows, validation, reset and evidence',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await expect(page.getByRole('heading',{name:'A clearer view of your fleet.',exact:true})).toBeVisible();await reset(page);await page.reload();
  if(mode==='static')await screenshot(page,'dashboard');
  for(const kind of ['vehicle','customer']){
   await page.locator('nav a[href="#'+(kind==='vehicle'?'vehicles':'customers')+'"]').click();
   if(mode==='static')await screenshot(page,kind==='vehicle'?'inventory':'customers');
   await page.getByRole('button',{name:'＋ Add '+kind,exact:true}).click();
   const label=kind==='vehicle'?'Model and category':'Sample customer name';
   await page.getByLabel(label,{exact:true}).fill(kind==='vehicle'?'Toyota Corolla · Compact':'Casey Example');await page.getByLabel('Vehicle reference',{exact:true}).fill('QA-DEMO');await page.getByLabel('Daily rate (€)',{exact:true}).fill('45');
   if(mode==='static'&&kind==='vehicle')await screenshot(page,'vehicle-form');
   await page.getByRole('button',{name:'Save '+kind+' →',exact:true}).dblclick();await expect(page.locator('#editor')).not.toBeVisible();await expect(page.locator('tbody tr').filter({hasText:kind==='vehicle'?'QA-DEMO':'Casey Example'})).toHaveCount(1);
   const identity=kind==='vehicle'?'QA-DEMO':'Casey Example';await page.getByRole('button',{name:'Edit '+identity,exact:true}).click();await page.getByLabel('Daily rate (€)',{exact:true}).fill('48');await page.getByRole('button',{name:'Save '+kind+' →',exact:true}).click();await expect(page.locator('#editor')).not.toBeVisible();await expect(page.locator('tbody tr').filter({hasText:identity})).toContainText('€48');
   if(mode==='static'&&kind==='vehicle')await screenshot(page,'completed-action');
   await page.reload();await expect(page.getByRole('button',{name:'Edit '+identity,exact:true})).toBeVisible();
   await page.getByRole('button',{name:'Delete '+identity,exact:true}).click();await page.getByRole('button',{name:'Cancel',exact:true}).click();await expect(page.getByRole('button',{name:'Edit '+identity,exact:true})).toBeVisible();
   await page.getByRole('button',{name:'Delete '+identity,exact:true}).click();await page.getByRole('button',{name:'Delete record',exact:true}).click();await expect(page.locator('#confirm')).not.toBeVisible();await expect(page.getByRole('button',{name:'Edit '+identity,exact:true})).toHaveCount(0);
  }
  await page.locator('nav a[href="#vehicles"]').click();await page.getByRole('button',{name:'＋ Add vehicle',exact:true}).click();await page.getByLabel('Model and category',{exact:true}).fill('Duplicate example');await page.getByLabel('Vehicle reference',{exact:true}).fill('DEMO-001');await page.getByLabel('Daily rate (€)',{exact:true}).fill('39');await page.getByRole('button',{name:'Save vehicle →',exact:true}).click();await expect(page.locator('#form-error')).toContainText('already exists');await expect(page.getByLabel('Model and category',{exact:true})).toHaveValue('Duplicate example');await page.getByRole('button',{name:'Cancel',exact:true}).click();
  await page.getByRole('searchbox',{name:'Search vehicles',exact:true}).fill('does-not-exist');await expect(page.getByText('No matching records.',{exact:true})).toBeVisible();await reset(page);await expect(page.locator('tbody tr')).toHaveCount(8);
  await page.setViewportSize({width:390,height:844});await page.locator('nav a[href="#dashboard"]').click();await expect(page.getByRole('heading',{name:'A clearer view of your fleet.',exact:true})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.keyboard.press('Control+Home');if(mode==='static')await screenshot(page,'mobile-dashboard');
  await page.locator('nav a[href="#customers"]').click();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.keyboard.press('Control+Home');if(mode==='static')await screenshot(page,'mobile-customers');expect(errors).toEqual([]);
 });
}
test('server failure preserves the vehicle form',async({page})=>{await page.goto('http://127.0.0.1:5000');await page.getByRole('button',{name:'＋ Add vehicle',exact:true}).click();await page.getByLabel('Model and category',{exact:true}).fill('Failure example');await page.getByLabel('Vehicle reference',{exact:true}).fill('FAIL-EXAMPLE');await page.getByLabel('Daily rate (€)',{exact:true}).fill('42');await page.route('**/cars',route=>route.request().method()==='POST'?route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Record storage is unavailable.'})}):route.continue());await page.getByRole('button',{name:'Save vehicle →',exact:true}).click();await expect(page.locator('#form-error')).toContainText('unavailable');await expect(page.getByLabel('Model and category',{exact:true})).toHaveValue('Failure example');});
