"""Helpers para payload dos cards KPI do dashboard."""


def build_meta_kpi_cards_payload(meta_data: dict) -> list:
    cards = [
        {"icon": "💰", "label": "Valor investido", "value": f"$ {meta_data.get('investimento', 0):,.2f}", "delta": meta_data.get('delta_investimento', 0), "suffix": "%"},
        {"icon": "👀", "label": "Vezes que o anúncio apareceu", "value": f"{meta_data.get('impressoes', 0):,.0f}", "delta": meta_data.get('delta_impressoes', 0), "suffix": "%"},
        {"icon": "📡", "label": "Pessoas alcançadas", "value": f"{meta_data.get('alcance', 0):,.0f}", "delta": meta_data.get('delta_alcance', 0), "suffix": "%"},
        {"icon": "🔁", "label": "Vezes que cada pessoa viu", "value": f"{meta_data.get('frequencia', 0):.2f}", "delta": meta_data.get('delta_frequencia', 0), "suffix": "", "precision": 2},
        {"icon": "🖱️", "label": "Cliques no anúncio", "value": f"{meta_data.get('cliques_link', 0):,.0f}", "delta": meta_data.get('delta_cliques', 0), "suffix": "%"},
        {"icon": "🎯", "label": "Taxa de cliques", "value": f"{meta_data.get('ctr_link', 0):.2f}%", "delta": meta_data.get('delta_ctr', 0), "suffix": "pp", "precision": 2},
        {"icon": "💡", "label": "Custo por clique", "value": f"$ {meta_data.get('cpc_link', 0):.2f}", "delta": meta_data.get('delta_cpc', 0), "suffix": "%", "invert": True},
        {"icon": "📊", "label": "Custo por mil exibições", "value": f"$ {meta_data.get('cpm', 0):.2f}", "delta": meta_data.get('delta_cpm', 0), "suffix": "%", "invert": True},
    ]

    sdk_events = meta_data.get("_all_sdk_events", {})
    sdk_installs = meta_data.get("instalacoes_sdk", 0) or 0

    if sdk_installs > 0:
        cards.append({"icon": "📲", "label": "Instalações (SDK)", "value": f"{sdk_installs:,.0f}", "delta": 0, "suffix": ""})

    activate = sdk_events.get("fb_mobile_activate_app", 0) or sdk_events.get("activate_app", 0)
    if activate > 0 and activate != sdk_installs:
        cards.append({"icon": "📱", "label": "Activate App (SDK)", "value": f"{activate:,.0f}", "delta": 0, "suffix": ""})

    view_content = sdk_events.get("fb_mobile_content_view", 0)
    if view_content > 0:
        cards.append({"icon": "👁️", "label": "View Content (SDK)", "value": f"{view_content:,.0f}", "delta": 0, "suffix": ""})

    return cards
