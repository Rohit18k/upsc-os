from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.response import success_response
from app.models.syllabus import Subject, Topic, Concept
from app.models.versioning import ContentVersion
from app.services.ingestion.books import NCERTIngestor, StandardBookIngestor
from app.services.ingestion.pyq_importer import PYQImporter
from app.services.content.lesson_factory import LessonFactory
from app.services.content.flashcard_factory import FlashcardFactory
from app.services.content.revision_factory import RevisionFactory
from app.services.content.answer_factory import AnswerWritingFactory
from app.services.validation.pipeline import ValidationPipeline
from app.services.batch.processor import get_processor

router = APIRouter()


@router.post("/ingest/ncert")
async def ingest_ncert(db: AsyncSession = Depends(get_db)):
    subject_map = {}
    result = await db.execute(select(Subject))
    for s in result.scalars().all():
        subject_map[s.name.lower()] = s.id

    ingestor = NCERTIngestor(db)
    stats = await ingestor.ingest_all(subject_map)
    return success_response(stats, message="NCERT books ingested")


@router.post("/ingest/standard-books")
async def ingest_standard_books(db: AsyncSession = Depends(get_db)):
    subject_map = {}
    result = await db.execute(select(Subject))
    for s in result.scalars().all():
        subject_map[s.name.lower()] = s.id

    ingestor = StandardBookIngestor(db)
    stats = await ingestor.ingest_all(subject_map)
    return success_response(stats, message="Standard books ingested")


@router.post("/ingest/pyqs")
async def ingest_pyqs(db: AsyncSession = Depends(get_db)):
    subject_map = {}
    result = await db.execute(select(Subject))
    for s in result.scalars().all():
        subject_map[s.name.lower()] = s.id

    topic_map = {}
    for subj_name, subj_id in subject_map.items():
        modules_result = await db.execute(
            select(Topic).join(Topic.module).where(
                Topic.module.has(subject_id=subj_id)
            )
        )
        topics = modules_result.scalars().all()
        topic_map[subj_name] = {t.name: t.id for t in topics}

    importer = PYQImporter(db)
    stats = await importer.generate_sample_pyqs(subject_map, topic_map)
    signal_stats = await importer.compute_signals()
    stats.update(signal_stats)
    return success_response(stats, message="PYQs imported with signals computed")


@router.post("/generate/lessons")
async def generate_lessons(
    topic_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    topic_result = await db.execute(
        select(Topic).where(Topic.id == topic_id)
    )
    topic = topic_result.scalar_one_or_none()
    if not topic:
        from app.core.exception_handlers import NotFoundError
        raise NotFoundError("Topic not found")

    factory = LessonFactory(db)
    lesson_data = LessonFactory.build_lesson_data(
        title=topic.display_name,
        learning_objectives=[f"Understand {topic.display_name}", f"Analyze key concepts in {topic.display_name}"],
        prerequisites=topic.prerequisites or [],
        core_theory=[{"heading": "Introduction", "body": f"Overview of {topic.display_name}."}],
        examples=[{"title": f"Example: {topic.display_name}", "body": "Sample example text."}],
        memory_tricks=[f"Mnemonic for {topic.display_name}"],
        mind_map={"central": topic.display_name, "nodes": []},
        common_mistakes=["Common mistake 1", "Common mistake 2"],
        pyq_references=[],
        revision_notes=[f"Key point about {topic.display_name}"],
        flashcards=[{"front": f"What is {topic.display_name}?", "back": f"{topic.display_name} is...", "card_type": "concept"}],
        summary=f"Summary of {topic.display_name}",
        references=[],
    )
    result = await factory.create_lesson(
        title=topic.display_name,
        lesson_data=lesson_data,
        syllabus_node_id=topic.id,
        syllabus_node_type="topic",
        source="lesson_generator",
    )

    pipeline = ValidationPipeline(db)
    content_result = await db.execute(
        select(ContentVersion).where(ContentVersion.content_id == UUID(result["content_id"]))
    )
    content = content_result.scalar_one_or_none()
    if content:
        await pipeline.validate(content, source="lesson_generator")

    return success_response(result, message=f"Lesson generated for {topic.display_name}")


@router.post("/generate/flashcards")
async def generate_flashcards(
    topic_id: UUID = Query(...),
    count: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    topic_result = await db.execute(
        select(Topic).where(Topic.id == topic_id)
    )
    topic = topic_result.scalar_one_or_none()
    if not topic:
        from app.core.exception_handlers import NotFoundError
        raise NotFoundError("Topic not found")

    concepts_result = await db.execute(
        select(Concept).where(Concept.topic_id == topic_id)
    )
    concepts = concepts_result.scalars().all()

    factory = FlashcardFactory(db)
    flashcards = []
    for i in range(min(count, max(len(concepts), 1))):
        concept = concepts[i % max(len(concepts), 1)] if concepts else None
        flashcards.append({
            "front": f"What is {concept.display_name if concept else topic.display_name}?",
            "back": f"{concept.display_name if concept else topic.display_name} refers to...",
            "card_type": "concept" if concept else "definition",
        })

    results = await factory.bulk_create(
        flashcards=flashcards,
        syllabus_node_id=topic.id,
        syllabus_node_type="topic",
    )

    return success_response(results, message=f"{len(results)} flashcards generated")


@router.post("/generate/revision-notes")
async def generate_revision_notes(
    topic_id: UUID = Query(...),
    note_type: str = Query("one_page_notes"),
    db: AsyncSession = Depends(get_db),
):
    topic_result = await db.execute(
        select(Topic).where(Topic.id == topic_id)
    )
    topic = topic_result.scalar_one_or_none()
    if not topic:
        from app.core.exception_handlers import NotFoundError
        raise NotFoundError("Topic not found")

    factory = RevisionFactory(db)
    result = await factory.create_revision_note(
        note_type=note_type,
        title=f"{topic.display_name} - {note_type.replace('_', ' ').title()}",
        key_points=[f"Key point 1: {topic.display_name}", f"Key point 2: Important aspect"],
        syllabus_node_id=topic.id,
        syllabus_node_type="topic",
        mnemonics=[f"Mnemonic for {topic.display_name}"],
        quick_references=[{"key": topic.display_name, "value": "Reference value"}],
        exam_tips=[f"Focus on {topic.display_name} for UPSC"],
    )

    return success_response(result, message=f"Revision note generated for {topic.display_name}")


@router.get("/jobs")
async def list_jobs():
    processor = get_processor()
    jobs = processor.list_jobs()
    return success_response(jobs)

