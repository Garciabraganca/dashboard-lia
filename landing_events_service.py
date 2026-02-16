"""Serviço para card de eventos da landing com fallback resiliente."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


PLACEHOLDER_CHECKLIST = [
    "Adicionar a service account como Viewer na propriedade GA4",
    "Setar GA4_PROPERTY_ID",
    "Validar eventos da landing page",
]


def build_landing_events_card_data(
    ga4_client: Any,
    *,
    events_mode: str,
    period_api: str,
    custom_start: str | None,
    custom_end: str | None,
    landing_host_filter: str | None,
) -> dict[str, Any]:
    """Monta payload do card de eventos da landing sem quebrar a UI."""
    if events_mode == "off":
        return {
            "status": "disabled",
            "title": "Eventos desativados",
            "message": "EVENTS_MODE=off: bloco de eventos oculto por configuração.",
        }

    if ga4_client is None:
        return {
            "status": "unavailable",
            "title": "Eventos (em desenvolvimento)",
            "message": "Integração GA4/Meta em configuração. Este bloco será ativado quando GA4_PROPERTY_ID e credenciais estiverem válidos.",
            "checklist": PLACEHOLDER_CHECKLIST,
            "error": "Credenciais GA4 ausentes.",
        }

    try:
        summary = ga4_client.get_landing_events_summary(
            date_range=period_api,
            custom_start=custom_start,
            custom_end=custom_end,
            landing_host_filter=landing_host_filter,
            limit=100,
        )
        rows = summary.get("rows", [])
        if not rows:
            return {
                "status": "no_data",
                "title": "Eventos da Landing (GA4)",
                "message": "GA4 conectado, mas sem eventos para o período selecionado.",
                "date_range": summary.get("date_range"),
                "landing_host_filter": landing_host_filter,
            }

        events_df = pd.DataFrame(rows)
        grouped = events_df.groupby("Evento", as_index=False).agg({
            "Contagem": "sum",
            "Usuários": "sum",
            "Conversões": "sum",
        })
        grouped = grouped.sort_values("Contagem", ascending=False).head(8)

        return {
            "status": "ok",
            "title": "Eventos da Landing (GA4)",
            "table": grouped,
            "kpi_total_events": int(summary.get("total_events", 0)),
            "kpi_total_users": int(summary.get("total_users", 0)),
            "kpi_total_conversions": float(summary.get("total_conversions", 0)),
            "key_event_totals": summary.get("key_event_totals", {}),
            "has_key_events": bool(summary.get("has_key_events", False)),
            "has_conversions": bool(summary.get("has_conversions", False)),
            "date_range": summary.get("date_range"),
            "landing_host_filter": landing_host_filter,
        }
    except Exception as exc:
        logger.error("Erro ao obter Eventos da Landing (GA4): %s", exc)
        return {
            "status": "error",
            "title": "Eventos (em desenvolvimento)",
            "message": "Integração GA4/Meta em configuração. Este bloco será ativado quando GA4_PROPERTY_ID e credenciais estiverem válidos.",
            "checklist": PLACEHOLDER_CHECKLIST,
            "error": str(exc),
        }
