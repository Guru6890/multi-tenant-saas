# crm/service/lead_service.py
from typing import Optional, Any, Dict
from django.core.exceptions import ValidationError
from django.db import transaction

from crm.models.lead import Lead
from authorization.services import AuthorizationService
from identity.models import User

LEAD_CREATE = 'crm.lead.create'
LEAD_UPDATE = 'crm.lead.update'
LEAD_DELETE = 'crm.lead.delete'

class LeadService:
    @staticmethod
    def create(
        *,
        user,
        workspace,
        type: str,
        display_name: str,
        email: str,
        phone: Optional[str] = None,
        preferred_contact_method: str = Lead.ContactMethod.EMAIL,
        status: str = Lead.Status.NEW,
        source: str,
        address: Optional[str] = None,
        assigned_user: Optional[User] = None,
        notes: Optional[str] = None,
        qualification_score: Optional[int] = None
    ) -> Lead:
        AuthorizationService.require_permission(user, workspace, LEAD_CREATE)

        if type.strip().upper() not in Lead.LeadType.values:
            raise ValidationError({'type': 'Invalid lead type provided.'})
        if source.strip().upper() not in Lead.Source.values:
            raise ValidationError({'source': 'invalid lead source provided.'})
        if status.strip().upper() not in Lead.Status.values:
            raise ValidationError({'status': 'Invalid lead status provided.'})
        if preferred_contact_method.strip().upper() not in Lead.ContactMethod.values:
            raise ValidationError('Invalid preferred contact method provided.')
        
        lead = Lead(
            workspace=workspace,
            type=type,
            display_name=display_name,
            email=email,
            phone=phone,
            preferred_contact_method=preferred_contact_method,
            status=status,
            source=source,
            address=address,
            assigned_user=assigned_user,
            notes=notes,
            qualification_score=qualification_score
        )

        lead.full_clean()
        lead.save()
        return lead
    
    @staticmethod
    def update(
        *,
        user: User,
        workspace,
        lead: Lead,
        data: Dict[str, Any]
    ) -> Lead:
        AuthorizationService.require_permission(user, workspace, LEAD_UPDATE)

        allowed_fields = {
            'display_name', 'email', 'phone',
            'preferred_contact_method', 'status', 'source',
            'address', 'assigned_user', 'notes', 'qualification_score'
        }

        if lead.status == Lead.Status.CONVERTED:
            raise ValidationError('Converted leads cannot be re-opened or modified directly.')
        
        for field, value in data.items():
            if field in allowed_fields:
                setattr(lead, field, value)

        lead.full_clean()
        lead.save()
        return lead
    
    @staticmethod
    def assign(
        *,
        user: User,
        workspace,
        lead: Lead
    ) -> Lead:
        
        return LeadService.update(
            user=user,
            workspace=workspace,
            lead=lead,
            data={'assigned_user': user}
        )
    
    @staticmethod
    def change_status(
        *,
        user: User,
        workspace,
        lead: Lead,
        new_status: str
    ) -> Lead:
        AuthorizationService.require_permission(user, workspace, LEAD_UPDATE)

        new_status = new_status.strip().upper()
        if new_status not in Lead.Status.values:
            raise ValidationError('Invalid lead status provided.')
        
        if lead.status == new_status:
            return lead
        
        if lead.status == Lead.Status.CONVERTED:
            raise ValidationError("A converted lead's status cannot be changed.")
        if new_status == Lead.Status.CONVERTED:
            raise ValidationError('Use LeadConversionService to convert a lead rather than updating status directly.')
        
        lead.status = new_status
        lead.save(update_fields=['status', 'updated_at'])
        return lead
    
    @staticmethod
    def update_qualification_score(
        user: User,
        workspace,
        lead: Lead,
        qualification_score: int
    ) -> Lead:
        
        if not (0 <= qualification_score <= 100):
            raise ValidationError('Qualification score must be between 0 and 100.')

        return LeadService.update(
            user=user,
            workspace=workspace,
            lead=lead,
            data={'qualification_score': qualification_score}
        )

    @staticmethod
    def delete(
        *,
        user: Any,
        workspace: Any,
        lead: Lead,
    ) -> None:
        AuthorizationService.require_permission(user, workspace, LEAD_DELETE)
        lead.delete()