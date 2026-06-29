from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.core.response import success_response, paginated_response
from app.models.versioning import ContentVersion, Citation
from app.models.mapping import ContentMapping

router = APIRouter()


CONTENT_TYPES = ["lesson", "flashcard", "revision_note"]


@router.get("/search")
async def search_content(
    q: str = Query(..., min_length=1),
    content_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(ContentVersion)
    count_query = select(func.count(ContentVersion.id))

    type_filter = [ContentVersion.content_type.in_(CONTENT_TYPES)]
    if content_type:
        type_filter = [ContentVersion.content_type == content_type]

    pattern = f"%{q}%"
    text_filter = ContentVersion.title.ilike(pattern)

    query = query.where(*type_filter, text_filter)
    count_query = count_query.where(*type_filter, text_filter)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = query.order_by(ContentVersion.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return paginated_response(
        items=[
            {
                "content_id": str(v.content_id),
                "content_type": v.content_type,
                "title": v.title,
                "version_number": v.version_number,
                "source": v.source,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/by-syllabus-node/{node_id}")
async def get_content_by_node(
    node_id: UUID,
    node_type: str = Query(...),
    content_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    mapping_query = select(ContentMapping).where(
        ContentMapping.syllabus_node_id == node_id,
        ContentMapping.syllabus_node_type == node_type,
    )
    if content_type:
        mapping_query = mapping_query.where(ContentMapping.content_type == content_type)
    mappings_result = await db.execute(mapping_query)
    mappings = mappings_result.scalars().all()

    content_ids = [(m.content_id, m.content_type) for m in mappings]
    if not content_ids:
        return success_response([])

    results = []
    for cid, ctype in content_ids:
        version_result = await db.execute(
            select(ContentVersion)
            .where(
                ContentVersion.content_id == cid,
                ContentVersion.content_type == ctype,
            )
            .order_by(ContentVersion.version_number.desc())
            .limit(1)
        )
        version = version_result.scalar_one_or_none()
        if version:
            results.append({
                "content_id": str(version.content_id),
                "content_type": version.content_type,
                "title": version.title,
                "content_data": version.content_data,
                "version_number": version.version_number,
                "source": version.source,
                "created_at": version.created_at.isoformat() if version.created_at else None,
            })

    return success_response(results)


@router.get("/{content_type}/{content_id}")
async def get_content(
    content_type: str,
    content_id: UUID,
    version_number: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ContentVersion).where(
        ContentVersion.content_id == content_id,
        ContentVersion.content_type == content_type,
    )
    if version_number:
        query = query.where(ContentVersion.version_number == version_number)
    else:
        query = query.order_by(ContentVersion.version_number.desc())

    result = await db.execute(query)
    version = result.scalar_one_or_none()
    if not version:
        from app.core.exception_handlers import NotFoundError
        raise NotFoundError(f"{content_type} not found")

    citations_result = await db.execute(
        select(Citation).where(Citation.content_version_id == version.id)
    )
    citations = citations_result.scalars().all()

    return success_response({
        "content_id": str(version.content_id),
        "content_type": version.content_type,
        "title": version.title,
        "version_number": version.version_number,
        "content_data": version.content_data,
        "change_summary": version.change_summary,
        "source": version.source,
        "checksum": version.checksum,
        "citations": [
            {
                "source_type": c.source_type,
                "source_title": c.source_title,
                "page_reference": c.page_reference,
                "excerpt": c.excerpt,
                "confidence": c.confidence,
            }
            for c in citations
        ],
        "created_at": version.created_at.isoformat() if version.created_at else None,
    })


@router.get("/types/summary")
async def content_type_summary(db: AsyncSession = Depends(get_db)):
    results = []
    for ctype in CONTENT_TYPES:
        count_result = await db.execute(
            select(func.count(func.distinct(ContentVersion.content_id))).where(
                ContentVersion.content_type == ctype
            )
        )
        count = count_result.scalar() or 0
        results.append({"content_type": ctype, "count": count})

    return success_response(results)
