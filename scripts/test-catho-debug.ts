import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

async function test() {
  console.log('🔍 Testing Catho...');
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  console.log('📄 Loading page...');
  await page.goto('https://www.catho.com.br/vagas/desenvolvedor/', {
    waitUntil: 'networkidle2',
    timeout: 45000,
  });

  await page.waitForTimeout(5000);

  const html = await page.content();
  console.log('HTML length:', html.length);
  
  const selectors = [
    'article', '.job-card', '[data-testid]', 'li',
    'a[href*="/vaga"]', 'h2', 'h3', '.card', 'div[class*="job"]'
  ];

  console.log('\n=== TESTING SELECTORS ===');
  for (const sel of selectors) {
    const count = await page.$$eval(sel, els => els.length).catch(() => 0);
    if (count > 0) console.log(`✅ ${sel}: ${count}`);
  }
  
  await browser.close();
  console.log('Done!');
}

test();
