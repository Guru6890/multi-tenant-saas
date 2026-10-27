# crm/services/activity_service.py
from typing import Optional, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from crm.models import Activity
from authorization.services import AuthorizationService

ACTIVITY_CREATE = 'crm.activity.create'
ACTIVITY_UPDATE = 'crm.activity.update'
ACTIVITY_DELETE = 'crm.activity.delete'

class ActivityService:
    @staticmethod
    def log(
        *,
        user,
        workspace,
        content_object: Any,
        activity_type: str = Activity.ActivityType.NOTE,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[Any] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Activity:
        AuthorizationService.require_permission(user, workspace, ACTIVITY_CREATE)

        if activity_type not in Activity.ActivityType.values:
            raise ValidationError('Invalid activity type provided.')
        
        if hasattr(content_object, 'workspace') and content_object.workspace != workspace:
            raise ValidationError('Cannot attach activity to an object outside the workspace scope.')
        
        ct = ContentType.objects.get_for_model(content_object.__class__)

        activity = Activity(
            workspace=workspace,
            user=user,
            activity_type=activity_type,
            subject=subject,
            description=description,
            due_date=due_date,
            content_type=ct,
            onject_id=content_object.id,
            meta_data=meta_data or {}
        )

        activity.full_clean()
        activity.save()
        return activity
    
    @staticmethod
    @transaction.atomic
    def complete_task(
        *,
        user,
        workspace,
        activity: Activity
    ) -> Activity:
        AuthorizationService.require_permission(user, workspace, ACTIVITY_UPDATE)

        if activity.activity_type != Activity.ActivityType.TASK:
            raise ValidationError('Only task-type activities can be completed.')
        
        if activity.completed_at is not None:
            return activity
        
        activity.completed_at = timezone.now()
        activity.full_clean()
        activity.save(update_fields=['completed_at', 'updated_at'])
        return activity
    
    