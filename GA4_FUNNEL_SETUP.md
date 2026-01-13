# GA4 Funnel Tracking - Guia de Implementacao

Este documento explica como implementar o tracking de eventos de funil do GA4 na landing page do LIA.

## Eventos Rastreados

| Evento | Descricao | Parametros |
|--------|-----------|------------|
| `primary_cta_click` | Clique no CTA principal (Baixar Agora) | `button_text`, `url` |
| `store_click` | Clique nos botoes de loja | `store`, `button_text`, `url` |
| `scroll_25` | Usuario rolou 25% da pagina | `percent_scrolled`, `page_path` |
| `scroll_50` | Usuario rolou 50% da pagina | `percent_scrolled`, `page_path` |
| `scroll_75` | Usuario rolou 75% da pagina | `percent_scrolled`, `page_path` |
| `landing_visit` | Visita com UTM (trafego pago) | `utm_source`, `utm_campaign`, `utm_medium` |

## Como Implementar

### Passo 1: Verificar se o GA4 esta instalado

O GA4 deve estar carregado via gtag.js. Procure no HTML da landing:

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXX');
</script>
```

**Anote o Measurement ID (G-XXXXXXX)** - ele sera usado para validacao.

### Passo 2: Adicionar o Script de Instrumentacao

Copie o arquivo `assets/ga4-funnel.js` para a pasta de assets da landing page.

Adicione antes do `</body>`:

```html
<script src="assets/ga4-funnel.js" defer></script>
</body>
```

### Passo 3: Marcar os Elementos no HTML

#### CTA Principal (Baixar Agora)

Adicione `data-ga4="primary-cta"` ao botao/link do CTA:

```html
<!-- ANTES -->
<a href="#download" class="btn-primary">Baixar agora</a>

<!-- DEPOIS -->
<a href="#download" class="btn-primary" data-ga4="primary-cta">Baixar agora</a>
```

#### Botoes de Loja

Adicione `data-store` com o valor apropriado:

```html
<!-- Google Play -->
<a href="https://play.google.com/store/apps/details?id=..."
   data-store="play_store">
  Google Play
</a>

<!-- App Store -->
<a href="https://apps.apple.com/app/..."
   data-store="app_store">
  App Store
</a>

<!-- Web App (se houver) -->
<a href="https://app.lia.com.br/..."
   data-store="web">
  Acessar Web
</a>
```

### Exemplo Completo de HTML

```html
<!DOCTYPE html>
<html>
<head>
  <!-- Google tag (gtag.js) - JA EXISTENTE -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXX"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-XXXXXXXXX');
  </script>
</head>
<body>
  <!-- Hero Section -->
  <section class="hero">
    <h1>LIA - Sua assistente de marketing</h1>
    <p>Simplifique sua gestao de midia com inteligencia artificial</p>

    <!-- CTA Principal - ADICIONAR data-ga4 -->
    <a href="#download" class="btn-cta" data-ga4="primary-cta">
      Baixar agora
    </a>
  </section>

  <!-- Download Section -->
  <section id="download" class="download">
    <h2>Baixe o app</h2>

    <!-- Botoes de Loja - ADICIONAR data-store -->
    <div class="store-buttons">
      <a href="https://play.google.com/store/apps/details?id=..."
         data-store="play_store">
        <img src="google-play-badge.png" alt="Google Play">
      </a>

      <a href="https://apps.apple.com/app/..."
         data-store="app_store">
        <img src="app-store-badge.png" alt="App Store">
      </a>
    </div>
  </section>

  <!-- Script de Instrumentacao - ADICIONAR ANTES DO </body> -->
  <script src="assets/ga4-funnel.js" defer></script>
</body>
</html>
```

## Validacao

### Metodo 1: GA4 DebugView

1. Acesse o GA4: https://analytics.google.com
2. Va em **Admin > DebugView**
3. Abra a landing page em outra aba
4. Interaja com a pagina (clique no CTA, botoes de loja, role a pagina)
5. Os eventos devem aparecer em tempo real no DebugView

### Metodo 2: Query Parameter debug_mode

Adicione `?debug_mode=true` na URL da landing:

```
https://sualanding.com/?debug_mode=true
```

Abra o Console do navegador (F12 > Console) e veja os logs:
- `[GA4 Funnel] Script inicializado`
- `[GA4 Funnel] gtag disponivel: true`

### Metodo 3: Chrome Extension

Instale a extensao "Google Analytics Debugger" para Chrome:
https://chrome.google.com/webstore/detail/google-analytics-debugger

## Eventos Esperados no GA4

Apos a implementacao, voce deve ver no GA4:

| Evento | Significado |
|--------|-------------|
| `primary_cta_click` | Cliques no botao principal |
| `store_click` | Cliques nos botoes de loja (somatorio) |
| `store_click` com `store=play_store` | Cliques no Google Play |
| `store_click` com `store=app_store` | Cliques na App Store |
| `scroll_25` | Usuarios que rolaram 25% |
| `scroll_50` | Usuarios que rolaram 50% |
| `scroll_75` | Usuarios que rolaram 75% |

## Funil Montavel

Com esses eventos, o funil fica:

```
Impressoes (Meta Ads)
    |
    v
Cliques no Link (Meta Ads)
    |
    v
Sessoes na Landing (GA4)
    |
    v
scroll_25 / scroll_50 / scroll_75 (engajamento)
    |
    v
primary_cta_click (interesse)
    |
    v
store_click (intencao de download)
    |
    v
Instalacoes (SDK - quando integrado)
```

## Troubleshooting

### Eventos nao aparecem no GA4

1. **Verifique se gtag esta carregado**: Abra o Console e digite `gtag`. Deve retornar a funcao.
2. **Verifique o Measurement ID**: Confirme que o ID no gtag.config e o correto.
3. **Aguarde ate 24-48h**: O GA4 pode demorar para processar eventos.
4. **Use DebugView**: Eventos em debug aparecem em tempo real.

### Cliques nao estao sendo rastreados

1. Verifique se o elemento tem o atributo correto (`data-ga4` ou `data-store`)
2. Verifique se o script esta sendo carregado (sem erros no Console)
3. Verifique se nao ha JavaScript interferindo (ex: `e.stopPropagation()`)

### Scroll events nao aparecem

1. A pagina precisa ter conteudo suficiente para rolar
2. Verifique se o evento de scroll nao esta sendo bloqueado por outro script

## Contato

Duvidas sobre a implementacao? Abra uma issue no repositorio do dashboard.
