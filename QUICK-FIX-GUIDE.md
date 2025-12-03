# 🚀 QUICK FIX GUIDE - Sofia Pulse

**Data**: 2025-11-22
**Status**: Todos os arquivos criados e prontos

---

## ✅ O QUE ESTÁ PRONTO:

1. ✅ **Migrations SQL** (migrations/008-add-city-column.sql, 009-add-countries-column-openalex.sql)
2. ✅ **Script Gemini Key** (apply-new-gemini-key.sh) - com nova chave
3. ✅ **Script Python Migrations** (apply-migrations-python.py)
4. ✅ **Master Script** (fix-everything.sh) - roda tudo de uma vez

---

## 🎯 OPÇÃO 1: Rodar Tudo de Uma Vez (RECOMENDADO)

```bash
bash fix-everything.sh
```

Isso vai:
1. ✅ Aplicar nova chave Gemini no .env
2. ✅ Aplicar migrations (adicionar colunas city e countries)
3. ✅ Restart sofia-mastra-api

**Tempo**: ~10 segundos

---

## 🔧 OPÇÃO 2: Rodar Passo a Passo

### Passo 1: Nova Chave Gemini
```bash
bash apply-new-gemini-key.sh
```
- Atualiza GEMINI_API_KEY no .env
- Script se auto-deleta após uso (segurança)

### Passo 2: Aplicar Migrations
```bash
python apply-migrations-python.py
```
- Adiciona coluna `city` a `funding_rounds`
- Adiciona coluna `countries` a `openalex_papers`

### Passo 3: Restart Docker
```bash
docker restart sofia-mastra-api
```
- Recarrega nova chave Gemini

---

## 🧪 TESTAR TUDO

Depois de aplicar os fixes, rodar analytics:

```bash
bash run-mega-analytics.sh
```

**Resultado Esperado**:
- ✅ 23 de 23 relatórios funcionando
- ✅ Sem erro "column does not exist"
- ✅ Gemini API funcionando

---

## 🐛 PROBLEMAS RESOLVIDOS:

### 1. WhatsApp não chegava ❌
**Causa**: Moderação detectou "comportamento de bot"
**Solução**: Ver `fix-whatsapp-bot-detection.md`

### 2. Gemini API vazada 🔑
**Causa**: Chave hardcoded em update-gemini-key.sh
**Solução**: Nova chave aplicada + script sem hardcode

### 3. Relatórios falhando (3/23) 📊
**Causa**: Colunas city e countries não existiam
**Solução**: Migrations 008 e 009 criadas

---

## 📁 ARQUIVOS CRIADOS:

```
sofia-pulse/
├── migrations/
│   ├── 008-add-city-column.sql         (792 bytes)
│   └── 009-add-countries-column-openalex.sql  (871 bytes)
├── apply-new-gemini-key.sh             (1.9K) - se auto-deleta
├── apply-migrations-python.py          (criado antes)
├── fix-everything.sh                   (master script)
└── QUICK-FIX-GUIDE.md                  (este arquivo)
```

---

## ✅ VERIFICAR SE FUNCIONOU:

### Gemini Key:
```bash
grep "GEMINI_API_KEY" .env | sed 's/\(.\{25\}\).*/\1.../'
```
Deve mostrar: `GEMINI_API_KEY=AIzaSyA4E...`

### Migrations:
```bash
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', database='sofia_db', user='sofia', password='sofia123strong')
cur = conn.cursor()
cur.execute(\"SELECT column_name FROM information_schema.columns WHERE table_schema='sofia' AND table_name='funding_rounds' AND column_name='city'\")
print('✅ Column city exists' if cur.fetchone() else '❌ Column city missing')
"
```

### Sofia Mastra:
```bash
docker logs sofia-mastra-api --tail 20 | grep -i "error\|started"
```

---

## 🚀 PRÓXIMOS PASSOS:

1. ✅ Rodar `bash fix-everything.sh`
2. ✅ Rodar `bash run-mega-analytics.sh`
3. ✅ Verificar se 23/23 relatórios funcionaram
4. ⏳ Escolher solução para WhatsApp (mensagens humanas | Telegram | só email)

---

**Última atualização**: 2025-11-22 02:10 UTC
**Status**: ✅ Pronto para usar
