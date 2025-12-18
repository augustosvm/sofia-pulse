import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

async function test() {
  console.log('🔍 Testing Catho HTML structure...');
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  try {
    const page = await browser.newPage();
    console.log('📄 Navigating to Catho...');
    
    await page.goto('https://www.catho.com.br/vagas/desenvolvedor/', {
      waitUntil: 'networkidle0',
      timeout: 60000,
    });

    console.log('⏳ Waiting for content...');
    await delay(8000);

    // Extract all possible job elements
    const jobs = await page.evaluate(() => {
      const results: any[] = [];
      
      // Try multiple possible selectors
      const allLinks = document.querySelectorAll('a[href*="vaga"], a[href*="job"]');
      
      allLinks.forEach((link, i) => {
        if (i < 10) { // First 10
          const href = link.getAttribute('href');
          const text = link.textContent?.trim();
          results.push({ href, text: text?.substring(0, 100) });
        }
      });
      
      return results;
    });

    console.log('\n=== FOUND LINKS ===');
    console.log(JSON.stringify(jobs, null, 2));
    console.log(`\nTotal links: ${jobs.length}`);

  } finally {
    await browser.close();
  }
}

test().catch(console.error);
