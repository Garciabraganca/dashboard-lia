import pandas as pd

from meta_funnel import build_meta_funnel, collect_all_action_types, resolve_store_clicks, sum_actions_by_types, INSTALL_ACTION_TYPES


def test_parser_sums_store_clicks_and_installs_from_actions():
    df = pd.DataFrame([
        {
            "impressions": 1000,
            "inline_link_clicks": 100,
            "actions": [
                {"action_type": "app_store_click", "value": "45"},
                {"action_type": "mobile_app_install", "value": "11"},
            ],
        },
        {
            "impressions": 2000,
            "inline_link_clicks": 200,
            "actions": [
                {"action_type": "store_click", "value": "5"},
                {"action_type": "mobile_app_install", "value": "9"},
            ],
        },
    ])

    store_clicks, source = resolve_store_clicks(df)
    installs, found = sum_actions_by_types(df["actions"], INSTALL_ACTION_TYPES)

    assert source == "actions"
    assert store_clicks == 50
    assert found is True
    assert installs == 20


def test_meta_funnel_labels_do_not_render_ga4_primary_cta_click():
    labels, values = build_meta_funnel(
        {
            "impressoes": 3000,
            "cliques_link": 400,
            "store_clicks_meta": 120,
            "instalacoes_sdk": 30,
        }
    )

    labels_snapshot = " | ".join(labels)

    assert labels_snapshot == "Viram o anúncio | Clicaram no anúncio | Foram para a loja do app | Instalaram o app (SDK)"
    assert "primary_cta_click" not in labels_snapshot
    assert values == [3000, 400, 120, 30]


def test_collect_all_action_types_returns_dict():
    df = pd.DataFrame([
        {
            "actions": [
                {"action_type": "link_click", "value": "100"},
                {"action_type": "page_engagement", "value": "50"},
            ],
        },
        {
            "actions": [
                {"action_type": "link_click", "value": "200"},
                {"action_type": "mobile_app_install", "value": "5"},
            ],
        },
    ])
    result = collect_all_action_types(df["actions"])
    assert result == {"link_click": 300, "mobile_app_install": 5, "page_engagement": 50}


def test_collect_all_action_types_empty_series():
    empty = pd.Series(dtype=object)
    result = collect_all_action_types(empty)
    assert result == {}
