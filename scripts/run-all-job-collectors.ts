#!/usr/bin/env tsx
/**
 * Script para executar todos os coletores de vagas com keywords centralizadas
 */
import { spawn } from 'child_process';

const COLLECTORS = [
    { name: 'Adzuna', script: 'collect-jobs-adzuna.ts' },
    { name: 'Jooble', script: 'collect-jooble-jobs.ts' },
    { name: 'The Muse', script: 'collect-jobs-themuse.ts' },
    { name: 'Findwork', script: 'collect-jobs-findwork.ts' },
    { name: 'USAJobs', script: 'collect-jobs-usajobs.ts' },
    { name: 'ActiveJobs (RapidAPI)', script: 'collect-rapidapi-activejobs.py' },
    { name: 'Google Jobs (SerpApi)', script: 'collect-serpapi-googlejobs.py' },
    { name: 'Catho', script: 'collect-catho-final.ts' },
    { name: 'InfoJobs', script: 'collect-infojobs-brasil.ts' },
    // Less critical / older collectors
    { name: 'Arbeitnow', script: 'collect-jobs-arbeitnow.ts' },
    { name: 'GitHub Jobs', script: 'collect-jobs-github.ts' },
    { name: 'Himalayas', script: 'collect-jobs-himalayas.ts' },
    { name: 'WeWorkRemotely', script: 'collect-jobs-weworkremotely.ts' },
];

async function runCollector(collector: { name: string; script: string }) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 Executando: ${collector.name}`);
    console.log('='.repeat(60));

    return new Promise<{ name: string; success: boolean; error: any }>((resolve) => {
        const cmd = collector.script.endsWith('.py') ? 'python' : 'npx';
        const args = collector.script.endsWith('.py')
            ? [`scripts/${collector.script}`]
            : ['tsx', `scripts/${collector.script}`];

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
