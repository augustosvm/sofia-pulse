#!/usr/bin/env npx tsx
import axios from 'axios';

async function debugHimalayas() {
  console.log('\n🔍 Debugging Himalayas API\n');

  const response = await axios.get('https://himalayas.app/jobs/api/feed', {
    params: {
      format: 'json',
      limit: 10,
    },
  });

  const jobs = response.data.items || [];
  console.log(`Found ${jobs.length} jobs\n`);

  jobs.forEach((job: any, index: number) => {
    console.log(`Job ${index + 1}: ${job.title}`);
    console.log(`  Company: ${job.companyName}`);
    console.log(`  locationRestrictions: ${JSON.stringify(job.locationRestrictions)}`);
    console.log(`  length: ${job.locationRestrictions?.length || 0}`);
    if (job.locationRestrictions) {
      job.locationRestrictions.forEach((loc: string, i: number) => {
        console.log(`    [${i}]: "${loc}"`);
      });
    }
    console.log('');
  });
}

debugHimalayas();
