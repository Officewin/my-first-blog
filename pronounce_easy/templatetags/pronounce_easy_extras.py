from django import template
import json

register = template.Library()

@register.filter
def metric_score(data, metric):
    """Safely retrieve pronunciation metric from API response."""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return None
    metric_key = f"{metric.lower()}_score"
    score = None
    if isinstance(data, dict):
        score = data.get(metric_key, {}).get("pronunciation")
        if score is None:
            score = (
                data.get("text_score", {})
                .get(metric_key, {})
                .get("pronunciation")
            )
    return score if score is not None else ""
