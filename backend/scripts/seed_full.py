async def seed_syllabus():
    from app.database.session import async_session_factory
    from app.models.syllabus import Subject, Module, Topic, Subtopic, Concept
    from sqlalchemy import select, func

    SYLLABUS_DATA = {
        "history": {
            "display_name": "History",
            "exam_type": "mains",
            "gs_paper": "GS-1",
            "sort_order": 1,
            "modules": {
                "ancient_history": {
                    "display_name": "Ancient History",
                    "sort_order": 1,
                    "topics": {
                        "indus_valley": {"display_name": "Indus Valley Civilization", "difficulty": "medium", "sort_order": 1, "concepts": ["Town Planning", "Economy", "Religion", "Decline"], "subtopics": ["Harappa", "Mohenjo-Daro", "Dholavira"]},
                        "vedic_age": {"display_name": "Vedic Age", "difficulty": "medium", "sort_order": 2, "concepts": ["Rig Vedic", "Later Vedic", "Society", "Religion"], "subtopics": ["Early Vedic", "Later Vedic Period"]},
                        "mahajanapadas": {"display_name": "Mahajanapadas", "difficulty": "medium", "sort_order": 3, "concepts": ["16 Mahajanapadas", "Republics", "Monarchies"], "subtopics": []},
                        "mauryan_empire": {"display_name": "Mauryan Empire", "difficulty": "medium", "sort_order": 4, "concepts": ["Chandragupta", "Ashoka", "Administration", "Art & Architecture"], "subtopics": ["Chanakya", "Dhamma", "Edicts"]},
                        "gupta_period": {"display_name": "Gupta Period", "difficulty": "medium", "sort_order": 5, "concepts": ["Golden Age", "Administration", "Literature", "Science"], "subtopics": ["Chandragupta I", "Samudragupta", "Chandragupta II"]},
                    }
                },
                "medieval_history": {
                    "display_name": "Medieval History",
                    "sort_order": 2,
                    "topics": {
                        "delhi_sultanate": {"display_name": "Delhi Sultanate", "difficulty": "medium", "sort_order": 1, "concepts": ["Slave Dynasty", "Khilji", "Tughlaq", "Sayyid", "Lodhi"], "subtopics": ["Administration", "Economy", "Architecture"]},
                        "mughal_empire": {"display_name": "Mughal Empire", "difficulty": "medium", "sort_order": 2, "concepts": ["Babur", "Akbar", "Administration", "Culture"], "subtopics": ["Mansabdari", "Din-i-Ilahi", "Decline"]},
                        "bhakti_movement": {"display_name": "Bhakti Movement", "difficulty": "easy", "sort_order": 3, "concepts": ["Alvars", "Nayanars", "Sufism", "Sant Tradition"], "subtopics": ["Ramanuja", "Kabir", "Guru Nanak"]},
                    }
                },
                "modern_history": {
                    "display_name": "Modern History",
                    "sort_order": 3,
                    "topics": {
                        "british_expansion": {"display_name": "British Expansion", "difficulty": "medium", "sort_order": 1, "concepts": ["Battle of Plassey", "Subsidiary Alliance", "Doctrine of Lapse"], "subtopics": ["Carnatic Wars", "Anglo-Mysore", "Anglo-Maratha"]},
                        "revolt_1857": {"display_name": "Revolt of 1857", "difficulty": "medium", "sort_order": 2, "concepts": ["Causes", "Spread", "Leadership", "Consequences"], "subtopics": ["Mangal Pandey", "Jhansi Ki Rani", "Bahadur Shah"]},
                        "national_movement": {"display_name": "National Movement", "difficulty": "hard", "sort_order": 3, "concepts": ["INC", "Moderates", "Extremists", "Gandhian Era"], "subtopics": ["Non-Cooperation", "Civil Disobedience", "Quit India"]},
                        "constitutional_dev": {"display_name": "Constitutional Development", "difficulty": "medium", "sort_order": 4, "concepts": ["Regulating Act", "Charter Acts", "Government of India Acts"], "subtopics": ["1909 Act", "1919 Act", "1935 Act"]},
                    }
                },
                "art_culture": {
                    "display_name": "Art & Culture",
                    "sort_order": 4,
                    "topics": {
                        "architecture": {"display_name": "Architecture", "difficulty": "medium", "sort_order": 1, "concepts": ["Temple Architecture", "Indo-Islamic", "Colonial"], "subtopics": ["Nagara", "Dravida", "Vesara"]},
                        "painting": {"display_name": "Painting", "difficulty": "easy", "sort_order": 2, "concepts": ["Mural", "Miniature", "Modern"], "subtopics": ["Ajanta", "Mughal", "Rajput"]},
                        "dance_music": {"display_name": "Dance & Music", "difficulty": "easy", "sort_order": 3, "concepts": ["Classical Dance", "Classical Music", "Folk"], "subtopics": ["Bharatanatyam", "Kathak", "Hindustani"]},
                    }
                },
            }
        },
        "geography": {
            "display_name": "Geography",
            "exam_type": "mains",
            "gs_paper": "GS-1",
            "sort_order": 2,
            "modules": {
                "physical_geography": {
                    "display_name": "Physical Geography",
                    "sort_order": 1,
                    "topics": {
                        "geomorphology": {"display_name": "Geomorphology", "difficulty": "medium", "sort_order": 1, "concepts": ["Earth Structure", "Plate Tectonics", "Landforms"], "subtopics": ["Rocks", "Volcanoes", "Earthquakes"]},
                        "climatology": {"display_name": "Climatology", "difficulty": "medium", "sort_order": 2, "concepts": ["Atmosphere", "Pressure Systems", "Cyclones"], "subtopics": ["Monsoon", "El Nino", "Climate Change"]},
                        "oceanography": {"display_name": "Oceanography", "difficulty": "medium", "sort_order": 3, "concepts": ["Ocean Relief", "Salinity", "Tides", "Currents"], "subtopics": ["Indian Ocean", "Pacific", "Atlantic"]},
                    }
                },
                "indian_geography": {
                    "display_name": "Indian Geography",
                    "sort_order": 2,
                    "topics": {
                        "physiography": {"display_name": "Physiography", "difficulty": "medium", "sort_order": 1, "concepts": ["Himalayas", "Peninsular Plateau", "Plains", "Coasts"], "subtopics": ["Northern Plains", "Thar Desert", "Islands"]},
                        "drainage": {"display_name": "Drainage System", "difficulty": "medium", "sort_order": 2, "concepts": ["Himalayan Rivers", "Peninsular Rivers", "Lakes"], "subtopics": ["Ganga", "Brahmaputra", "Godavari"]},
                        "climate": {"display_name": "Climate of India", "difficulty": "medium", "sort_order": 3, "concepts": ["Monsoon Mechanism", "Seasons", "Distribution"], "subtopics": ["SW Monsoon", "NE Monsoon", "Retreating"]},
                        "soils_vegetation": {"display_name": "Soils & Vegetation", "difficulty": "easy", "sort_order": 4, "concepts": ["Soil Types", "Forest Types", "Conservation"], "subtopics": ["Alluvial", "Black", "Laterite"]},
                    }
                },
                "human_geography": {
                    "display_name": "Human Geography",
                    "sort_order": 3,
                    "topics": {
                        "population": {"display_name": "Population", "difficulty": "medium", "sort_order": 1, "concepts": ["Distribution", "Growth", "Migration"], "subtopics": ["Census", "Demographic Dividend"]},
                        "agriculture": {"display_name": "Agriculture", "difficulty": "medium", "sort_order": 2, "concepts": ["Crops", "Green Revolution", "Food Security"], "subtopics": ["Irrigation", "Fertilizers", "Organic"]},
                        "mineral_resources": {"display_name": "Mineral Resources", "difficulty": "easy", "sort_order": 3, "concepts": ["Metallic", "Non-Metallic", "Energy"], "subtopics": ["Coal", "Petroleum", "Nuclear"]},
                    }
                },
            }
        },
        "polity": {
            "display_name": "Polity",
            "exam_type": "mains",
            "gs_paper": "GS-2",
            "sort_order": 3,
            "modules": {
                "constitution": {
                    "display_name": "Constitution of India",
                    "sort_order": 1,
                    "topics": {
                        "making": {"display_name": "Making of Constitution", "difficulty": "easy", "sort_order": 1, "concepts": ["Constituent Assembly", "Committees", "Sources"], "subtopics": ["Objective Resolution", "Drafting Committee"]},
                        "preamble": {"display_name": "Preamble", "difficulty": "easy", "sort_order": 2, "concepts": ["Sovereign", "Socialist", "Secular", "Democratic", "Republic"], "subtopics": []},
                        "fundamental_rights": {"display_name": "Fundamental Rights", "difficulty": "hard", "sort_order": 3, "concepts": ["Article 12-35", "Right to Equality", "Right to Freedom"], "subtopics": ["Article 14", "Article 19", "Article 21", "Writs"]},
                        "dpsp": {"display_name": "DPSP", "difficulty": "medium", "sort_order": 4, "concepts": ["Article 36-51", "Socialist", "Gandhian", "Liberal"], "subtopics": ["Article 39", "Article 44", "Article 48"]},
                        "fundamental_duties": {"display_name": "Fundamental Duties", "difficulty": "easy", "sort_order": 5, "concepts": ["Article 51A", "Sardar Swaran Singh Committee"], "subtopics": []},
                        "amendments": {"display_name": "Amendments", "difficulty": "medium", "sort_order": 6, "concepts": ["42nd", "44th", "73rd", "74th", "101st"], "subtopics": ["Basic Structure", "Landmark Cases"]},
                    }
                },
                "union_executive": {
                    "display_name": "Union Executive",
                    "sort_order": 2,
                    "topics": {
                        "president": {"display_name": "President", "difficulty": "medium", "sort_order": 1, "concepts": ["Election", "Powers", "Impeachment"], "subtopics": ["Ordinance", "Pardon", "Emergency"]},
                        "pm_council": {"display_name": "PM & Council of Ministers", "difficulty": "medium", "sort_order": 2, "concepts": ["Appointment", "Powers", "Collective Responsibility"], "subtopics": []},
                        "parliament": {"display_name": "Parliament", "difficulty": "medium", "sort_order": 3, "concepts": ["Lok Sabha", "Rajya Sabha", "Legislative Process"], "subtopics": ["Speaker", "Committees", "Budget"]},
                        "judiciary": {"display_name": "Judiciary", "difficulty": "medium", "sort_order": 4, "concepts": ["Supreme Court", "High Courts", "Judicial Review"], "subtopics": ["PIL", "Judicial Activism", "Collegium"]},
                    }
                },
                "federalism": {
                    "display_name": "Federal System",
                    "sort_order": 3,
                    "topics": {
                        "centre_state": {"display_name": "Centre-State Relations", "difficulty": "hard", "sort_order": 1, "concepts": ["Legislative", "Administrative", "Financial"], "subtopics": ["Sarkaria", "Punchhi Commission"]},
                        "local_self_govt": {"display_name": "Local Self Government", "difficulty": "medium", "sort_order": 2, "concepts": ["73rd Amendment", "74th Amendment", "Panchayats", "Municipalities"], "subtopics": ["PESA", "District Planning"]},
                    }
                },
            }
        },
        "economics": {
            "display_name": "Economics",
            "exam_type": "mains",
            "gs_paper": "GS-3",
            "sort_order": 4,
            "modules": {
                "indian_economy": {
                    "display_name": "Indian Economy",
                    "sort_order": 1,
                    "topics": {
                        "planning": {"display_name": "Planning in India", "difficulty": "medium", "sort_order": 1, "concepts": ["Five Year Plans", "NITI Aayog", "Model of Planning"], "subtopics": ["Mahalanobis", "Rolling Plan"]},
                        "economic_reforms": {"display_name": "Economic Reforms 1991", "difficulty": "medium", "sort_order": 2, "concepts": ["Liberalization", "Privatization", "Globalization"], "subtopics": ["LPG Reforms", "FDI", "Disinvestment"]},
                        "agriculture_economy": {"display_name": "Agriculture", "difficulty": "medium", "sort_order": 3, "concepts": ["Land Reforms", "Green Revolution", "Agri Marketing"], "subtopics": ["MSP", "PM-KISAN", "E-NAM"]},
                        "industries": {"display_name": "Industries", "difficulty": "easy", "sort_order": 4, "concepts": ["Industrial Policy", "MSME", "Make in India"], "subtopics": ["SEZ", "Industrial Corridors"]},
                    }
                },
                "banking_finance": {
                    "display_name": "Banking & Finance",
                    "sort_order": 2,
                    "topics": {
                        "rbi": {"display_name": "RBI", "difficulty": "hard", "sort_order": 1, "concepts": ["Monetary Policy", "CRR", "SLR", "Repo Rate"], "subtopics": ["MPC", "Open Market", "Liquidity"]},
                        "banking_system": {"display_name": "Banking System", "difficulty": "medium", "sort_order": 2, "concepts": ["Commercial Banks", "NBFCs", "Payment Banks"], "subtopics": ["PSBs", "NPAs", "Basel Norms"]},
                        "financial_markets": {"display_name": "Financial Markets", "difficulty": "medium", "sort_order": 3, "concepts": ["Capital Market", "Money Market", "SEBI"], "subtopics": ["Stock Exchange", "Mutual Funds"]},
                    }
                },
                "budget_fiscal": {
                    "display_name": "Budget & Fiscal Policy",
                    "sort_order": 3,
                    "topics": {
                        "union_budget": {"display_name": "Union Budget", "difficulty": "medium", "sort_order": 1, "concepts": ["Revenue Budget", "Capital Budget", "Fiscal Deficit"], "subtopics": ["Tax Revenue", "Expenditure"]},
                        "fiscal_policy": {"display_name": "Fiscal Policy", "difficulty": "medium", "sort_order": 2, "concepts": ["FRBM Act", "GST", "Direct/Indirect Tax"], "subtopics": ["Finance Commission", "Tax GDP Ratio"]},
                    }
                },
            }
        },
        "environment": {
            "display_name": "Environment & Ecology",
            "exam_type": "mains",
            "gs_paper": "GS-3",
            "sort_order": 5,
            "modules": {
                "ecology": {
                    "display_name": "Ecology",
                    "sort_order": 1,
                    "topics": {
                        "ecosystem": {"display_name": "Ecosystem", "difficulty": "medium", "sort_order": 1, "concepts": ["Structure", "Function", "Energy Flow", "Nutrient Cycle"], "subtopics": ["Food Chain", "Ecological Pyramids"]},
                        "biodiversity": {"display_name": "Biodiversity", "difficulty": "medium", "sort_order": 2, "concepts": ["Species Diversity", "Genetic Diversity", "Ecosystem Diversity"], "subtopics": ["Hotspots", "National Parks", "Wildlife"]},
                    }
                },
                "environmental_issues": {
                    "display_name": "Environmental Issues",
                    "sort_order": 2,
                    "topics": {
                        "pollution": {"display_name": "Pollution", "difficulty": "easy", "sort_order": 1, "concepts": ["Air", "Water", "Soil", "Noise", "Marine"], "subtopics": ["Air Quality Index", "E-Waste"]},
                        "climate_change": {"display_name": "Climate Change", "difficulty": "hard", "sort_order": 2, "concepts": ["Global Warming", "Ozone Depletion", "UNFCCC", "Paris Agreement"], "subtopics": ["IPCC", "COP", "Carbon Credit"]},
                        "conservation": {"display_name": "Conservation", "difficulty": "medium", "sort_order": 3, "concepts": ["In-Situ", "Ex-Situ", "Project Tiger", "Project Elephant"], "subtopics": ["Biosphere Reserves", "Ramsar Sites"]},
                    }
                },
            }
        },
        "science_tech": {
            "display_name": "Science & Technology",
            "exam_type": "mains",
            "gs_paper": "GS-3",
            "sort_order": 6,
            "modules": {
                "basic_science": {
                    "display_name": "Basic Science",
                    "sort_order": 1,
                    "topics": {
                        "physics": {"display_name": "Physics", "difficulty": "medium", "sort_order": 1, "concepts": ["Nuclear Physics", "Quantum Mechanics", "Relativity"], "subtopics": ["Laser", "Superconductivity"]},
                        "chemistry": {"display_name": "Chemistry", "difficulty": "medium", "sort_order": 2, "concepts": ["Organic", "Inorganic", "Biochemistry", "Nanotechnology"], "subtopics": ["Polymers", "Drugs"]},
                        "biology": {"display_name": "Biology", "difficulty": "medium", "sort_order": 3, "concepts": ["Genetics", "Biotechnology", "Human Body"], "subtopics": ["DNA", "CRISPR", "Vaccines"]},
                    }
                },
                "tech_applications": {
                    "display_name": "Technology Applications",
                    "sort_order": 2,
                    "topics": {
                        "space_tech": {"display_name": "Space Technology", "difficulty": "medium", "sort_order": 1, "concepts": ["ISRO", "Satellites", "Launch Vehicles"], "subtopics": ["GSLV", "PSLV", "Chandrayaan", "Mangalyaan"]},
                        "defence_tech": {"display_name": "Defence Technology", "difficulty": "medium", "sort_order": 2, "concepts": ["Missiles", "Drones", "Cybersecurity"], "subtopics": ["Agni", "Prithvi", "Brahmos"]},
                        "it_computers": {"display_name": "IT & Computers", "difficulty": "easy", "sort_order": 3, "concepts": ["AI", "Blockchain", "Cloud Computing", "IoT"], "subtopics": ["5G", "Quantum Computing"]},
                    }
                },
            }
        },
        "society": {
            "display_name": "Indian Society",
            "exam_type": "mains",
            "gs_paper": "GS-1",
            "sort_order": 7,
            "modules": {
                "social_structure": {
                    "display_name": "Social Structure",
                    "sort_order": 1,
                    "topics": {
                        "caste_system": {"display_name": "Caste System", "difficulty": "medium", "sort_order": 1, "concepts": ["Varna", "Jati", "Changes", "Policies"], "subtopics": ["Mandal Commission", "Reservation"]},
                        "family_marriage": {"display_name": "Family & Marriage", "difficulty": "easy", "sort_order": 2, "concepts": ["Types", "Changes", "Laws"], "subtopics": ["Uniform Civil Code"]},
                        "religion": {"display_name": "Religion in India", "difficulty": "easy", "sort_order": 3, "concepts": ["Communalism", "Secularism", "Pluralism"], "subtopics": ["Temple Entry", "Personal Laws"]},
                    }
                },
                "social_issues": {
                    "display_name": "Social Issues",
                    "sort_order": 2,
                    "topics": {
                        "poverty": {"display_name": "Poverty", "difficulty": "medium", "sort_order": 1, "concepts": ["Measurement", "Causes", "Programs"], "subtopics": ["Multidimensional Poverty", "SDGs"]},
                        "education": {"display_name": "Education", "difficulty": "medium", "sort_order": 2, "concepts": ["NEP 2020", "RTE", "Literacy"], "subtopics": ["Higher Education", "Skill Development"]},
                        "health": {"display_name": "Health", "difficulty": "medium", "sort_order": 3, "concepts": ["Public Health", "Diseases", "Health Infrastructure"], "subtopics": ["Ayushman Bharat", "COVID"]},
                        "women_empowerment": {"display_name": "Women Empowerment", "difficulty": "medium", "sort_order": 4, "concepts": ["Issues", "Laws", "Schemes"], "subtopics": ["Sex Ratio", "Women Reservation"]},
                    }
                },
            }
        },
    }

    async with async_session_factory() as session:
        existing = await session.execute(select(Subject).limit(1))
        if existing.scalar_one_or_none():
            print("Syllabus already seeded — skipping")
            return

        for subj_key, subj_data in SYLLABUS_DATA.items():
            subject = Subject(
                name=subj_key,
                display_name=subj_data["display_name"],
                exam_type=subj_data.get("exam_type", "mains"),
                gs_paper=subj_data.get("gs_paper"),
                sort_order=subj_data.get("sort_order", 0),
            )
            session.add(subject)
            await session.flush()

            for mod_key, mod_data in subj_data.get("modules", {}).items():
                module = Module(
                    subject_id=subject.id,
                    name=mod_key,
                    display_name=mod_data["display_name"],
                    sort_order=mod_data.get("sort_order", 0),
                )
                session.add(module)
                await session.flush()

                for top_key, top_data in mod_data.get("topics", {}).items():
                    topic = Topic(
                        module_id=module.id,
                        name=top_key,
                        display_name=top_data["display_name"],
                        difficulty=top_data.get("difficulty", "medium"),
                        sort_order=top_data.get("sort_order", 0),
                    )
                    session.add(topic)
                    await session.flush()

                    for concept_name in top_data.get("concepts", []):
                        concept = Concept(
                            topic_id=topic.id,
                            name=concept_name.lower().replace(" ", "_"),
                            display_name=concept_name,
                        )
                        session.add(concept)

                    for st_name in top_data.get("subtopics", []):
                        subtopic = Subtopic(
                            topic_id=topic.id,
                            name=st_name.lower().replace(" ", "_"),
                            display_name=st_name,
                        )
                        session.add(subtopic)

        await session.commit()

        counts = {
            "subjects": (await session.execute(select(func.count(Subject.id)))).scalar(),
            "modules": (await session.execute(select(func.count(Module.id)))).scalar(),
            "topics": (await session.execute(select(func.count(Topic.id)))).scalar(),
            "subtopics": (await session.execute(select(func.count(Subtopic.id)))).scalar(),
            "concepts": (await session.execute(select(func.count(Concept.id)))).scalar(),
        }
        print(f"Seeded: {counts}")
        return counts


async def seed_content():
    from app.database.session import async_session_factory
    from app.models.syllabus import Topic
    from app.models.versioning import ContentVersion
    from app.models.answers import ConclusionTemplate
    from app.services.content.lesson_factory import LessonFactory
    from app.services.content.flashcard_factory import FlashcardFactory
    from app.services.content.revision_factory import RevisionFactory
    from app.services.content.answer_factory import AnswerWritingFactory
    from app.services.validation.pipeline import ValidationPipeline
    from sqlalchemy import select, func

    async with async_session_factory() as session:
        topics = (await session.execute(select(Topic))).scalars().all()
        print(f"Generating content for {len(topics)} topics...")

        lesson_factory = LessonFactory(session)
        flashcard_factory = FlashcardFactory(session)
        revision_factory = RevisionFactory(session)
        pipeline = ValidationPipeline(session)

        for topic in topics[:5]:
            lesson_data = LessonFactory.build_lesson_data(
                title=topic.display_name,
                learning_objectives=[f"Understand {topic.display_name}", f"Analyze key concepts"],
                prerequisites=[],
                core_theory=[{"heading": "Introduction", "body": f"Core theory for {topic.display_name}"}],
                examples=[{"title": "Example", "body": "Sample example"}],
                memory_tricks=[f"Mnemonic: {topic.display_name}"],
                mind_map={"central": topic.display_name, "nodes": []},
                common_mistakes=["Common mistake"],
                pyq_references=[],
                revision_notes=[f"Key point about {topic.display_name}"],
                flashcards=[{"front": f"What is {topic.display_name}?", "back": f"{topic.display_name} is...", "card_type": "concept"}],
                summary=f"Summary of {topic.display_name}",
                references=[],
            )
            result = await lesson_factory.create_lesson(
                title=topic.display_name,
                lesson_data=lesson_data,
                syllabus_node_id=topic.id,
                syllabus_node_type="topic",
                source="seed_script",
            )

            content_result = await session.execute(
                select(ContentVersion).where(
                    ContentVersion.content_id == result["content_id"]
                )
            )
            content = content_result.scalar_one_or_none()
            if content:
                await pipeline.validate(content, source="seed_script")

            flashcards = [{"front": f"What is {topic.display_name}?", "back": f"{topic.display_name} refers to...", "card_type": "definition"}]
            await flashcard_factory.bulk_create(
                flashcards=flashcards,
                syllabus_node_id=topic.id,
                syllabus_node_type="topic",
            )

            await revision_factory.create_revision_note(
                note_type="one_page_notes",
                title=f"{topic.display_name} - One Page Notes",
                key_points=[f"Key point about {topic.display_name}"],
                syllabus_node_id=topic.id,
                syllabus_node_type="topic",
            )

        template = ConclusionTemplate(
            title="Balanced Conclusion Template",
            template_text="In conclusion, while there are valid arguments on both sides, a balanced approach that considers ... is essential for sustainable outcomes.",
            category="gs_mains",
            tone="balanced",
            word_count=50,
            tags=["general", "balanced"],
        )
        session.add(template)
        await session.commit()

        lesson_count = (await session.execute(select(func.count(ContentVersion.id)).where(ContentVersion.content_type == "lesson"))).scalar()
        flashcard_count = (await session.execute(select(func.count(ContentVersion.id)).where(ContentVersion.content_type == "flashcard"))).scalar()
        revision_count = (await session.execute(select(func.count(ContentVersion.id)).where(ContentVersion.content_type == "revision_note"))).scalar()
        print(f"Content: {lesson_count} lessons, {flashcard_count} flashcards, {revision_count} revision notes")
        return {"lessons": lesson_count, "flashcards": flashcard_count, "revision_notes": revision_count}


async def seed_books():
    from app.database.session import async_session_factory
    from app.models.syllabus import Subject
    from app.services.ingestion.books import NCERTIngestor, StandardBookIngestor
    from sqlalchemy import select

    async with async_session_factory() as session:
        subject_map = {}
        result = await session.execute(select(Subject))
        for s in result.scalars().all():
            subject_map[s.name.lower()] = s.id

        ncert = NCERTIngestor(session)
        ncert_stats = await ncert.ingest_all(subject_map)
        print(f"NCERT: {ncert_stats}")

        std = StandardBookIngestor(session)
        std_stats = await std.ingest_all(subject_map)
        print(f"Standard: {std_stats}")

        return {"ncert": ncert_stats, "standard": std_stats}


async def seed_pyqs():
    from app.database.session import async_session_factory
    from app.models.syllabus import Subject, Topic
    from app.services.ingestion.pyq_importer import PYQImporter
    from sqlalchemy import select

    async with async_session_factory() as session:
        subject_map = {}
        result = await session.execute(select(Subject))
        for s in result.scalars().all():
            subject_map[s.name.lower()] = s.id

        topic_map = {}
        for subj_name, subj_id in subject_map.items():
            modules_result = await session.execute(
                select(Topic).join(Topic.module).where(
                    Topic.module.has(subject_id=subj_id)
                )
            )
            topics = modules_result.scalars().all()
            topic_map[subj_name] = {t.name: t.id for t in topics}

        importer = PYQImporter(session)
        pyq_stats = await importer.generate_sample_pyqs(subject_map, topic_map)
        signal_stats = await importer.compute_signals()
        print(f"PYQs: {pyq_stats}")
        print(f"Signals: {signal_stats}")
        return {"pyqs": pyq_stats, "signals": signal_stats}


async def main():
    import sys
    from sqlalchemy import func

    phase = sys.argv[1] if len(sys.argv) > 1 else "all"

    if phase in ("all", "syllabus"):
        print("\n=== Phase 1: Syllabus ===")
        from app.models.syllabus import Subject, Module, Topic, Subtopic, Concept
        await seed_syllabus()

    if phase in ("all", "books"):
        print("\n=== Phase 2: Books ===")
        await seed_books()

    if phase in ("all", "pyqs"):
        print("\n=== Phase 3: PYQs ===")
        await seed_pyqs()

    if phase in ("all", "content"):
        print("\n=== Phase 4: Generated Content ===")
        await seed_content()

    print("\n=== Done ===")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
