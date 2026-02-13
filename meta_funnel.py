import json
import logging
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

STORE_CLICK_ACTION_TYPES = {
    "app_store_click",
    "store_click",
    "mobile_store_click",
    "app_install_store_click",
    "outbound_click",
    "google_play_click",
}

INSTALL_ACTION_TYPES = {
    # Classic action types
    "app_install",
    "mobile_app_install",
    "omni_app_install",
    "app_install_event",
    "mobile_app_install_event",
    "offsite_conversion.fb_mobile_install",
    "fb_mobile_install",
    "offsite_conversion.mobile_app_install",
    "offsite_conversion.app_install",
    # Newer Meta SDK naming conventions (post SDK updates)
    "app_custom_event.fb_mobile_install",
    "onsite_conversion.app_install",
    "offsite_conversion.fb_mobile_first_open",
    "fb_mobile_first_open",
    "omni_app_install_event",
    "app_custom_event.fb_mobile_first_open",
    # Generic / short-form variants seen in some pipelines
    "first_open",
    "install",
}

ACTIVATE_APP_ACTION_TYPES = {
    "activate_app",
    "app_custom_event.fb_mobile_activate_app",
    "offsite_conversion.fb_mobile_activate_app",
    "fb_mobile_activate_app",
    "omni_activate_app",
}


def _parse_actions_cell(actions: Any) -> List[Dict[str, Any]]:
    if isinstance(actions, str):
        try:
            parsed = json.loads(actions)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    if isinstance(actions, dict):
        return [actions]
    if isinstance(actions, list):
        return [a for a in actions if isinstance(a, dict)]
    return []


def collect_all_action_types(actions_series: pd.Series) -> Dict[str, int]:
    """Collect all unique action types and their totals from the API response."""
    all_types: Dict[str, float] = {}
    for actions in actions_series.dropna():
        for action in _parse_actions_cell(actions):
            atype = action.get("action_type", "unknown")
            try:
                val = float(action.get("value", 0) or 0)
            except (TypeError, ValueError):
                val = 0
            all_types[atype] = all_types.get(atype, 0) + val
    result = {k: int(v) for k, v in sorted(all_types.items())}
    if result:
        logger.warning("Meta action types found: %s", result)
    else:
        logger.warning("Meta API returned NO action types in the actions column.")
    return result


def log_all_action_types(actions_series: pd.Series) -> None:
    """Legacy wrapper – calls collect_all_action_types for backwards compat."""
    collect_all_action_types(actions_series)


def sum_actions_by_types(actions_series: pd.Series, action_types: Iterable[str]) -> Tuple[int, bool]:
    target_types = set(action_types)
    total = 0.0
    found_type = False

    for actions in actions_series.dropna():
        for action in _parse_actions_cell(actions):
            action_type = action.get("action_type")
            if action_type in target_types:
                found_type = True
                try:
                    total += float(action.get("value", 0) or 0)
                except (TypeError, ValueError):
                    continue

    return int(total), found_type


def _safe_int(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def resolve_store_clicks(df: pd.DataFrame) -> Tuple[int, str]:
    actions = df["actions"] if "actions" in df.columns else pd.Series(dtype=object)
    store_clicks, has_store_action = sum_actions_by_types(actions, STORE_CLICK_ACTION_TYPES)
    if has_store_action:
        return store_clicks, "actions"

    if "inline_link_clicks" in df.columns:
        inline_clicks = _safe_int(pd.to_numeric(df["inline_link_clicks"], errors="coerce").fillna(0).sum())
        if inline_clicks > 0:
            logger.warning("Meta funnel fallback: store_click action_type not found, using inline_link_clicks.")
            return inline_clicks, "inline_link_clicks"

    link_clicks, has_link_click = sum_actions_by_types(actions, {"link_click"})
    if has_link_click:
        logger.warning("Meta funnel fallback: store_click action_type not found, using actions.link_click.")
        return link_clicks, "actions.link_click"

    clicks = _safe_int(pd.to_numeric(df.get("clicks", 0), errors="coerce").fillna(0).sum())
    logger.warning("Meta funnel fallback: store_click action_type not found, using clicks.")
    return clicks, "clicks"


def resolve_link_clicks(df: pd.DataFrame) -> int:
    if "inline_link_clicks" in df.columns:
        inline_clicks = _safe_int(pd.to_numeric(df["inline_link_clicks"], errors="coerce").fillna(0).sum())
        if inline_clicks > 0:
            return inline_clicks

    actions = df["actions"] if "actions" in df.columns else pd.Series(dtype=object)
    link_clicks, has_link_click = sum_actions_by_types(actions, {"link_click"})
    if has_link_click:
        return link_clicks

    return _safe_int(pd.to_numeric(df.get("clicks", 0), errors="coerce").fillna(0).sum())


def collect_action_type_diagnostics(actions_series: pd.Series) -> Dict[str, Any]:
    """Collect diagnostic info about action types for UI display."""
    all_types: Dict[str, float] = {}
    for actions in actions_series.dropna():
        for action in _parse_actions_cell(actions):
            atype = action.get("action_type", "unknown")
            try:
                val = float(action.get("value", 0) or 0)
            except (TypeError, ValueError):
                val = 0
            all_types[atype] = all_types.get(atype, 0) + val

    install_types_found = {k: int(v) for k, v in all_types.items() if k in INSTALL_ACTION_TYPES}
    store_types_found = {k: int(v) for k, v in all_types.items() if k in STORE_CLICK_ACTION_TYPES}
    activate_types_found = {k: int(v) for k, v in all_types.items() if k in ACTIVATE_APP_ACTION_TYPES}

    return {
        "all_action_types": {k: int(v) for k, v in sorted(all_types.items())},
        "install_events": install_types_found,
        "store_click_events": store_types_found,
        "activate_app_events": activate_types_found,
        "has_install_events": bool(install_types_found),
        "has_store_click_events": bool(store_types_found),
        "has_activate_app_events": bool(activate_types_found),
        "total_action_types": len(all_types),
    }


def build_meta_funnel(meta_data: Dict[str, Any]) -> Tuple[List[str], List[int]]:
    labels = ["Viram o anúncio", "Clicaram no anúncio", "Foram para a loja do app", "Instalaram o app (SDK)"]
    values = [
        _safe_int(meta_data.get("impressoes", 0)),
        _safe_int(meta_data.get("cliques_link", 0)),
        _safe_int(meta_data.get("store_clicks_meta", 0)),
        _safe_int(meta_data.get("instalacoes_sdk", 0)),
    ]
    return labels, values
