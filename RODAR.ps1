# 🚀 RODAR DASHBOARD LIA + TOUR GUIADO
# Execute este arquivo para iniciar o dashboard com guia de apresentação

Write-Host ""
Write-Host "╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  📊 DASHBOARD LIA + 📖 TOUR GUIADO        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "[1/3] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "      ❌ Python não encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Instale Python em: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Pressione ENTER para sair"
    exit
}

# Instalar dependências
Write-Host ""
Write-Host "[2/3] Instalando dependências (pode demorar 1-2 min)..." -ForegroundColor Yellow
pip install streamlit pandas plotly --quiet --disable-pip-version-check 2>&1 | Out-Null
Write-Host "      ✅ Dependências instaladas" -ForegroundColor Green

# Rodar dashboard
Write-Host ""
Write-Host "[3/3] Iniciando dashboard..." -ForegroundColor Yellow
Write-Host "      🌐 Dashboard abrirá em: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ DASHBOARD + TOUR GUIADO RODANDO!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📖 NOVIDADE: Tour Guiado Pergaminho" -ForegroundColor Yellow
Write-Host ""
Write-Host "O dashboard agora inclui um guia de apresentação" -ForegroundColor White
Write-Host "no sidebar esquerdo (estilo pergaminho). Use como" -ForegroundColor White
Write-Host "teleprompter durante sua apresentação!" -ForegroundColor White
Write-Host ""
Write-Host "Dicas:" -ForegroundColor Yellow
Write-Host "  📖 Clique nas seções do tour para ver as dicas" -ForegroundColor White
Write-Host "  🎯 Use como guia durante apresentação" -ForegroundColor White
Write-Host "  💡 Leia TOUR_GUIADO_PERGAMINHO.md para detalhes" -ForegroundColor White
Write-Host "  🖥️  Pressione F11 para fullscreen" -ForegroundColor White
Write-Host "  ⌨️  Use Ctrl+C para parar o servidor" -ForegroundColor White
Write-Host ""

# Executar Streamlit
streamlit run app_lia_premium.py
