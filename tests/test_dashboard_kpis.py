from dashboard_kpis import build_meta_kpi_cards_payload


def test_ga4_fallback_renders_install_card_label_when_install_campaign_configured():
    meta_data = {
        "investimento": 0,
        "impressoes": 0,
        "alcance": 0,
        "frequencia": 0,
        "cliques_link": 0,
        "ctr_link": 0,
        "cpc_link": 0,
        "cpm": 0,
        "instalacoes_sdk": 123,
        "_sdk_source": "ga4_first_open",
        "_all_sdk_events": {},
        "show_install_kpis": True,
    }

    cards = build_meta_kpi_cards_payload(meta_data)
    labels = [card["label"] for card in cards]

    assert "Instalações (GA4)" in labels


def test_sdk_cards_hidden_by_default_when_install_campaign_not_configured():
    meta_data = {
        "investimento": 0,
        "impressoes": 0,
        "alcance": 0,
        "frequencia": 0,
        "cliques_link": 0,
        "ctr_link": 0,
        "cpc_link": 0,
        "cpm": 0,
        "instalacoes_sdk": 123,
        "_sdk_source": "ga4_first_open",
        "_all_sdk_events": {},
    }

    cards = build_meta_kpi_cards_payload(meta_data)
    labels = [card["label"] for card in cards]

    assert "Instalações (GA4)" not in labels
    assert "Instalações (SDK)" not in labels
