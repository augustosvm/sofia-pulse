#!/usr/bin/env tsx
/**
 * Script para executar todos os coletores de vagas com keywords centralizadas
 */
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

const COLLECTORS = [
    { name: 'Adzuna', script: 'collect-jobs-adzuna.ts' },
    { name: 'Arbeitnow', script: 'collect-jobs-arbeitnow.ts' },
    { name: 'GitHub Jobs', script: 'collect-jobs-github.ts' },
    { name: 'Himalayas', script: 'collect-jobs-himalayas.ts' },
    { name: 'The Muse', script: 'collect-jobs-themuse.ts' },
    { name: 'USAJobs', script: 'collect-jobs-usajobs.ts' },
    { name: 'WeWorkRemotely', script: 'collect-jobs-weworkremotely.ts' },
];

async function runCollector(collector: { name: string; script: string }) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 Executando: ${collector.name}`);
    console.log('='.repeat(60));

    try {
        const { stdout, stderr } = await execAsync(`npx tsx scripts/${collector.script}`);
        console.log(stdout);
        if (stderr) console.error(stderr);
        console.log(`✅ ${collector.name} concluído`);
        return { name: collector.name, success: true, error: null };
    } catch (error) {
        console.error(`❌ ${collector.name} falhou:`, error);
        return { name: collector.name, success: false, error };
    }
}

async function main() {
    console.log('🎯 Executando todos os coletores de vagas');
    console.log('='.repeat(60));

    const results = [];

    for (const collector of COLLECTORS) {
        const result = await runCollector(collector);
        results.push(result);

        // Delay entre coletores para não sobrecarregar
        await new Promise(r => setTimeout(r, 5000));
    }

    console.log('\n' + '='.repeat(60));
    console.log('📊 RESUMO FINAL');
    console.log('='.repeat(60));

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    console.log(`✅ Sucesso: ${successful.length}/${results.length}`);
    successful.forEach(r => console.log(`   - ${r.name}`));

    if (failed.length > 0) {
        console.log(`\n❌ Falhas: ${failed.length}/${results.length}`);
        failed.forEach(r => console.log(`   - ${r.name}`));
    }

    console.log('='.repeat(60));
}

main();
