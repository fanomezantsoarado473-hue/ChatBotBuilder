"""
analytics/utils.py

Fonction fanampiana hanombohana ny date range sy
hanaovana ny "comparaison" amin'ny periode teo aloha.
"""

from datetime import timedelta
from django.utils import timezone


RANGE_DAYS = {
    "today": 1,
    "7d": 7,
    "30d": 30,
}


def get_date_range(range_key: str):
    """
    Mamerina (date_from, date_to) ho an'ny periode "izao" arakaraka
    ny range_key (today / 7d / 30d).
    """
    days = RANGE_DAYS.get(range_key, 7)
    now = timezone.now()

    if range_key == "today":
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        date_from = now - timedelta(days=days)

    return date_from, now


def get_previous_period_range(range_key: str):
    """
    Mamerina ny date_from/date_to ho an'ny PERIODE TEO ALOHA mitovy
    haben'andro, ilaina ho an'ny calcul ny % change.
    Ohatra: raha "7d" androany, dia ny herinandro talohan'iny no
    averina eto.
    """
    days = RANGE_DAYS.get(range_key, 7)
    current_from, _ = get_date_range(range_key)
    previous_to = current_from
    previous_from = previous_to - timedelta(days=days)
    return previous_from, previous_to


def calculate_percentage_change(current: float, previous: float) -> float:
    """
    Mamerina ny % fiovana eo amin'ny roa valeur.
    Raha previous = 0, dia 100% raha current > 0, fa 0% raha tsia
    (mba tsy hisy division by zero).
    """
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    change = ((current - previous) / previous) * 100
    return round(change, 1)


def build_daily_history(queryset, date_field: str, days: int, value_func=None):
    """
    Manamboatra lisitra (array) misy ny isan'ny records isan'andro,
    feno (na dia 0 aza raha tsy misy data amin'iny andro iny),
    mba ho mazava ny chart any amin'ny frontend.

    value_func : fonction azo ampiasaina raha tianao avg/sum hafa
                 noho ny "count" tsotra.
    """
    from collections import defaultdict
    from django.utils import timezone

    counts = defaultdict(float)
    for item in queryset:
        day_key = getattr(item, date_field).date()
        if value_func:
            counts[day_key] += value_func(item)
        else:
            counts[day_key] += 1

    today = timezone.now().date()
    history = []
    for i in range(days - 1, -1, -1):
        day = today - timezone.timedelta(days=i)
        history.append(round(counts.get(day, 0), 2))

    return history