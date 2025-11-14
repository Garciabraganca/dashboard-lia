# Script para arrumar arquivos do Dashboard LIA
# Execute este script na pasta raiz do repositório

Write-Host "🚀 Arrumando arquivos do Dashboard LIA..." -ForegroundColor Cyan
Write-Host ""

# 1. Renomear arquivo com espaço
Write-Host "📝 Renomeando 'tour guide.py' para 'tour_guide.py'..." -ForegroundColor Yellow
if (Test-Path "tour guide.py") {
    Rename-Item "tour guide.py" "tour_guide.py" -Force
    Write-Host "✅ Arquivo renomeado!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Arquivo 'tour guide.py' não encontrado" -ForegroundColor Red
}

Write-Host ""

# 2. Verificar se as imagens existem
Write-Host "🖼️  Verificando imagens..." -ForegroundColor Yellow

$imagens = @("lia-logo.png", "lia-imagem.jpg", "logotipo-gb.png")
$imagensFaltando = @()

foreach ($img in $imagens) {
    if (Test-Path $img) {
        Write-Host "  ✅ $img encontrada" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $img NÃO encontrada" -ForegroundColor Red
        $imagensFaltando += $img
    }
}

Write-Host ""

# 3. Git add, commit e push
Write-Host "📦 Fazendo commit das mudanças..." -ForegroundColor Yellow

git add .

$commitMsg = "fix: renomear tour_guide.py e adicionar imagens"
git commit -m $commitMsg

Write-Host "✅ Commit realizado: $commitMsg" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 Fazendo push para GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ CONCLUÍDO!" -ForegroundColor Green
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($imagensFaltando.Count -gt 0) {
    Write-Host "⚠️  ATENÇÃO: As seguintes imagens NÃO foram encontradas:" -ForegroundColor Yellow
    foreach ($img in $imagensFaltando) {
        Write-Host "   • $img" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "📋 AÇÃO NECESSÁRIA:" -ForegroundColor Yellow
    Write-Host "   1. Copie as 3 imagens para a pasta do repositório" -ForegroundColor White
    Write-Host "   2. Execute este script novamente" -ForegroundColor White
} else {
    Write-Host "🎉 Tudo certo! Aguarde 2-3 minutos e acesse o Streamlit Cloud" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Seu dashboard: https://dashboard-lia-ed2xhysnmetq7xnu8baprr.streamlit.app" -ForegroundColor Cyan
}

Write-Host ""
Read-Host "Pressione ENTER para fechar"
