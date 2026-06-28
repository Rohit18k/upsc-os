import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.digital_twin import KnowledgeNode, StudentDigitalTwin, StudentEventLog, knowledge_node_dependencies
from app.models.reasoning import StudentDecision

from app.security.jwt import create_access_token
from app.services.student_intelligence import StudentIntelligenceService
from app.services.cognitive_reasoning import CognitiveReasoningService

@pytest.fixture
async def setup_knowledge_graph(test_session: AsyncSession):
    from sqlalchemy import delete
    # Clear existing dependency map and nodes at start
    await test_session.execute(knowledge_node_dependencies.delete())
    await test_session.execute(delete(KnowledgeNode))
    await test_session.commit()

    # Seed Economy Subject and nodes for dependency testing
    economy_subject = KnowledgeNode(
        code="economy",
        title="Indian Economy",
        type="subject",
        subject="Economy"
    )
    test_session.add(economy_subject)
    await test_session.commit()
    await test_session.refresh(economy_subject)

    economy_inflation = KnowledgeNode(
        code="economy_inflation",
        title="Inflation",
        type="topic",
        subject="Economy",
        parent_id=economy_subject.id
    )
    test_session.add(economy_inflation)
    await test_session.commit()
    await test_session.refresh(economy_inflation)

    c_monetary = KnowledgeNode(
        code="economy_monetary_policy",
        title="Monetary Policy",
        type="concept",
        subject="Economy",
        parent_id=economy_inflation.id
    )
    c_rbi = KnowledgeNode(
        code="economy_rbi",
        title="Reserve Bank of India (RBI)",
        type="concept",
        subject="Economy",
        parent_id=economy_inflation.id
    )
    # Monetary Policy depends on RBI
    c_monetary.prerequisites.append(c_rbi)

    test_session.add_all([c_monetary, c_rbi])
    await test_session.commit()

    # Seed Polity Subject and nodes
    polity_subject = KnowledgeNode(
        code="polity",
        title="Indian Polity",
        type="subject",
        subject="Polity"
    )
    test_session.add(polity_subject)
    await test_session.commit()
    await test_session.refresh(polity_subject)

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

    c_preamble = KnowledgeNode(
        code="polity_basics_preamble",
        title="Preamble of Constitution",
        type="concept",
        subject="Polity",
        parent_id=polity_basics.id
    )
    test_session.add(c_preamble)
    await test_session.commit()

    yield

    # Teardown database
    await test_session.execute(knowledge_node_dependencies.delete())
    await test_session.execute(delete(KnowledgeNode))
    await test_session.commit()


@pytest.fixture
async def test_users(test_session: AsyncSession):
    from sqlalchemy import delete
    # Clear existing users to avoid email unique constraints at start
    await test_session.execute(delete(User))
    await test_session.commit()

    user_a = User(
        email="student_a@upscos.io",
        hashed_password="hashedpassword123",
        full_name="Student A",
        role="user",
        is_active=True,
        is_verified=True
    )
    user_b = User(
        email="student_b@upscos.io",
        hashed_password="hashedpassword123",
        full_name="Student B",
        role="user",
        is_active=True,
        is_verified=True
    )
    test_session.add_all([user_a, user_b])
    await test_session.commit()
    await test_session.refresh(user_a)
    await test_session.refresh(user_b)
    
    yield user_a, user_b

    # Teardown database
    await test_session.execute(delete(User))
    await test_session.commit()




