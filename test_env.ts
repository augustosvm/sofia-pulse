
import { fileURLToPath } from 'url';

console.log('require type:', typeof require !== 'undefined' ? typeof require : 'undefined');
if (typeof require !== 'undefined') {
    console.log('require.main type:', typeof require.main !== 'undefined' ? typeof require.main : 'undefined');
    console.log('require.main === module:', require.main === (global as any).module);
}

console.log('import.meta.url:', import.meta.url);
console.log('process.argv[1]:', process.argv[1]);
