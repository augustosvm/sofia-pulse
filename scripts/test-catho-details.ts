import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
puppeteer.use(StealthPlugin());

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

async function test() {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.goto('https://www.catho.com.br/vagas/desenvolvedor/', {
    waitUntil: 'networkidle0',
    timeout: 60000,
  });

  await delay(8000);

  const jobs = await page.evaluate(() => {
    const results: any[] = [];
    const jobCards = document.querySelectorAll('article, li, div[class*="card"]');
    
    jobCards.forEach((card, i) => {
      if (i >= 5) return; // First 5
      
      const titleEl = card.querySelector('a[href*="/vagas/"]');
      const companyEl = card.querySelector('span, p, div[class*="company"], div[class*="empresa"]');
      const locationEl = card.querySelector('span[class*="local"], div[class*="location"], span[class*="city"]');
      
      if (titleEl) {
        results.push({
          title: titleEl.textContent?.trim(),
          company: companyEl?.textContent?.trim() || 'Not found',
          location: locationEl?.textContent?.trim() || 'Not found',
          html: card.innerHTML.substring(0, 500),
        });
      }
    });
    
    return results;
  });

  console.log(JSON.stringify(jobs, null, 2));
  await browser.close();
}

test();
