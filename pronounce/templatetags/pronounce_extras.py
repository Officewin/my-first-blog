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
    try:
        return data.get(metric_key, {}).get("pronunciation")
    except AttributeError:
        pass
    try:
        return (
            data.get("text_score", {})
            .get(metric_key, {})
            .get("pronunciation")
        )
    except AttributeError:
        return None
