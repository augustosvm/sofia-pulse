#!/usr/bin/env npx tsx
/**
 * Test WeWorkRemotely API to debug 406 error
 */

import axios from 'axios';

const WWR_API = 'https://weworkremotely.com/remote-jobs.json';

async function testWWRAPI() {
    console.log('🧪 Testing WeWorkRemotely API...\n');

    // Test 1: Simple request (current implementation)
    console.log('Test 1: Simple request with User-Agent');
    try {
        const response1 = await axios.get(WWR_API, {
            timeout: 15000,
            headers: {
                'User-Agent': 'Sofia-Pulse-Jobs-Collector/1.0'
            }
        });
        console.log(`✅ Success: ${response1.status}`);
        console.log(`   Jobs found: ${Array.isArray(response1.data) ? response1.data.length : 'N/A'}`);
    } catch (error: any) {
        console.log(`❌ Failed: ${error.response?.status || error.code} - ${error.message}`);
    }

    // Test 2: Browser-like headers
    console.log('\nTest 2: Browser-like headers');
    try {
        const response2 = await axios.get(WWR_API, {
            timeout: 15000,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://weworkremotely.com/',
                'Origin': 'https://weworkremotely.com'
            }
        });
        console.log(`✅ Success: ${response2.status}`);
        console.log(`   Jobs found: ${Array.isArray(response2.data) ? response2.data.length : 'N/A'}`);
    } catch (error: any) {
        console.log(`❌ Failed: ${error.response?.status || error.code} - ${error.message}`);
    }

    // Test 3: Minimal headers
    console.log('\nTest 3: Minimal headers');
    try {
        const response3 = await axios.get(WWR_API, {
            timeout: 15000,
            headers: {
                'Accept': 'application/json'
            }
        });
        console.log(`✅ Success: ${response3.status}`);
        console.log(`   Jobs found: ${Array.isArray(response3.data) ? response3.data.length : 'N/A'}`);
    } catch (error: any) {
        console.log(`❌ Failed: ${error.response?.status || error.code} - ${error.message}`);
    }

    // Test 4: No custom headers
    console.log('\nTest 4: No custom headers (axios defaults)');
    try {
        const response4 = await axios.get(WWR_API, {
            timeout: 15000
        });
        console.log(`✅ Success: ${response4.status}`);
        console.log(`   Jobs found: ${Array.isArray(response4.data) ? response4.data.length : 'N/A'}`);
    } catch (error: any) {
        console.log(`❌ Failed: ${error.response?.status || error.code} - ${error.message}`);
    }
}

testWWRAPI()
    .then(() => process.exit(0))
    .catch(err => {
        console.error('Fatal error:', err);
        process.exit(1);
    });
