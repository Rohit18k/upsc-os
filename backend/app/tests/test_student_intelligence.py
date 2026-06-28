import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.digital_twin import KnowledgeNode, StudentDigitalTwin, StudentEventLog
from app.security.jwt import create_access_token
from app.services.student_intelligence import StudentIntelligenceService
from app.services.mastery_engine import MasteryEngine
from app.services.memory_engine import MemoryEngine

@pytest.mark.asyncio
async def test_student_intelligence_flow(client: AsyncClient, test_session: AsyncSession):
    # 1. Setup/Register a Test User
    user = User(
        email="student@upscos.io",
        hashed_password="hashedpassword123",
        full_name="Test Student",
        role="user",
        is_active=True,
        is_verified=True
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Generate Auth Token
    token = create_access_token(subject=str(user.id), extra_claims={"role": "user"})

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed UPSC Knowledge Graph (Polity)
    # Subject: Polity
    polity_subject = KnowledgeNode(
        code="polity",
        title="Indian Polity",
        type="subject",
        subject="Polity"
    )
    test_session.add(polity_subject)
    await test_session.commit()
    await test_session.refresh(polity_subject)

    # Topic: Basics of Constitution
    polity_basics = KnowledgeNode(
        code="polity_basics",
        title="Basics of Constitution",
        type="topic",
        subject="Polity",
        parent_id=polity_subject.id
    )
    test_session.add(polity_basics)
    await test_session.commit()
    await test_session.refresh(polity_basics)

    # Concept 1: Preamble
    c1 = KnowledgeNode(
        code="polity_basics_preamble",
        title="Preamble of Constitution",
        type="concept",
        subject="Polity",
        parent_id=polity_basics.id
    )
    # Concept 2: Fundamental Rights (Prerequisite: Preamble)
    c2 = KnowledgeNode(
        code="polity_basics_fr",
        title="Fundamental Rights",
        type="concept",
        subject="Polity",
        parent_id=polity_basics.id
    )
    # Concept 3: Directive Principles
    c3 = KnowledgeNode(
        code="polity_basics_dpsp",
        title="Directive Principles (DPSP)",
        type="concept",
        subject="Polity",
        parent_id=polity_basics.id
    )
    # Concept 4: Fundamental Duties
    c4 = KnowledgeNode(
        code="polity_basics_fd",
        title="Fundamental Duties",
        type="concept",
        subject="Polity",
        parent_id=polity_basics.id
    )
    # Concept 5: Amendments
    c5 = KnowledgeNode(
        code="polity_basics_amendment",
        title="Constitutional Amendments",
        type="concept",
        subject="Polity",
        parent_id=polity_basics.id
    )

    # Establish dependency: c2 (Fundamental Rights) depends on c1 (Preamble)
    c2.prerequisites.append(c1)

    test_session.add_all([c1, c2, c3, c4, c5])
    await test_session.commit()


    # Confirm Knowledge Graph counts
    db_concepts = (await test_session.execute(select(KnowledgeNode).where(KnowledgeNode.type == "concept"))).scalars().all()
    assert len(db_concepts) == 5

    # 3. Verify digital twin initialization
    response = await client.get("/api/v1/student/twin", headers=headers)
    assert response.status_code == 200
    twin_data = response.json()
    assert twin_data["user_id"] == str(user.id)
    assert twin_data["knowledge_readiness"] == 0.0
    assert twin_data["memory_readiness"] == 1.0  # default score is 1.0 when empty

    # 4. Scenario Step A: Student Uploads NCERT
    event_payload = {
        "event_type": "DocumentUploaded",
        "payload": {
            "document_id": "doc_ncert_class11_polity",
            "topics": [
                "polity_basics_preamble",
                "polity_basics_fr",
                "polity_basics_dpsp",
                "polity_basics_fd",
                "polity_basics_amendment"
            ]
        }
    }
    response = await client.post("/api/v1/student/events", json=event_payload, headers=headers)
    assert response.status_code == 200
    twin_data = response.json()
    visited = twin_data["knowledge_state"]["coverage"]["visited_concepts"]
    assert len(visited) == 5
    assert twin_data["knowledge_state"]["coverage"]["coverage_percentage"] == 100.0

    # 5. Scenario Step B: Student Studies 5 Lessons
    lessons = [
        {"node_code": "polity_basics_preamble", "confidence": 0.8, "difficulty": 0.3},
        {"node_code": "polity_basics_fr", "confidence": 0.9, "difficulty": 0.6},
        {"node_code": "polity_basics_dpsp", "confidence": 0.7, "difficulty": 0.4},
        {"node_code": "polity_basics_fd", "confidence": 0.8, "difficulty": 0.2},
        {"node_code": "polity_basics_amendment", "confidence": 0.75, "difficulty": 0.5}
    ]

    for lesson in lessons:
        payload = {
            "event_type": "LessonCompleted",
            "payload": {
                "node_code": lesson["node_code"],
                "confidence": lesson["confidence"],
                "difficulty": lesson["difficulty"],
                "time_spent": 600.0,
                "content_type": "text"
            }
        }
        res = await client.post("/api/v1/student/events", json=payload, headers=headers)
        assert res.status_code == 200
    
    # Query updated twin knowledge state
    twin_response = await client.get("/api/v1/student/twin", headers=headers)
    twin_data = twin_response.json()
    
    # Preamble Concept Mastery should be calculated:
    # base = 0.3 * 1.0 (lesson) + 0.5 * 0.0 (practice) + 0.2 * 0.8 (confidence) = 0.46
    # difficulty adjust: 1.0 - 0.1 * (0.3 - 0.5) = 1.02 => mastery = 0.4692
    concept_mastery = twin_data["knowledge_state"]["concept_mastery"]
    assert concept_mastery["polity_basics_preamble"] == pytest.approx(0.4692, abs=1e-3)
    
    # Topic and Subject masteries should propagate
    topic_mastery = twin_data["knowledge_state"]["topic_mastery"]
    assert "polity_basics" in topic_mastery
    assert "polity" in topic_mastery
    assert topic_mastery["polity_basics"] > 0.0

    # Total Session Duration
    assert twin_data["behaviour_state"]["session_duration"] == 3000.0  # 5 * 600

    # 6. Scenario Step C: Student Solves 20 PYQs (80% overall accuracy)
    # 16 correct, 4 incorrect
    # Preamble: 4 correct
    # FR: 4 correct
    # DPSP: 4 correct
    # Duties: 4 correct
    # Amendment: 4 incorrect (e.g. silly errors)
    questions = []
    for node in ["polity_basics_preamble", "polity_basics_fr", "polity_basics_dpsp", "polity_basics_fd"]:
        for _ in range(4):
            questions.append({"node_code": node, "correct": True, "difficulty": 0.4})
    for _ in range(4):
        questions.append({"node_code": "polity_basics_amendment", "correct": False, "difficulty": 0.6, "error_category": "conceptual_gap"})

    pyq_payload = {
        "event_type": "PYQSolved",
        "payload": {
            "questions": questions,
            "time_spent": 1200.0
        }
    }
    response = await client.post("/api/v1/student/events", json=pyq_payload, headers=headers)
    assert response.status_code == 200
    twin_data = response.json()
    
    # Practice accuracy should be exactly 80% (16 / 20 = 0.8)
    assert twin_data["practice_state"]["pyq_accuracy"] == 0.8
    assert twin_data["practice_state"]["error_taxonomy"]["conceptual_gap"] == 4

    # Preamble mastery should now be high:
    # base = 0.3 * 1.0 (lesson) + 0.5 * 1.0 (100% accuracy) + 0.2 * 0.6 (confidence from correct PYQ) = 0.92
    # difficulty adjust: 1.0 - 0.1 * (0.4 - 0.5) = 1.01 => mastery = 0.9292 (>= 0.8, meaning strong/mastered!)
    preamble_mastery = twin_data["knowledge_state"]["concept_mastery"]["polity_basics_preamble"]
    assert preamble_mastery >= 0.8
    assert "polity_basics_preamble" in twin_data["knowledge_state"]["strong_concepts"]
    assert "polity_basics_preamble" in twin_data["knowledge_state"]["coverage"]["mastered_concepts"]

    # Verify locked / unlocked concepts
    cov_details_res = await client.get("/api/v1/student/coverage", headers=headers)
    cov_details = cov_details_res.json()
    # Since Preamble is mastered, Fundamental Rights dependency (preamble) should be met.
    # Therefore, FR is no longer listed in failed dependencies.
    # Amendment, however, has 0.0 mastery and might lock other things if they depend on it.
    # Let's ensure coverage endpoint runs successfully and returns data
    assert cov_details["visited_concepts_count"] == 5

    # 7. Scenario Step D: Student Revises Twice
    # Revision 1 (rating 4)
    rev_payload_1 = {
        "event_type": "RevisionCompleted",
        "payload": {
            "node_code": "polity_basics_preamble",
            "rating": 4,
            "time_spent": 300.0
        }
    }
    response = await client.post("/api/v1/student/events", json=rev_payload_1, headers=headers)
    assert response.status_code == 200
    twin_data = response.json()
    
    # Repetitions should be 1, stability 1 day
    preamble_mem = twin_data["memory_state"]["items"]["polity_basics_preamble"]
    assert preamble_mem["repetitions"] == 1
    assert preamble_mem["stability"] == 1.0

    # Revision 2 (rating 5)
    rev_payload_2 = {
        "event_type": "RevisionCompleted",
        "payload": {
            "node_code": "polity_basics_preamble",
            "rating": 5,
            "time_spent": 200.0
        }
    }
    response = await client.post("/api/v1/student/events", json=rev_payload_2, headers=headers)
    assert response.status_code == 200
    twin_data = response.json()

    # Repetitions should be 2, stability 6 days
    preamble_mem = twin_data["memory_state"]["items"]["polity_basics_preamble"]
    assert preamble_mem["repetitions"] == 2
    assert preamble_mem["stability"] == 6.0
    assert preamble_mem["recall_probability"] == 1.0  # 1.0 immediately after revision

    # 8. Scenario Step E: Student Writes One Answer
    answer_payload = {
        "event_type": "AnswerWritten",
        "payload": {
            "node_code": "polity_basics_preamble",
            "word_count": 250,
            "time_taken": 900.0,
            "evaluation_score": 8.0,
            "max_score": 10.0,
            "self_evaluation": {"clarity": 4, "structure": 4}
        }
    }
    response = await client.post("/api/v1/student/events", json=answer_payload, headers=headers)
    assert response.status_code == 200
    twin_data = response.json()
    assert twin_data["writing_state"]["total_answers"] == 1
    assert twin_data["writing_state"]["writing_quality"] == 0.8
    assert twin_data["writing_readiness"] > 0.0

    # 9. Scenario Step F: Student skips revision for 10 days
    # Calculate recall probability decay after 10 days:
    # stability is 6.0 days, elapsed time is 10 days.
    # R = 2^(-10/6) = 2^(-1.6667) = 0.3149
    recall_prob = MemoryEngine.calculate_recall_probability(
        last_reviewed_at_str=preamble_mem["last_reviewed_at"],
        current_time=datetime.now(timezone.utc) + timedelta(days=10),
        stability=6.0
    )
    assert recall_prob == pytest.approx(0.3149, abs=1e-3)

    # Concept mastery should decay based on decay factor (forgetting curve)
    # Let's verify MasteryEngine handles decay factor correctly
    mastery_decayed, _ = MasteryEngine.calculate_concept_mastery(
        lesson_completed=True,
        practice_accuracy=1.0,
        revision_count=2,
        last_review_days=10.0,
        confidence=0.8,
        difficulty=0.4,
        memory_stability=6.0
    )
    # The decayed mastery is base_mastery * decay_factor
    # base_mastery = (0.3 * 1.0) + (0.5 * 1.0) + (0.2 * 0.8) = 0.96
    # difficulty adjustment = 1.0 - 0.1 * (0.4 - 0.5) = 1.01 => 0.9696
    # decay_factor = 2^(-10/6) = 0.3149
    # mastery_decayed = 0.9696 * 0.3149 = 0.3054
    assert mastery_decayed == pytest.approx(0.3054, abs=1e-3)

    # 10. Query Analytics APIs
    # Knowledge State
    res = await client.get("/api/v1/student/knowledge-state", headers=headers)
    assert res.status_code == 200
    assert "concept_mastery" in res.json()

    # Memory State
    res = await client.get("/api/v1/student/memory-state", headers=headers)
    assert res.status_code == 200
    assert "retention_score" in res.json()

    # Practice State
    res = await client.get("/api/v1/student/practice-state", headers=headers)
    assert res.status_code == 200
    assert "pyq_accuracy" in res.json()

    # Behaviour State
    res = await client.get("/api/v1/student/behaviour-state", headers=headers)
    assert res.status_code == 200
    assert "session_duration" in res.json()

    # Learning Velocity
    res = await client.get("/api/v1/student/learning-velocity", headers=headers)
    assert res.status_code == 200
    assert "learning_profile" in res.json()
    assert "projections" in res.json()

    # Trends
    res = await client.get("/api/v1/student/trends", headers=headers)
    assert res.status_code == 200
    assert "knowledge_readiness" in res.json()
    assert "word_count_trends" in res.json()

    # Security check: another student attempts to query this student's twin without admin access
    other_user = User(
        email="other@upscos.io",
        hashed_password="hashedpassword123",
        full_name="Other Student",
        role="user",
        is_active=True,
        is_verified=True
    )
    test_session.add(other_user)
    await test_session.commit()
    other_token = create_access_token(subject=str(other_user.id), extra_claims={"role": "user"})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # Try to access first student's twin
    bad_res = await client.get(f"/api/v1/student/twin?student_id={user.id}", headers=other_headers)
    assert bad_res.status_code == 403
    assert "Forbidden" in bad_res.json()["title"]
