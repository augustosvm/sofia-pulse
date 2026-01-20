#!/usr/bin/env npx tsx
/**
 * Script para executar todos os coletores de Inteligência Editorial (Phase 7)
 * Frequência: Diária (Daily)
 */
import { spawn } from 'child_process';

const COLLECTORS = [
    { name: 'Stack Exchange Trends', script: 'collect-stackexchange-trends.ts' },
    { name: 'Docker Hub Stats', script: 'collect-docker-stats.ts' },
    { name: 'PapersWithCode Ingest', script: 'collect-paperswithcode.ts' },
];

async function runCollector(collector: { name: string; script: string }) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 Executando: ${collector.name}`);
    console.log('='.repeat(60));

    return new Promise<{ name: string; success: boolean; error: any }>((resolve) => {
        const cmd = 'npx';
        const args = ['tsx', `scripts/${collector.script}`];

        // Use shell: true for wider compatibility on Windows
        const child = spawn(cmd, args, { stdio: 'inherit', shell: true });

        child.on('close', (code) => {
            if (code === 0) {
                console.log(`✅ ${collector.name} concluído`);
                resolve({ name: collector.name, success: true, error: null });
            } else {
                console.error(`❌ ${collector.name} falhou com código ${code}`);
                resolve({ name: collector.name, success: false, error: `Exit code ${code}` });
            }
        });

        child.on('error', (err) => {
            console.error(`❌ ${collector.name} erro de execução:`, err);
            resolve({ name: collector.name, success: false, error: err });
        });
    });
}

async function main() {
    console.log('🧠 Executando Coletores de Inteligência (Editorial)');
    console.log('='.repeat(60));

    const results = [];

    for (const collector of COLLECTORS) {
        const result = await runCollector(collector);
        results.push(result);

        // Delay entre coletores para não sobrecarregar
        await new Promise(r => setTimeout(r, 2000));
    }

    console.log('\n' + '='.repeat(60));
    console.log('📊 RESUMO FINAL DE INTELIGÊNCIA');
    console.log('='.repeat(60));

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    console.log(`✅ Sucesso: ${successful.length}/${results.length}`);
    successful.forEach(r => console.log(`   - ${r.name}`));

    if (failed.length > 0) {
        console.log(`\n❌ Falhas: ${failed.length}/${results.length}`);
        failed.forEach(r => console.log(`   - ${r.name}`));
        process.exit(1); // Exit with error if any collector failed
    }

    console.log('='.repeat(60));
}

main();
