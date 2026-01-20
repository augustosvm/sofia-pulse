
export function dummy() {
    console.log('Dummy executed');
}

console.log('Checking execution...');
if (require.main === module) {
    console.log('!!! PROTECTED CODE EXECUTED !!!');
    dummy();
} else {
    console.log('Code protected - not main module');
}
