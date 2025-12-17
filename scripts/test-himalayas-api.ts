#!/usr/bin/env npx tsx
/**
 * Test Himalayas API to debug schema parsing
 */

import axios from 'axios';

const HIMALAYAS_API = 'https://himalayas.app/jobs/api';

async function testHimalayasAPI() {
    console.log('🧪 Testing Himalayas API...\n');

    try {
        const response = await axios.get(HIMALAYAS_API, {
            timeout: 15000,
            headers: {
                'User-Agent': 'Sofia-Pulse-Jobs-Collector/1.0'
            }
        });

        console.log(`✅ API Response: ${response.status}`);
        console.log(`\n📦 Response structure:`);
        console.log(`   Type: ${typeof response.data}`);
        console.log(`   Keys: ${Object.keys(response.data).join(', ')}`);

        // Check if jobs array exists
        if (response.data.jobs) {
            console.log(`\n✅ Jobs array found: ${response.data.jobs.length} jobs`);

            // Analyze first job structure
            if (response.data.jobs.length > 0) {
                const firstJob = response.data.jobs[0];
                console.log(`\n📋 First job structure:`);
                console.log(JSON.stringify(firstJob, null, 2));

                // Check company field
                console.log(`\n🏢 Company field analysis:`);
                console.log(`   Type: ${typeof firstJob.company}`);
                if (typeof firstJob.company === 'object') {
                    console.log(`   Keys: ${Object.keys(firstJob.company).join(', ')}`);
                    console.log(`   company.name: ${firstJob.company.name || 'UNDEFINED'}`);
                } else {
                    console.log(`   Value: ${firstJob.company}`);
                }
            }
        } else {
            console.log(`\n❌ No 'jobs' array in response`);
            console.log(`   Full response: ${JSON.stringify(response.data).substring(0, 500)}...`);
        }

    } catch (error: any) {
        if (axios.isAxiosError(error)) {
            console.log(`❌ API Error: ${error.response?.status} - ${error.message}`);
            if (error.response?.data) {
                console.log(`   Response: ${JSON.stringify(error.response.data).substring(0, 500)}`);
            }
        } else {
            console.log(`❌ Error: ${error.message}`);
        }
    }
}

testHimalayasAPI()
    .then(() => process.exit(0))
    .catch(err => {
        console.error('Fatal error:', err);
        process.exit(1);
    });
