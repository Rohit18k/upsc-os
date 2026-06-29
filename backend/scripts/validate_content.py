async def validate_db():
    from app.database.session import async_session_factory
    from app.models import Subject, Module, Topic, Subtopic, Concept
    from app.models import PYQ, Book, ContentMapping, SyllabusSignal
    from sqlalchemy import select, func

    async with async_session_factory() as session:
        errors = []

        subjects = (await session.execute(select(Subject))).scalars().all()
        print(f"  Subjects: {len(subjects)}")
        if not subjects:
            errors.append("No subjects found — seed syllabus first")

        for s in subjects:
            modules = (await session.execute(
                select(Module).where(Module.subject_id == s.id)
            )).scalars().all()
            for m in modules:
                topics = (await session.execute(
                    select(Topic).where(Topic.module_id == m.id)
                )).scalars().all()
                for t in topics:
                    concepts = (await session.execute(
                        select(Concept).where(Concept.topic_id == t.id)
                    )).scalars().all()
                    subtopics = (await session.execute(
                        select(Subtopic).where(Subtopic.topic_id == t.id)
                    )).scalars().all()

                    if not concepts and not subtopics:
                        errors.append(
                            f"Topic '{t.display_name}' ({t.id}) has no concepts or subtopics"
                        )

        pyq_count = (await session.execute(select(func.count(PYQ.id)))).scalar() or 0
        print(f"  PYQs: {pyq_count}")

        mapping_count = (await session.execute(select(func.count(ContentMapping.id)))).scalar() or 0
        print(f"  Content Mappings: {mapping_count}")

        signal_count = (await session.execute(select(func.count(SyllabusSignal.id)))).scalar() or 0
        print(f"  Syllabus Signals: {signal_count}")

        if errors:
            print(f"\n  Validation errors ({len(errors)}):")
            for e in errors[:20]:
                print(f"    - {e}")
        else:
            print("\n  All validations passed")

        return len(errors) == 0


async def main():
    import sys
    print("=== Content Intelligence DB Validation ===\n")
    ok = await validate_db()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
