#!/usr/bin/env npx tsx
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const ADZUNA_APP_ID = process.env.ADZUNA_APP_ID;
const ADZUNA_API_KEY = process.env.ADZUNA_API_KEY;

const countries = [
  {code: 'gb', name: 'United Kingdom'},
  {code: 'fr', name: 'France'},
  {code: 'br', name: 'Brazil'},
];

async function debugMultipleCountries() {
  for (const country of countries) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`🔍 ${country.name} (${country.code})\n`);

    try {
      const url = `https://api.adzuna.com/v1/api/jobs/${country.code}/search/1`;
      const response = await axios.get(url, {
        params: {
          app_id: ADZUNA_APP_ID,
          app_key: ADZUNA_API_KEY,
          what: 'developer',
          results_per_page: 3,
        },
        timeout: 10000
      });

      const jobs = response.data.results;
      console.log(`Found ${jobs.length} jobs\n`);

      jobs.forEach((job: any, index: number) => {
        console.log(`Job ${index + 1}: ${job.title}`);
        console.log(`  display_name: "${job.location.display_name}"`);
        console.log(`  area: [${job.location.area.map((a: string) => `"${a}"`).join(', ')}]`);
        console.log(`  area.length: ${job.location.area.length}\n`);
      });
    } catch (error: any) {
      console.error(`❌ Error: ${error.message}\n`);
    }

    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

debugMultipleCountries();
