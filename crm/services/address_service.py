# crm/services/address_service.py
from typing import Optional, Dict, Any
from django.core.exceptions import ValidationError
from django.db import transaction

from crm.models.customer import Customer, Address
from authorization.services import AuthorizationService

ADDRESS_CREATE = 'crm.address.create'
ADDRESS_UPDATE = 'crm.address.update'
ADDRESS_DELETE = 'crm.address.delete'

class AddressService:
    @staticmethod
    @transaction.atomic
    def create(
        *,
        user,
        workspace,
        customer: Customer,
        purpose: str,
        line1: str,
        city: str,
        state: str,
        postal_code: str,
        country: str,
        label: Optional[str] = None,
        line2: Optional[str] = None,
        is_primary: bool = False,
        is_active: bool = True
    ) -> Address:
        AuthorizationService.require_permission(user, workspace, ADDRESS_CREATE)

        if not purpose or purpose not in Address.Purpose.values:
            raise ValidationError('The purpose is not provided or the address purpose is invalid.')
        if is_primary:
            AddressService._demote_existing_primary(workspace=workspace, customer=customer, purpose=purpose)

        address = Address(
            workspace=workspace,
            customer=customer,
            purpose=purpose,
            label=label,
            line1=line1,
            line2=line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_primary=is_primary,
            is_active=is_active
        )

        address.full_clean()
        address.save()
        return address

    @staticmethod
    @transaction.atomic
    def update(
        *,
        user,
        workspace,
        address: Address,
        data: Dict[str, Any]
    ) -> Address:
        AuthorizationService.require_permission(user, workspace, ADDRESS_UPDATE)

        allowed_fields = {
            'purpose', 'label', 'line1', 'line2',
            'city', 'state', 'postal_code', 'country',
            'is_primary', 'is_active'
        }

        target_purpose = data.get('purpose', address.purpose)
        will_be_primary = data.get('is_primary', address.is_primary)

        if target_purpose not in Address.Purpose.values:
            raise ValidationError('Invalid address purpose provided.')
        
        if will_be_primary and (not address.is_primary or target_purpose != address.purpose):
            AddressService._demote_existing_primary(
                workspace=workspace,
                customer=address.customer,
                purpose=target_purpose,
                exclude_address_id=address.id,
            )

        for field, value in data.items():
            if field in allowed_fields:
                setattr(address, field, value)

        address.full_clean()
        address.save()
        return address
    
    @staticmethod
    def set_primary(
        *,
        user,
        workspace,
        address: Address
    ) -> Address:
        
        return AddressService.update(
            user=user,
            workspace=workspace,
            address=address,
            data={'is_primary': True}
        )
    
    @staticmethod
    def delete(*, user, workspace, address) -> None:
        AuthorizationService.require_permission(user, workspace, ADDRESS_DELETE)
        address.delete()

    @staticmethod
    def _demote_existing_primary(
        *,
        workspace,
        customer: Customer,
        purpose: str,
        exclude_address_id: Optional[Any] = None
    ):
        
        qs = Address.objects.filter(
            workspace=workspace,
            customer=customer,
            purpose=purpose,
            is_primary=True
        )

        if exclude_address_id:
            qs = qs.exclude(id=exclude_address_id)

        qs.update(is_primary=False)