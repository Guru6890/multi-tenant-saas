# crm/selectors/contact_selectors.py
from typing import Optional, Any
from django.db.models import QuerySet
from django.core.exceptions import ValidationError

from crm.models.contact import Contact
from crm.models.customer import Customer

from authorization.services import AuthorizationService

CONTACT_VIEW = 'crm.contact.view'

def get_contact_queryset(*, workspace) -> QuerySet[Contact]:
    return Contact.objects.filter(workspace=workspace)

def get_contact_by_id(*, user, workspace, id) -> Optional[Contact]:
    AuthorizationService.require_permission(user, workspace, CONTACT_VIEW)
    try:
        return get_contact_queryset(workspace=workspace).filter(id=id).first()
    except Contact.DoesNotExist:
        raise ValidationError('Contact cannot with the given id.')
    
def list_contacts_for_customer(*, user, workspace, customer:Customer, is_active: Optional[bool]=None) -> QuerySet[Contact]:
    AuthorizationService.require_permission(user, workspace, CONTACT_VIEW)
    qs = get_contact_queryset(workspace=workspace).filter(customer=customer)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs

def get_primary_contact(*, user, workspace, customer) -> Optional[Contact]:
    AuthorizationService.require_permission(user, workspace, CONTACT_VIEW)
    try:
        return (get_contact_queryset(workspace=workspace)
                .filter(workspace=workspace, is_primary=True)
                .first()
        )
    except Contact.DoesNotExist:
        raise ValidationError('The customer does not have an active primary contact.')