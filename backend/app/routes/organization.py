from fastapi.responses import JSONResponse

from app.schemas import (
    APIResponse,
    OrganizationRequest,
    OrganizationResponse,
)
from app.models.User import Organization
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/organizations")

@router.post("/", response_model=APIResponse[OrganizationResponse])
async def add_times(
    request: OrganizationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Organization).where(
            Organization.id == current_user.organization_id
        )
    )
    org_record = result.scalar_one_or_none()

    if not org_record:
        return JSONResponse(
            status_code=404,
            content=APIResponse(
                success=False,
                message="Organization not found"
            ).model_dump()
        )

    if org_record.default_open_time or org_record.default_close_time:
        return JSONResponse(
            status_code=400,
            content=APIResponse(
                success=False,
                message="Open/Close times already set for this organization"
            ).model_dump()
        )

    update_data = request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(org_record, field, value)

    await db.commit()
    await db.refresh(org_record)

    return APIResponse(
        success=True,
        data=org_record,
        message="Open/Close times added successfully"
    )
    
@router.put("/", response_model=APIResponse[OrganizationResponse])
async def update_times(
    request: OrganizationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Organization).where(
            Organization.id == current_user.organization_id
        )
    )
    org_record = result.scalar_one_or_none()

    if not org_record:
        return JSONResponse(
            status_code=404,
            content=APIResponse(
                success=False,
                message="Organization not found"
            ).model_dump()
        )

    update_data = request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(org_record, field, value)

    await db.commit()
    await db.refresh(org_record)

    return APIResponse(
        success=True,
        data=org_record,
        message="Open/Close times updated successfully"
    )