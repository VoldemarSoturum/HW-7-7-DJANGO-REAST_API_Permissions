from rest_framework import serializers
from .models import Advertisement

MAX_OPEN_ADS = 10

def _is_open_status(value):
    try:
        return value == Advertisement.Status.OPEN
    except Exception:
        return str(value).upper() == 'OPEN'

def validate_open_ads_limit(user, desired_status, exclude_id=None):
    if not _is_open_status(desired_status):
        return
    qs = Advertisement.objects.filter(creator=user)
    try:
        qs = qs.filter(status=Advertisement.Status.OPEN)
    except Exception:
        qs = qs.filter(status='OPEN')
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    if qs.count() >= MAX_OPEN_ADS:
        raise serializers.ValidationError(
            {'status': f'Превышен лимит: не более {MAX_OPEN_ADS} открытых объявлений.'}
        )
