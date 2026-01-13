/**
 * GA4 Funnel Events Instrumentation
 *
 * Este script adiciona tracking de eventos de funil para o GA4.
 * Eventos rastreados:
 * - primary_cta_click: Clique no CTA principal
 * - store_click: Clique nos botoes de loja (App Store, Play Store, Web)
 * - scroll_25, scroll_50, scroll_75: Profundidade de scroll
 *
 * IMPLEMENTACAO NA LANDING PAGE:
 * 1. Adicione este script antes do </body>:
 *    <script src="assets/ga4-funnel.js" defer></script>
 *
 * 2. Marque os elementos no HTML:
 *    - CTA principal: adicione data-ga4="primary-cta"
 *      Ex: <a href="#download" data-ga4="primary-cta">Baixar agora</a>
 *
 *    - Botoes de loja: adicione data-store="play_store" ou "app_store" ou "web"
 *      Ex: <a href="https://play.google.com/..." data-store="play_store">Google Play</a>
 *      Ex: <a href="https://apps.apple.com/..." data-store="app_store">App Store</a>
 *      Ex: <a href="https://site.com/..." data-store="web">Acessar Web</a>
 *
 * 3. Validacao: GA4 DebugView ou ?debug_mode=true na URL
 */

(function () {
  'use strict';

  // =========================================================================
  // HELPER: Dispara evento GA4 com seguranca antes de navegar
  // =========================================================================
  function track(eventName, params, navigateTo) {
    params = params || {};
    var done = false;

    function finish() {
      if (done) return;
      done = true;
      if (navigateTo) window.location.href = navigateTo;
    }

    try {
      if (typeof gtag === "function") {
        gtag("event", eventName, Object.assign({}, params, {
          event_callback: finish
        }));
        // Fallback: nao travar navegacao caso callback nao volte em 300ms
        setTimeout(finish, 300);
      } else {
        console.warn('[GA4 Funnel] gtag nao encontrado. Evento nao enviado:', eventName);
        finish();
      }
    } catch (e) {
      console.error('[GA4 Funnel] Erro ao enviar evento:', e);
      finish();
    }
  }

  // =========================================================================
  // 1) CTA PRINCIPAL: elementos com [data-ga4="primary-cta"]
  // =========================================================================
  document.addEventListener("click", function (e) {
    var el = e.target && e.target.closest ? e.target.closest('[data-ga4="primary-cta"]') : null;
    if (!el) return;

    var href = el.getAttribute("href") || null;
    var buttonText = (el.innerText || el.textContent || "").trim().slice(0, 80);

    // Se for link externo, previne navegacao imediata para garantir envio do evento
    if (href && /^https?:\/\//i.test(href)) {
      e.preventDefault();
      track("primary_cta_click", {
        button_text: buttonText,
        url: href
      }, href);
      return;
    }

    // Link interno ou ancora
    track("primary_cta_click", {
      button_text: buttonText,
      url: href || window.location.href
    });
  }, true);

  // =========================================================================
  // 2) BOTOES DE LOJA: links com [data-store]
  //    Valores: play_store, app_store, web
  // =========================================================================
  document.addEventListener("click", function (e) {
    var el = e.target && e.target.closest ? e.target.closest('a[data-store]') : null;
    if (!el) return;

    var store = el.getAttribute("data-store") || "unknown";
    var href = el.getAttribute("href") || null;
    var buttonText = (el.innerText || el.textContent || "").trim().slice(0, 80);

    // Evitar perder evento ao sair do site
    if (href && /^https?:\/\//i.test(href)) {
      e.preventDefault();
      track("store_click", {
        store: store,
        button_text: buttonText,
        url: href
      }, href);
      return;
    }

    track("store_click", {
      store: store,
      button_text: buttonText,
      url: href || window.location.href
    });
  }, true);

  // =========================================================================
  // 3) SCROLL DEPTH: 25%, 50%, 75%
  //    Util para "zoom" do funil em trafego frio
  // =========================================================================
  var scrollFired = { 25: false, 50: false, 75: false };

  function onScroll() {
    var doc = document.documentElement;
    var scrollTop = window.pageYOffset || doc.scrollTop || 0;
    var height = Math.max(doc.scrollHeight, doc.offsetHeight, doc.clientHeight);
    var viewport = window.innerHeight || doc.clientHeight || 0;
    var maxScroll = Math.max(1, height - viewport);
    var pct = Math.round((scrollTop / maxScroll) * 100);

    [25, 50, 75].forEach(function (threshold) {
      if (!scrollFired[threshold] && pct >= threshold) {
        scrollFired[threshold] = true;
        if (typeof gtag === "function") {
          gtag("event", "scroll_" + threshold, {
            percent_scrolled: threshold,
            page_path: window.location.pathname
          });
        }
      }
    });
  }

  // Usar passive listener para melhor performance
  window.addEventListener("scroll", onScroll, { passive: true });

  // =========================================================================
  // 4) PAGE VIEW ENHANCED (opcional)
  //    Envia informacoes extras sobre a visita
  // =========================================================================
  if (typeof gtag === "function") {
    // Detectar se usuario veio de anuncio (utm_source presente)
    var urlParams = new URLSearchParams(window.location.search);
    var utmSource = urlParams.get('utm_source');
    var utmCampaign = urlParams.get('utm_campaign');
    var utmMedium = urlParams.get('utm_medium');

    if (utmSource) {
      gtag("event", "landing_visit", {
        utm_source: utmSource,
        utm_campaign: utmCampaign || '',
        utm_medium: utmMedium || '',
        page_path: window.location.pathname
      });
    }
  }

  // Log de inicializacao (apenas em modo debug)
  if (window.location.search.indexOf('debug_mode=true') > -1) {
    console.log('[GA4 Funnel] Script inicializado');
    console.log('[GA4 Funnel] gtag disponivel:', typeof gtag === "function");
  }

})();
