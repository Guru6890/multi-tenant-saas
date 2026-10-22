# crm/services/customer_service.py
from typing import Optional, Dict, Any
from django.core.exceptions import ValidationError

from crm.models.customer import Customer
from crm.exceptions import CustomerAlreadyExistsError
from selectors.customer_selectors import customer_exists_by_email

from tenancy.models import TenantBaseModel
from authorization.services import AuthorizationService

CUSTOMER_CREATE = 'crm.customer.create'
CUSTOMER_UPDATE = 'crm.customer.update'
CUSTOMER_DELETE = 'crm.customer.delete'

class CustomerService:
    @staticmethod
    def create(
        *,
        user,
        workspace,
        display_name: str,
        customer_type: str,
        email: str,
        phone: Optional[str] = None,
        status: str = Customer.Status.ACTIVE,
        notes: Optional[str] = None
    ) -> Customer:
        AuthorizationService.require_permission(user, workspace, CUSTOMER_CREATE)
        
        if customer_exists_by_email(email):
            raise CustomerAlreadyExistsError(f'A customer with email {email} already exists in this workspace.')
        if customer_type.strip().upper() not in Customer.CustomerType.values:
            raise ValidationError('The customer type is not valid.')
        
        customer = Customer(
            workspace=workspace,
                type=customer_type,
                display_name=display_name,
                email=email,
                phone=phone,
                status=status,
                notes=notes,
        )

        customer.save()
        return customer
    
    @staticmethod
    def update(
        *,
        user,
        workspace,
        customer: Customer,
        data: Dict[str, Any]
    ) -> Customer:
        AuthorizationService.require_permission(user, workspace, CUSTOMER_UPDATE)

        allowed_fields = ['type', 'display_name', 'email', 'phone', 'notes']

        if 'email' in data:
            new_email = data.get('email')
            if new_email and new_email != customer.email:
                if customer_exists_by_email(new_email):
                    raise CustomerAlreadyExistsError(f'A customer with email {new_email} already exists in this workspace.')
                
        for field, value in data.items():
            if field in allowed_fields:
                setattr(customer, field, value)

        customer.save()
        return customer

    @staticmethod
    def change_status(
        *,
        user,
        workspace,
        customer: Customer,
        new_status: str
    ) -> Customer:
        AuthorizationService.require_permission(user, workspace, CUSTOMER_UPDATE)

        if new_status.strip().upper() not in Customer.Status.values:
            raise ValidationError('The given status is not valid.')

        if new_status == customer.status:
            return customer
        
        customer.status = new_status
        customer.save(update_fields=['status', 'updated_at'])
        return customer

    @staticmethod
    def delete(
        *,
        user,
        workspace,
        customer
    ) -> None:
        AuthorizationService.require_permission(user, workspace, CUSTOMER_DELETE)
        customer.delete()