#!/usr/bin/env npx tsx
/**
 * Debug Adzuna API response to understand location structure
 */
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const ADZUNA_APP_ID = process.env.ADZUNA_APP_ID;
const ADZUNA_API_KEY = process.env.ADZUNA_API_KEY;

async function debugAdzunaAPI() {
  console.log('\n🔍 Debugging Adzuna API Location Structure\n');

  const url = 'https://api.adzuna.com/v1/api/jobs/us/search/1';
  const response = await axios.get(url, {
    params: {
      app_id: ADZUNA_APP_ID,
      app_key: ADZUNA_API_KEY,
      what: 'developer',
      results_per_page: 5,
    },
  });

  const jobs = response.data.results;
  console.log(`Found ${jobs.length} jobs\n`);

  jobs.forEach((job: any, index: number) => {
    console.log(`─`.repeat(80));
    console.log(`\nJob ${index + 1}: ${job.title}`);
    console.log(`Company: ${job.company.display_name}`);
    console.log(`\nLocation Object:`);
    console.log(`  display_name: "${job.location.display_name}"`);
    console.log(`  area: [${job.location.area.map((a: string) => `"${a}"`).join(', ')}]`);
    console.log(`  area.length: ${job.location.area.length}`);
    console.log(`\nParsing:`);
    console.log(`  area[0]: "${job.location.area[0]}"`);
    if (job.location.area.length > 1) console.log(`  area[1]: "${job.location.area[1]}"`);
    if (job.location.area.length > 2) console.log(`  area[2]: "${job.location.area[2]}"`);
    if (job.location.area.length > 3) console.log(`  area[3]: "${job.location.area[3]}"`);
    console.log('');
  });

  console.log(`─`.repeat(80));
}

debugAdzunaAPI().catch(console.error);
