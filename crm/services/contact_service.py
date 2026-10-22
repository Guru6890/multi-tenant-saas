# crm/services/contact_service.py
from typing import Optional, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError

from crm.models.contact import Contact
from crm.models.customer import Customer
from authorization.services import AuthorizationService

CONTACT_CREATE = 'crm.contact.create'
CONTACT_UPDATE = 'crm.contact.update'
CONTACT_DELETE = 'crm.contact.delete'

class ContactService:
    @staticmethod
    @transaction.atomic
    def create(
        *,
        user,
        workspace,
        customer: Customer,
        name: str,
        job_title: str,
        email: str,
        phone: Optional[str] = None,
        is_primary: bool = False,
        is_active: bool = True
    ) -> Contact:
        AuthorizationService.require_permission(user, workspace, CONTACT_CREATE)

        if is_primary:
            ContactService._demote_existing_primary(workspace=workspace, customer=customer)

        contact = Contact(
            workspace=workspace,
            customer=customer,
            name=name,
            job_title=job_title,
            email=email,
            phone=phone,
            is_primary=is_primary,
            is_active=is_active
        )

        contact.full_clean()
        contact.save()
        return contact
    
    @staticmethod
    @transaction.atomic
    def update(
        *,
        user,
        workspace,
        contact: Contact,
        data: Dict[str, Any]
    ) -> Contact:
        AuthorizationService.require_permission(user, workspace, CONTACT_UPDATE)

        allowed_fields = {'name', 'job_title', 'email', 'phone', 'is_primary', 'is_active'}

        will_be_primary = data.get('is_primary', contact.is_primary)
        if will_be_primary and not contact.is_primary:
            ContactService._demote_existing_primary(
                workspace=workspace,
                customer=contact.customer,
                exclude_id=contact.id
            )

        for field, value in data.items():
            if field in allowed_fields:
                setattr(contact, field, value)

        contact.full_clean()
        contact.save()
        return contact
    
    @staticmethod
    def set_primary(
        *,
        user,
        workspace,
        contact
    ) -> Contact:
        
        return ContactService.update(
            user=user,
            workspace=workspace,
            contact=contact,
            data={'is_primary': True}
        )
    
    @staticmethod
    def delete(
        *,
        user,
        workspace,
        contact
    ) -> None:
        AuthorizationService.require_permission(user, workspace, CONTACT_DELETE)
        contact.delete()

    @staticmethod
    def _demote_existing_primary(
        *,
        workspace,
        customer: Customer,
        exclude_id: Optional[Any] = None
    ) -> None:
        
        qs = Contact.objects.filter(
            workspace=workspace,
            customer=customer,
            is_primary=True
        )
        if exclude_id:
            qs = qs.exclude(id=exclude_id)

        qs.update(is_primary=False)