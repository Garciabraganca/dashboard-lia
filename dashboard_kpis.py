"""Helpers para payload dos cards KPI do dashboard."""


def _num(value, default=0.0):
    """Converte valor para número, com fallback seguro para None/inválido."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_meta_kpi_cards_payload(meta_data: dict) -> list:
    """Monta o payload padronizado dos cards KPI da seção Meta Ads."""
    cards = [
        {"icon": "💰", "label": "Valor investido", "value": f"$ {_num(meta_data.get('investimento'), 0.0):,.2f}", "delta": _num(meta_data.get('delta_investimento'), 0.0), "suffix": "%"},
        {"icon": "👀", "label": "Vezes que o anúncio apareceu", "value": f"{_num(meta_data.get('impressoes'), 0.0):,.0f}", "delta": _num(meta_data.get('delta_impressoes'), 0.0), "suffix": "%"},
        {"icon": "📡", "label": "Pessoas alcançadas", "value": f"{_num(meta_data.get('alcance'), 0.0):,.0f}", "delta": _num(meta_data.get('delta_alcance'), 0.0), "suffix": "%"},
        {"icon": "🔁", "label": "Vezes que cada pessoa viu", "value": f"{_num(meta_data.get('frequencia'), 0.0):.2f}", "delta": _num(meta_data.get('delta_frequencia'), 0.0), "suffix": "", "precision": 2},
        {"icon": "🖱️", "label": "Cliques no anúncio", "value": f"{_num(meta_data.get('cliques_link'), 0.0):,.0f}", "delta": _num(meta_data.get('delta_cliques'), 0.0), "suffix": "%"},
        {"icon": "🎯", "label": "Taxa de cliques", "value": f"{_num(meta_data.get('ctr_link'), 0.0):.2f}%", "delta": _num(meta_data.get('delta_ctr'), 0.0), "suffix": "pp", "precision": 2},
        {"icon": "💡", "label": "Custo por clique", "value": f"$ {_num(meta_data.get('cpc_link'), 0.0):.2f}", "delta": _num(meta_data.get('delta_cpc'), 0.0), "suffix": "%", "invert": True},
        {"icon": "📊", "label": "Custo por mil exibições", "value": f"$ {_num(meta_data.get('cpm'), 0.0):.2f}", "delta": _num(meta_data.get('delta_cpm'), 0.0), "suffix": "%", "invert": True},
    ]

    sdk_events = meta_data.get("_all_sdk_events", {})
    sdk_installs = int(_num(meta_data.get("instalacoes_sdk"), 0.0))

    if sdk_installs > 0:
        installs_label = "Instalações (GA4)" if meta_data.get("_sdk_source") == "ga4_first_open" else "Instalações (SDK)"
        cards.append({"icon": "📲", "label": installs_label, "value": f"{sdk_installs:,.0f}", "delta": 0, "suffix": ""})

    primary_activate = sdk_events.get("fb_mobile_activate_app")
    activate_raw = primary_activate if primary_activate is not None else sdk_events.get("activate_app", 0.0)
    activate = int(_num(activate_raw, 0.0))
    if activate > 0 and activate != sdk_installs:
        cards.append({"icon": "📱", "label": "Activate App (SDK)", "value": f"{activate:,.0f}", "delta": 0, "suffix": ""})

    view_content = int(_num(sdk_events.get("fb_mobile_content_view"), 0.0))
    if view_content > 0:
        cards.append({"icon": "👁️", "label": "View Content (SDK)", "value": f"{view_content:,.0f}", "delta": 0, "suffix": ""})

    return cards
