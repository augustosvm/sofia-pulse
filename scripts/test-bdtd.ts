
import axios from 'axios';
import { bdtdPapers } from './configs/research-papers-config.js';

async function testBdtd() {
    console.log('🧪 Testing BDTD Collector...');
    console.log(`URL: ${bdtdPapers.url}`);

    try {
        const response = await axios.get(bdtdPapers.url as string, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            timeout: 30000
        });

        console.log(`✅ Status: ${response.status}`);
        console.log(`📦 Data Length: ${response.data.length}`);

        // Preview data
        console.log('📄 Preview (first 500 chars):');
        console.log(response.data.substring(0, 500));

        // Test parsing
        console.log('🔄 Testing Parse Logic...');
        // Mock environment
        const papers = await bdtdPapers.parseResponse(response.data, process.env);
        console.log(`✅ Parsed ${papers.length} papers`);

        if (papers.length > 0) {
            console.log('📝 First Paper:');
            console.log(JSON.stringify(papers[0], null, 2));
        } else {
            console.log('⚠️ No papers parsed. Check Regex.');
        }

    } catch (error: any) {
        console.error('❌ Error:', error.message);
        if (error.response) {
            console.error('Status:', error.response.status);
            console.error('Data:', error.response.data);
        }
    }
}

testBdtd();
