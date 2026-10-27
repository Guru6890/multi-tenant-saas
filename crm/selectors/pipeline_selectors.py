# crm/selectors/pipeline_selectors.py
from typing import Optional
from django.core.exceptions import ValidationError

from crm.models import Pipeline
from authorization.services import AuthorizationService

PIPELINE_VIEW = 'crm.pipeline.view'

def get_pipeline_by_id(user, workspace, id):
    AuthorizationService.require_permission(user, workspace, PIPELINE_VIEW)
    try:
        return (
            Pipeline.objects
            .prefetch_related('stages')
            .filter(id=id)
            .first()
        )
    except Pipeline.DoesNotExist:
        raise ValidationError('Pipeline cannot be found with given id.')
    
def get_default_pipeline(user, workspace):
    AuthorizationService.require_permission(user, workspace, PIPELINE_VIEW)
    try:
        return (
            Pipeline.objects
            .prefetch_related('stages')
            .filter(is_default=True)
            .first()
        )
    except Pipeline.DoesNotExist:
        raise ValidationError('No pipline were created.')
    
def list_pipeline(user, workspace, is_active: Optional[bool] = None):
    AuthorizationService.require_permission(user, workspace, PIPELINE_VIEW)
    qs = Pipeline.objects.prefetch_related('stages')
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs