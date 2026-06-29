import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.syllabus import Subject, Concept
from app.services.ingestion.base import BaseIngestor


NCERT_BOOKS = {
    "class_6": [
        {"title": "Our Pasts I", "subject": "history", "chapters": 11},
        {"title": "The Earth Our Habitat", "subject": "geography", "chapters": 8},
        {"title": "Social and Political Life I", "subject": "polity", "chapters": 9},
    ],
    "class_7": [
        {"title": "Our Pasts II", "subject": "history", "chapters": 10},
        {"title": "Our Environment", "subject": "geography", "chapters": 10},
        {"title": "Social and Political Life II", "subject": "polity", "chapters": 10},
    ],
    "class_8": [
        {"title": "Our Pasts III", "subject": "history", "chapters": 10},
        {"title": "Resource and Development", "subject": "geography", "chapters": 6},
        {"title": "Social and Political Life III", "subject": "polity", "chapters": 10},
    ],
    "class_9": [
        {"title": "India and the Contemporary World I", "subject": "history", "chapters": 8},
        {"title": "Contemporary India I", "subject": "geography", "chapters": 6},
        {"title": "Democratic Politics I", "subject": "polity", "chapters": 6},
        {"title": "Economics", "subject": "economics", "chapters": 4},
    ],
    "class_10": [
        {"title": "India and the Contemporary World II", "subject": "history", "chapters": 8},
        {"title": "Contemporary India II", "subject": "geography", "chapters": 7},
        {"title": "Democratic Politics II", "subject": "polity", "chapters": 8},
        {"title": "Understanding Economic Development", "subject": "economics", "chapters": 5},
    ],
    "class_11": [
        {"title": "Ancient India (RS Sharma)", "subject": "history", "chapters": 28},
        {"title": "Themes in World History", "subject": "history", "chapters": 11},
        {"title": "Fundamentals of Physical Geography", "subject": "geography", "chapters": 16},
        {"title": "India Physical Environment", "subject": "geography", "chapters": 7},
        {"title": "Indian Constitution at Work", "subject": "polity", "chapters": 10},
        {"title": "Political Theory", "subject": "polity", "chapters": 10},
        {"title": "Indian Economic Development", "subject": "economics", "chapters": 10},
        {"title": "Sociology: Understanding Society", "subject": "sociology", "chapters": 5},
    ],
    "class_12": [
        {"title": "Themes in Indian History I", "subject": "history", "chapters": 4},
        {"title": "Themes in Indian History II", "subject": "history", "chapters": 4},
        {"title": "Themes in Indian History III", "subject": "history", "chapters": 7},
        {"title": "Fundamentals of Human Geography", "subject": "geography", "chapters": 10},
        {"title": "India People and Economy", "subject": "geography", "chapters": 12},
        {"title": "Politics in India since Independence", "subject": "polity", "chapters": 10},
        {"title": "Contemporary World Politics", "subject": "polity", "chapters": 9},
        {"title": "Introductory Macroeconomics", "subject": "economics", "chapters": 6},
        {"title": "Introductory Microeconomics", "subject": "economics", "chapters": 6},
    ],
}


STANDARD_BOOKS = [
    {"title": "Indian Polity", "author": "M. Laxmikanth", "book_type": "standard", "category": "polity", "chapters": 87},
    {"title": "A Brief History of Modern India", "author": "Spectrum", "book_type": "standard", "category": "history", "chapters": 28},
    {"title": "Certificate Physical and Human Geography", "author": "Goh Cheng Leong", "book_type": "standard", "category": "geography", "chapters": 36},
    {"title": "Environment", "author": "Shankar IAS", "book_type": "standard", "category": "environment", "chapters": 14},
    {"title": "Indian Economy", "author": "Ramesh Singh", "book_type": "standard", "category": "economics", "chapters": 26},
    {"title": "General Studies Paper 1", "author": "Nitin Singhania", "book_type": "standard", "category": "art_culture", "chapters": 15},
    {"title": "India Year Book", "author": "Government of India", "book_type": "reference", "category": "general", "chapters": 30},
]


class NCERTIngestor(BaseIngestor):
    async def ingest_all(
        self, subject_map: Dict[str, UUID]
    ) -> Dict[str, Any]:
        stats = {"books": 0, "chapters": 0, "mappings": 0}

        for class_level, books in NCERT_BOOKS.items():
            for book_info in books:
                subject_name = book_info["subject"]
                syllabus_subject_id = subject_map.get(subject_name)
                if not syllabus_subject_id:
                    continue

                book = await self.find_or_create_book(
                    title=book_info["title"],
                    author="NCERT",
                    publisher="NCERT",
                    book_type="ncert",
                    category=subject_name,
                    description=f"NCERT {class_level.replace('_', ' ')} - {book_info['title']}",
                    is_authoritative=True,
                    total_chapters=book_info["chapters"],
                    extra_metadata={"class": class_level, "subject": subject_name},
                )
                stats["books"] += 1

                for ch_num in range(1, book_info["chapters"] + 1):
                    chapter = await self.add_chapter(
                        book=book,
                        chapter_number=ch_num,
                        title=f"Chapter {ch_num}",
                        description=f"Chapter {ch_num} of {book_info['title']}",
                    )
                    stats["chapters"] += 1

        await self.db.commit()
        return stats


class StandardBookIngestor(BaseIngestor):
    async def ingest_all(
        self, subject_map: Dict[str, UUID]
    ) -> Dict[str, Any]:
        stats = {"books": 0, "chapters": 0, "mappings": 0}

        for book_info in STANDARD_BOOKS:
            book = await self.find_or_create_book(
                title=book_info["title"],
                author=book_info["author"],
                book_type=book_info["book_type"],
                category=book_info["category"],
                description=f"{book_info['title']} by {book_info['author']}",
                is_authoritative=True,
                total_chapters=book_info["chapters"],
            )
            stats["books"] += 1

            for ch_num in range(1, book_info["chapters"] + 1):
                chapter = await self.add_chapter(
                    book=book,
                    chapter_number=ch_num,
                    title=f"Chapter {ch_num}",
                )
                stats["chapters"] += 1

        await self.db.commit()
        return stats
