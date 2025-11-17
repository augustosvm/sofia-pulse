#!/usr/bin/env tsx

import * as dotenv from 'dotenv';

console.log('🔍 DEBUG - NASDAQ Environment Check\n');

console.log('📁 Antes de dotenv.config():');
console.log('  ALPHA_VANTAGE_API_KEY:', process.env.ALPHA_VANTAGE_API_KEY || '❌ UNDEFINED');
console.log('  DB_USER:', process.env.DB_USER || '❌ UNDEFINED');
console.log('');

console.log('⚙️  Executando dotenv.config()...');
const result = dotenv.config();
console.log('  Status:', result.error ? `❌ ${result.error.message}` : '✅ Success');
console.log('');

console.log('📁 Depois de dotenv.config():');
console.log('  ALPHA_VANTAGE_API_KEY:', process.env.ALPHA_VANTAGE_API_KEY || '❌ UNDEFINED');
console.log('  DB_USER:', process.env.DB_USER || '❌ UNDEFINED');
console.log('');

const API_KEY = process.env.ALPHA_VANTAGE_API_KEY;

console.log('🔑 Testando como o script NASDAQ faz:');
console.log('  const API_KEY = process.env.ALPHA_VANTAGE_API_KEY;');
console.log('  API_KEY:', API_KEY || '❌ UNDEFINED');
console.log('  !API_KEY:', !API_KEY);
console.log('');

if (!API_KEY) {
  console.log('❌ Script NASDAQ vai falhar aqui!');
} else {
  console.log('✅ Script NASDAQ vai continuar');
  console.log('  Length:', API_KEY.length);
  console.log('  First 4 chars:', API_KEY.substring(0, 4));
}
