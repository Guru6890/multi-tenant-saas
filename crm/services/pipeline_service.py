# crm/services/pipeline_service.py
from typing import Optional, Any, Dict, List
from django.db import transaction
from django.db import models
from django.core.exceptions import ValidationError

from crm.models import Pipeline, PipelineStage
from crm.selectors.pipeline_selectors import get_pipeline_by_id

from authorization.services import AuthorizationService

PIPELINE_CREATE = 'crm.pipeline.create'
PIPELINE_UPDATE = 'crm.pipeline.update'
PIPELINE_DELETE = 'crm.pipeline.delete'

class PipelineService:
    @staticmethod
    @transaction.atomic
    def create(
        *,
        user,
        workspace,
        name: str,
        description: Optional[str] = None,
        is_default: bool = False,
        stages_data: Optional[List[Dict[str, Any]]] = None
    ) -> Pipeline:
        AuthorizationService.require_permission(user, workspace, PIPELINE_CREATE)

        workspace_pipelines = Pipeline.objects.filter(workspace=workspace).select_for_update()
        has_existing_default = workspace_pipelines.filter(is_default=True).exists()

        if is_default:
            if has_existing_default:
                workspace_pipelines.filter(is_default=True).update(is_default=False)
        else:
            if not has_existing_default:
                is_default = True

        pipeline = Pipeline(
            workspace=workspace,
            name=name,
            description=description,
            is_default=is_default
        )

        pipeline.full_clean()
        pipeline.save()

        if not stages_data:
            # Provide sensible default initial stages if none provided
            stages_data = [
                {"name": "Qualified", "order": 1, "probability": 20, "stage_type": PipelineStage.StageType.OPEN},
                {"name": "Proposal", "order": 2, "probability": 60, "stage_type": PipelineStage.StageType.OPEN},
                {"name": "Won", "order": 3, "probability": 100, "stage_type": PipelineStage.StageType.WON},
                {"name": "Lost", "order": 4, "probability": 0, "stage_type": PipelineStage.StageType.LOST},
            ]

        PipelineService._validate_and_create_stages(
            user=user,
            workspace=workspace,
            pipeline=pipeline,
            stages_data=stages_data
        )

        return pipeline
    
    @staticmethod
    @transaction.atomic
    def update(
        *,
        user,
        workspace,
        pipeline,
        data: Dict[str, Any]
    ) -> Pipeline:
        AuthorizationService.require_permission(user, workspace, PIPELINE_UPDATE)

        allowed_fields = {'name', 'description', 'is_active'}

        unknown_fields = set(data.keys()) - allowed_fields
        if unknown_fields:
            raise ValidationError(f"Unknown fields provided for update: {', '.join(unknown_fields)}")

        is_active = data.get('is_active', pipeline.is_active)
        if pipeline.is_default and not is_active:
            raise ValidationError("Cannot deactivate the default pipeline. Set another pipeline as default first.")

        for field, value in data.items():
            setattr(pipeline, field, value)

        pipeline.full_clean()
        pipeline.save()

        return pipeline
    
    @staticmethod
    @transaction.atomic
    def set_as_default(
        *,
        user,
        workspace,
        pipeline: Pipeline,
    ) -> Pipeline:
        AuthorizationService.require_permission(user, workspace, PIPELINE_UPDATE)

        if pipeline.is_default:
            return pipeline
        
        if pipeline.is_active is False:
            raise ValidationError("Cannot set an inactive pipeline as default. Activate it first.")
        
        workspace_pipelines = Pipeline.objects.filter(workspace=workspace).select_for_update()
        workspace_pipelines.filter(is_default=True).update(is_default=False)
        pipeline.is_default = True
        pipeline.full_clean()
        pipeline.save(update_fields=['is_default', 'updated_at'])

        return pipeline
    
    @staticmethod
    @transaction.atomic
    def delete(
        *,
        user,
        workspace,
        pipeline
    ) -> None:
        AuthorizationService.require_permission(user, workspace, PIPELINE_DELETE)

        locked_pipeline = Pipeline.objects.filter(
            id=pipeline.id,
            workspace=workspace
        ).select_for_update().first()

        if not locked_pipeline:
            raise ValidationError('Pipeline not found.')

        if pipeline.is_default:
            raise ValidationError("Cannot delete the default pipeline. Set another pipeline as default first.")
        
        has_deals = locked_pipeline.stages.filter(deals__isnull=False).exists()
        if has_deals:
            raise ValidationError("Cannot delete a pipeline that has associated deals. Please reassign or delete the deals first.")

        pipeline.delete()

    @staticmethod
    def _validate_and_create_stages(
        *,
        user,
        workspace,
        pipeline: Pipeline,
        stages_data: List[Dict[str, Any]]
    ) -> None:
        names = set()
        orders = set()

        for stage_data in stages_data:
            name = stage_data.get('name').strip().upper()
            order = stage_data.get('order')
            probability = stage_data.get('probability', 10)
            stage_type = stage_data.get('stage_type', PipelineStage.StageType.OPEN)

            if not name or not isinstance(name, str) or name == '':
                raise ValidationError("Each stage must have a valid 'name'.")
            
            if not isinstance(order, int) or order < 1:
                raise ValidationError("Each stage must have a valid 'order' (positive integer).")

            if name in names:
                raise ValidationError(f"Duplicate stage name '{name}' found in stages data.")
            names.add(name)

            if order in orders:
                raise ValidationError(f"Duplicate stage order '{order}' found in stages data.")
            orders.add(order)

            if not isinstance(probability, int) or not (0 <= probability <= 100):
                raise ValidationError(f"Stage '{name}' has an invalid 'probability'. Must be between 0 and 100.")

            if stage_type not in PipelineStage.StageType.values:
                raise ValidationError(f"Stage '{name}' has an invalid 'stage_type'.")

            PipelineStageService.create(
                user=user,
                workspace=workspace,
                pipeline=pipeline,
                name=name,
                order=order,
                probability=probability,
                stage_type=stage_type
            )

