#!/usr/bin/env npx tsx
/**
 * Test WeWorkRemotely NEW API endpoint
 */

import axios from 'axios';

const WWR_API_OLD = 'https://weworkremotely.com/remote-jobs.json';
const WWR_API_NEW = 'https://weworkremotely.com/api/v1/remote-jobs/';

async function testWWRNewAPI() {
    console.log('🧪 Testing WeWorkRemotely NEW API Endpoint...\n');

    // Test new endpoint
    console.log('Test: New API endpoint (v1)');
    try {
        const response = await axios.get(WWR_API_NEW, {
            timeout: 15000,
            headers: {
                'User-Agent': 'Sofia-Pulse-Jobs-Collector/1.0',
                'Accept': 'application/json'
            }
        });
        console.log(`✅ Success: ${response.status}`);
        console.log(`   Response type: ${typeof response.data}`);
        console.log(`   Keys: ${Object.keys(response.data).join(', ')}`);

        // Check structure
        if (Array.isArray(response.data)) {
            console.log(`   Jobs found: ${response.data.length}`);
            if (response.data.length > 0) {
                console.log(`\n📋 First job structure:`);
                console.log(JSON.stringify(response.data[0], null, 2).substring(0, 1000));
            }
        } else if (response.data.jobs) {
            console.log(`   Jobs found: ${response.data.jobs.length}`);
            if (response.data.jobs.length > 0) {
                console.log(`\n📋 First job structure:`);
                console.log(JSON.stringify(response.data.jobs[0], null, 2).substring(0, 1000));
            }
        }
    } catch (error: any) {
        console.log(`❌ Failed: ${error.response?.status || error.code} - ${error.message}`);
    }
}

testWWRNewAPI()
    .then(() => process.exit(0))
    .catch(err => {
        console.error('Fatal error:', err);
        process.exit(1);
    });
