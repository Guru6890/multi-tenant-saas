# crm/selectors/activity_selectors.py
from typing import Optional, Any
from django.db.models import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from crm.models import Activity
from authorization.services import AuthorizationService

ACTIVITY_VIEW = 'crm.activity.view'

def get_activity_for_object(
    *
    user,
    workspace,
    content_object: Any,
    activity_type: Optional[str] = None
) -> QuerySet[Activity]:
    AuthorizationService.require_permission(user, workspace, ACTIVITY_VIEW)

    ct = ContentType.objects.get_for_model(content_object.__class__)
    qs = Activity.objects.filter(content_type=ct, object_id=content_object.id)
    if activity_type:
        qs = qs.filter(activity_type=activity_type)

    return qs

def list_pending_tasks(
    *,
    user,
    workspace,
    user_filter
) -> QuerySet[Activity]:
    AuthorizationService.require_permission(user, workspace, ACTIVITY_VIEW)

    try:
        qs = Activity.objects.filter(
            activity_type=Activity.ActivityType.TASK,
            completed_at__isnull=True
        )
    except Activity.DoesNotExist:
        raise ValidationError('Activity cannot be found with given criteria.')
    
    if user_filter:
        qs = qs.filter(user=user)

    return qs