class PipelineStageService:
    @staticmethod
    def create(
        *,
        user,
        workspace,
        pipeline: Pipeline,
        name: str,
        order: int,
        probability: int = 10,
        stage_type: str = PipelineStage.StageType.OPEN
    ) -> PipelineStage:
        AuthorizationService.require_permission(user, workspace, PIPELINE_UPDATE)

        if stage_type not in PipelineStage.StageType.values:
            raise ValidationError('Invalid stage type provided.')
        
        stage = PipelineStage(
            workspace=workspace,
            pipeline=pipeline,
            name=name,
            order=order,
            probability=probability,
            stage_type=stage_type
        )

        stage.full_clean()
        stage.save()
        return stage
    
    @staticmethod
    def update(
        *,
        user,
        workspace,
        stage: PipelineStage,
        data: Dict[str, Any]
    ) -> PipelineStage:
        AuthorizationService.require_permission(user, workspace, PIPELINE_UPDATE)

        allowed_fields = {'name', 'order', 'probability'}
        unknown_fields = set(data.keys()) - allowed_fields
        if unknown_fields:
            raise ValidationError(f"Unknown or unauthorized fields: {list(unknown_fields)}")
        
        if 'name' in data.keys():
            name = data.get('name').strip().upper()
            if not isinstance(name, str) or name == '':
                raise ValidationError("Each stage must have a valid 'name'.")
            
        if 'order' in data.keys():
            order = data.get('order')
            if not isinstance(order, int) or isinstance(order, bool) or order < 1:
                raise ValidationError("Each stage must have a valid 'order' (positive integer).")

        if 'probability' in data.keys():
            probability = data.get('probability')
            if not isinstance(probability, int) or not (0 <= probability <= 100):
                raise ValidationError(f"Stage '{stage.name}' has an invalid 'probability'. Must be between 0 and 100.")
        
        for field, value in data.items():
            if field in allowed_fields:
                setattr(stage, field, value)

        stage.full_clean()
        stage.save()
        return stage
    
    @staticmethod
    @transaction.atomic
    def reorder_stages(
        *,
        user,
        workspace,
        pipeline: Pipeline,
        stage_order_map: Dict[str, int]
    ) -> List[PipelineStage]:
        AuthorizationService.require_permission(user, workspace, PIPELINE_UPDATE)

        stages = list(pipeline.stages.all())
        stage_dict = {str(s.id): s for s in stages}

        if set(stage_order_map.keys()) != set(stage_dict.keys()):
            raise ValidationError("Stage order map must include all stages for the pipeline.")
        
        new_orders = list(stage_order_map.values())
        if len(set(new_orders)) != len(new_orders):
            raise ValidationError("Stage order values must be unique.")
        for order in new_orders:
            if not isinstance(order, int) or order < 1:
                raise ValidationError("All stage orders must be positive integers >= 1.")
        
        PipelineStage.objects.filter(pipeline=pipeline).update(order=models.F('order')+1000)

        updated_stages = []
        for stage_id, new_order in stage_order_map.items():
            stage = stage_dict[stage_id]
            stage.order = new_order
            stage.full_clean()
            stage.save(update_fields=['order', 'updated_at'])
            updated_stages.append(stage)

        return sorted(updated_stages, key=lambda s: s.order)
    
    @staticmethod
    @transaction.atomic
    def delete(*, user, workspace, stage: PipelineStage) -> None:
        AuthorizationService.require_permission(user, workspace, PIPELINE_UPDATE)

        locked_stage = PipelineStage.objects.filter(
            id=stage.id, 
            workspace=workspace
        ).select_for_update().first()

        if not locked_stage:
            raise ValidationError('Stage not found.')

        if locked_stage.deals.exists():
            raise ValidationError('Cannot delete a stage that contains deals. Reassign deals first.')

        stage.delete()