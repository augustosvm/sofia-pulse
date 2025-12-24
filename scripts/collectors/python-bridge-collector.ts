/**
 * Universal Python Bridge Collector
 *
 * Executes ANY legacy Python script defined in legacy-python-config.ts.
 * Bridges the Unified TS Architecture with the specialized Python logic.
 */

import { spawn } from 'child_process';
import { PythonCollectorConfig } from '../configs/legacy-python-config.js';

export async function runPythonBridgeCLI(collectors: Record<string, PythonCollectorConfig>) {
    const args = process.argv.slice(2);
    const collectorName = args[0];

    // Run all (filtered by legacy flag)
    if (collectorName === '--all-legacy') {
        console.log('🐍 Running ALL Legacy Python collectors...');
        for (const config of Object.values(collectors)) {
            try {
                await runPythonScript(config);
            } catch (err) {
                console.error(`⚠️ Failed to run ${config.name}, continuing...`);
            }
        }
        return;
    }

    // Run specific
    const config = collectors[collectorName];
    if (config) {
        await runPythonScript(config);
    } else {
        // Not a legacy collector, ignore (will be handled by main collect.ts)
    }
}

async function runPythonScript(config: PythonCollectorConfig): Promise<void> {
    console.log('');
    console.log(`🐍 Starting Python Script for ${config.name}...`);
    console.log(`📜 Script: ${config.script}`);
    console.log('='.repeat(50));

    return new Promise((resolve, reject) => {
        const pythonProcess = spawn('python3', [config.script], {
            stdio: 'inherit', // Pipe logs directly to console
        });

        pythonProcess.on('close', (code) => {
            if (code === 0) {
                console.log(`✅ ${config.name} completed successfully.`);
                resolve();
            } else {
                console.error(`❌ ${config.name} failed with code ${code}.`);
                reject(new Error(`Script exited with code ${code}`));
            }
        });

        pythonProcess.on('error', (err) => {
            console.error(`❌ Failed to start python script: ${err.message}`);
            reject(err);
        });
    });
}