@pytest.mark.asyncio
async def test_scenario_a_high_knowledge_low_practice(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Initialize twin with High knowledge readiness (e.g. 0.8) and low practice (e.g. 0.2)
    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    twin.knowledge_readiness = 0.8
    twin.practice_readiness = 0.2
    # Seed knowledge state
    twin.knowledge_state["concept_mastery"] = {"polity_basics_preamble": 0.85}
    twin.knowledge_state["coverage"]["visited_concepts"] = ["polity_basics_preamble"]
    twin.knowledge_state["coverage"]["mastered_concepts"] = ["polity_basics_preamble"]
    
    test_session.add(twin)
    await test_session.commit()

    # Call diagnosis endpoint
    res = await client.get("/api/v1/reasoning/diagnosis", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["root_cause"] == "Weak elimination skills"
    assert data["recommended_intervention_type"] == "solve PYQs"
    assert "practice readiness" in data["evidence"]


@pytest.mark.asyncio
async def test_scenario_b_strong_practice_poor_retention(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    twin.knowledge_readiness = 0.6
    twin.practice_readiness = 0.8
    twin.memory_readiness = 0.4
    
    # Overdue revisions in memory
    twin.memory_state["items"] = {
        "polity_basics_preamble": {
            "stability": 2.0,
            "repetitions": 1,
            "next_review_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "last_reviewed_at": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        }
    }
    
    test_session.add(twin)
    await test_session.commit()

    # Call diagnosis endpoint
    res = await client.get("/api/v1/reasoning/diagnosis", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["root_cause"] == "Skipped revisions"
    assert data["recommended_intervention_type"] == "spaced repetition revision"


@pytest.mark.asyncio
async def test_scenario_c_high_mastery_low_readiness(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    twin.knowledge_state["concept_mastery"] = {"polity_basics_preamble": 0.8}
    twin.behaviour_readiness = 0.3
    twin.behaviour_state["daily_study_consistency"] = 0.25
    
    test_session.add(twin)
    await test_session.commit()

    # Call diagnosis endpoint
    res = await client.get("/api/v1/reasoning/diagnosis", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["root_cause"] == "Irregular study schedule"
    assert data["recommended_intervention_type"] == "consistency booster"


@pytest.mark.asyncio
async def test_scenario_d_weak_economy_strong_polity(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    # Weak economy topic mastery (0.3) and strong polity (0.8)
    twin.knowledge_state["topic_mastery"] = {"economy": 0.3, "polity": 0.8}
    
    test_session.add(twin)
    await test_session.commit()

    # Call diagnosis endpoint
    res = await client.get("/api/v1/reasoning/diagnosis", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["root_cause"] == "Missing prerequisite topics"
    assert data["recommended_intervention_type"] == "prerequisite study"


@pytest.mark.asyncio
async def test_bottlenecks_predictions_interventions(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    twin.behaviour_state["daily_study_consistency"] = 0.4
    twin.knowledge_readiness = 0.5
    
    test_session.add(twin)
    await test_session.commit()

    # 1. Bottlenecks
    res = await client.get("/api/v1/reasoning/bottlenecks", headers=headers)
    assert res.status_code == 200
    bottlenecks = res.json()["data"]
    assert len(bottlenecks) > 0
    assert any(b["type"] == "Behaviour issue" for b in bottlenecks)

    # 2. Predictions
    res = await client.get("/api/v1/reasoning/predictions", headers=headers)
    assert res.status_code == 200
    pred = res.json()["data"]
    assert "projection_7_days" in pred
    assert "projection_30_days" in pred
    assert "projection_90_days" in pred
    assert "value" in pred["projection_7_days"]["readiness"]
    assert "lower_bound" in pred["projection_7_days"]["readiness"]
    assert "upper_bound" in pred["projection_7_days"]["readiness"]

    # 3. Interventions / ROI sorting
    res = await client.get("/api/v1/reasoning/interventions", headers=headers)
    assert res.status_code == 200
    interventions = res.json()["data"]
    assert len(interventions) > 0
    # Confirm ROI calculation and sorting
    for i in range(len(interventions) - 1):
        assert interventions[i]["roi"] >= interventions[i+1]["roi"]


@pytest.mark.asyncio
async def test_decisions_and_explainability(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, other = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    twin.knowledge_state["topic_mastery"] = {"economy": 0.3}
    test_session.add(twin)
    await test_session.commit()

    # Get decisions (generates and persists)
    res = await client.get("/api/v1/reasoning/decisions", headers=headers)
    assert res.status_code == 200
    decisions = res.json()["data"]
    assert len(decisions) > 0
    
    decision_id = decisions[0]["id"]

    # Retrieve specific explanation
    explain_res = await client.get(f"/api/v1/reasoning/explain/{decision_id}", headers=headers)
    assert explain_res.status_code == 200
    explanation = explain_res.json()["data"]
    assert explanation["decision_id"] == decision_id
    assert "why" in explanation
    assert "expected_benefit" in explanation

    # Row-Level Authorization check: Request explanation using user B's token
    token_b = create_access_token(subject=str(other.id), extra_claims={"role": "user"})
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # Without student_id, user B gets 404 (non-disclosure of resource existence)
    cross_res_404 = await client.get(f"/api/v1/reasoning/explain/{decision_id}", headers=headers_b)
    assert cross_res_404.status_code == 404

    # With student_id specified, row-level auth checks trigger 403 (cross-user access forbidden)
    cross_res_403 = await client.get(f"/api/v1/reasoning/explain/{decision_id}?student_id={student.id}", headers=headers_b)
    assert cross_res_403.status_code == 403

