# Script PowerShell - Deploy Dashboard LIA
# Execute este script para fazer deploy automático no Streamlit Cloud

Write-Host "🚀 Deploy Dashboard LIA - Streamlit Cloud" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# 1. Criar repositório Git local
Write-Host "📦 Criando repositório Git..." -ForegroundColor Yellow
git init
git add .
git commit -m "feat: Dashboard LIA premium - Funil AIDA completo"

# 2. Conectar com GitHub
Write-Host "`n🌐 Conectando com GitHub..." -ForegroundColor Yellow
Write-Host "Você precisa criar um repositório no GitHub primeiro!" -ForegroundColor Red
Write-Host "1. Acesse: https://github.com/new" -ForegroundColor White
Write-Host "2. Nome do repositório: dashboard-lia" -ForegroundColor White
Write-Host "3. Deixe como Public" -ForegroundColor White
Write-Host "4. NÃO marque 'Add README'" -ForegroundColor White
Write-Host "5. Clique em 'Create repository'`n" -ForegroundColor White

$repoUrl = Read-Host "Cole aqui a URL do repositório (ex: https://github.com/seu-usuario/dashboard-lia.git)"

git remote add origin $repoUrl
git branch -M main
git push -u origin main

Write-Host "`n✅ Código enviado para o GitHub!" -ForegroundColor Green

# 3. Instruções para Streamlit Cloud
Write-Host "`n📊 Agora faça o deploy no Streamlit Cloud:" -ForegroundColor Yellow
Write-Host "1. Acesse: https://streamlit.io/cloud" -ForegroundColor White
Write-Host "2. Clique em 'New app'" -ForegroundColor White
Write-Host "3. Conecte sua conta GitHub" -ForegroundColor White
Write-Host "4. Selecione o repositório: dashboard-lia" -ForegroundColor White
Write-Host "5. Main file: app_lia_premium.py" -ForegroundColor White
Write-Host "6. Clique em 'Deploy'`n" -ForegroundColor White

Write-Host "🎉 Seu dashboard ficará disponível em:" -ForegroundColor Green
Write-Host "   https://dashboard-lia-[seu-usuario].streamlit.app`n" -ForegroundColor Cyan

Write-Host "⏱️  Deploy leva ~2-3 minutos" -ForegroundColor Yellow

Read-Host "`nPressione ENTER para finalizar"
