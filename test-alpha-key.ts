#!/usr/bin/env tsx

import * as dotenv from 'dotenv';

dotenv.config();

console.log('ALPHA_VANTAGE_API_KEY:', process.env.ALPHA_VANTAGE_API_KEY || '❌ UNDEFINED');
console.log('Length:', process.env.ALPHA_VANTAGE_API_KEY?.length || 0);
