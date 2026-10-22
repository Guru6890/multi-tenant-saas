# crm/selectors/customer_selectors.py
from typing import Optional
from django.db.models import QuerySet, Q
from django.core.exceptions import ValidationError

from crm.models.customer import Customer

from authorization.services import AuthorizationService

CUSTOMER_VIEW = 'crm.customer.view'

def get_customer_by_id(*, user, workspace, customer_id):
    AuthorizationService.require_permission(user, workspace, CUSTOMER_VIEW)
    try:
        return Customer.objects.filter(id=customer_id).first()
    except Customer.DoesNotExist:
        raise ValidationError(f'The customer with the id {customer_id} not found.')

def customer_exists_by_email(email):
    return Customer.objects.filter(email__iexact=email).exists()

def list_customer(
    *,
    user,
    workspace,
    status: Optional[str] = None,
    customer_type: Optional[str] = None,
    search_query: Optional[str] = None
) -> QuerySet[Customer]:
    AuthorizationService.require_permission(user, workspace, CUSTOMER_VIEW)
    qs = Customer.objects.filter(workspace=workspace)

    if status:
        qs = qs.filter(status=status)
    if customer_type:
        qs = qs.filter(type=customer_type)
    if search_query:
        qs = qs.filter(
            Q(display_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    return qs

def get_customer_with_relations(*, user, workspace, customer_id):
    AuthorizationService.require_permission(user, workspace, CUSTOMER_VIEW)
    try:
        return(
            Customer.objects.filter(workspace=workspace)
            .prefetch_related('addresses', 'contacts')
            .filter(id=customer_id)
            .first()
        )
    except Customer.DoesNotExist:
        raise ValidationError(f'The customer with the id {customer_id} not found.')