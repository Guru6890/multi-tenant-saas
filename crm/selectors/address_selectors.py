# crm/selectors/address_selectors.py
from typing import Optional
from django.db.models import QuerySet
from django.core.exceptions import ValidationError

from crm.models.customer import Address, Customer
from authorization.services import AuthorizationService

ADDRESS_VIEW = 'crm.address.view'

def get_address_queryset(workspace):
    return Address.objects.filter(workspace=workspace)

def get_address_by_id(user,workspace,id):
    AuthorizationService.require_permission(user, workspace, ADDRESS_VIEW)
    try:
        return get_address_queryset(workspace).filter(id=id).first()
    except Address.DoesNotExist:
        raise ValidationError(f'The address with id {id} cannot be found.')
    
def list_addresses_for_customers(
    *,
    user,
    workspace,
    customer: Customer,
    purpose: Optional[str] = None,
    is_primary: Optional[bool] = None,
    is_active: Optional[bool] = None
) -> QuerySet[Address]:
    AuthorizationService.require_permission(user, workspace, ADDRESS_VIEW)

    try:
        qs = get_address_queryset(workspace).filter(customer=customer)
    except Address.DoesNotExist:
        raise ValidationError('Can not find any address for the given customer.')
    
    if purpose:
        qs = qs.filter(purpose=purpose)
    if is_primary is not None:
        qs = qs.filter(is_primary=is_primary)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    
    return qs