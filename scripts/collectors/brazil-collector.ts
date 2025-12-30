/**
 * Brazil Collector Bridge
 *
 * Executes Python scripts for Brazil Data Collectors.
 * Bridges the Unified TS Architecture with the specialized Python logic.
 */

import { spawn } from 'child_process';
import { BrazilCollectorConfig } from '../configs/brazil-config.js';

export async function runBrazilCLI(collectors: Record<string, BrazilCollectorConfig>) {
    const args = process.argv.slice(2);
    const collectorName = args[0];

    // Run all
    if (collectorName === '--all-brazil') {
        console.log('🇧🇷 Running ALL Brazil collectors...');
        for (const config of Object.values(collectors)) {
            await runPythonScript(config);
        }
        return;
    }

    // Run specific
    const config = collectors[collectorName];
    if (config) {
        await runPythonScript(config);
    } else {
        console.error(`❌ Unknown Brazil collector: ${collectorName}`);
        process.exit(1);
    }
}

async function runPythonScript(config: BrazilCollectorConfig): Promise<void> {
    console.log('');
    console.log(`📡 Starting ${config.displayName}...`);
    console.log(`📜 Script: ${config.scriptPath}`);
    console.log('='.repeat(50));

    return new Promise((resolve, reject) => {
        const pythonProcess = spawn('python', [config.scriptPath], {
            stdio: 'inherit', // Pipe logs directly to console (and thus to global logs)
        });

        pythonProcess.on('close', (code) => {
            if (code === 0) {
                console.log(`✅ ${config.displayName} completed successfully.`);
                resolve();
            } else {
                console.error(`❌ ${config.displayName} failed with code ${code}.`);
                reject(new Error(`Script exited with code ${code}`));
            }
        });

        pythonProcess.on('error', (err) => {
            console.error(`❌ Failed to start python script: ${err.message}`);
            reject(err);
        });
    });
}
