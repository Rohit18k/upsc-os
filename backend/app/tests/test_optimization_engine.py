import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import User
from app.models.digital_twin import KnowledgeNode, StudentDigitalTwin, knowledge_node_dependencies
from app.models.optimization import StudentOptimizationPlan
from app.security.jwt import create_access_token
from app.services.student_intelligence import StudentIntelligenceService
from app.services.cognitive_reasoning import CognitiveReasoningService


@pytest.fixture
async def setup_knowledge_graph(test_session: AsyncSession):
    # Clear existing dependency map and nodes
    await test_session.execute(knowledge_node_dependencies.delete())
    await test_session.execute(delete(KnowledgeNode))
    await test_session.commit()

    # Seed Economy Nodes
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

    c_rbi = KnowledgeNode(
        code="economy_rbi",
        title="Reserve Bank of India (RBI)",
        type="concept",
        subject="Economy",
        parent_id=economy_inflation.id
    )
    c_monetary = KnowledgeNode(
        code="economy_monetary_policy",
        title="Monetary Policy",
        type="concept",
        subject="Economy",
        parent_id=economy_inflation.id
    )
    
    # Monetary Policy depends on RBI
    c_monetary.prerequisites.append(c_rbi)
    test_session.add_all([c_rbi, c_monetary])
    await test_session.commit()

    # Seed Polity Nodes
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
        title="Preamble",
        type="concept",
        subject="Polity",
        parent_id=polity_basics.id
    )
    c_fr = KnowledgeNode(
        code="polity_basics_fr",
        title="Fundamental Rights",
        type="concept",
        subject="Polity",
        parent_id=polity_basics.id
    )
    # Fundamental Rights depends on Preamble
    c_fr.prerequisites.append(c_preamble)
    
    test_session.add_all([c_preamble, c_fr])
    await test_session.commit()

    yield

    # Teardown
    await test_session.execute(knowledge_node_dependencies.delete())
    await test_session.execute(delete(KnowledgeNode))
    await test_session.commit()


@pytest.fixture
async def test_users(test_session: AsyncSession):
    # Clear existing users
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

    # Teardown
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_scenarios_a_and_b_hour_constraints(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Setup twin state: study velocity = 2 concepts/day
    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    twin.learning_profile["learning_velocity"] = 2.0
    # Add some visited nodes
    twin.knowledge_state["coverage"]["visited_concepts"] = ["polity_basics_fr", "economy_monetary_policy"]
    twin.knowledge_state["concept_mastery"] = {"polity_basics_fr": 0.4, "economy_monetary_policy": 0.4}
    test_session.add(twin)
    await test_session.commit()

    # Scenario A: 2 hours/day -> Weekly cap is 14 hours
    res_a = await client.get("/api/v1/optimization/plan?daily_hours=2.0", headers=headers)
    assert res_a.status_code == 200
    plan_a = res_a.json()["data"]
    assert plan_a["estimated_completion_time"] <= 14.0

    # Scenario B: 8 hours/day -> Weekly cap is 56 hours. Produces a more aggressive/longer plan
    res_b = await client.post("/api/v1/optimization/recalculate?daily_hours=8.0", headers=headers)
    assert res_b.status_code == 200
    plan_b = res_b.json()["data"]
    assert plan_b["estimated_completion_time"] > plan_a["estimated_completion_time"]
    assert plan_b["estimated_completion_time"] <= 56.0


@pytest.mark.asyncio
async def test_scenario_c_near_term_exam(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Scenario C: 45 days from exam -> Set days_until_exam=45. Automatically prioritizes Revision
    res = await client.get("/api/v1/optimization/plan?days_until_exam=45", headers=headers)
    assert res.status_code == 200
    plan = res.json()["data"]
    assert plan["goal"] == "Revision"


@pytest.mark.asyncio
async def test_scenario_d_long_term_exam(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Scenario D: 300 days from exam -> Set days_until_exam=300. Automatically prioritizes Foundation Building
    res = await client.get("/api/v1/optimization/plan?days_until_exam=300", headers=headers)
    assert res.status_code == 200
    plan = res.json()["data"]
    assert plan["goal"] == "Foundation Building"


@pytest.mark.asyncio
async def test_scenario_e_subject_imbalance(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    # Weak Economy (0.3) but strong Polity (0.8)
    twin.knowledge_state["topic_mastery"] = {"economy": 0.3, "polity": 0.8}
    twin.knowledge_state["coverage"]["visited_concepts"] = ["economy_monetary_policy", "polity_basics_fr"]
    # RBI is unstudied (<80% mastery)
    twin.knowledge_state["concept_mastery"] = {"economy_monetary_policy": 0.4, "polity_basics_fr": 0.4, "economy_rbi": 0.0}
    test_session.add(twin)
    await test_session.commit()

    res = await client.get("/api/v1/optimization/plan", headers=headers)
    assert res.status_code == 200
    plan = res.json()["data"]
    
    # Prerequisite chain resolution check: Economy prerequisite (economy_rbi) must come first!
    actions = plan["ordered_actions"]
    assert len(actions) > 0
    
    # First action targets economy_rbi (or economy-related concepts) since it's the prerequisite of the weak topic
    first_target = actions[0]["target_node"]
    assert "economy" in first_target


@pytest.mark.asyncio
async def test_scenario_f_missed_revisions(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    # Seed overdue revisions in memory state
    now = datetime.now(timezone.utc)
    twin.memory_state["items"] = {
        "polity_basics_preamble": {
            "stability": 1.0,
            "repetitions": 1,
            "next_review_at": (now - timedelta(days=5)).isoformat(),
            "last_reviewed_at": (now - timedelta(days=6)).isoformat()
        },
        "economy_rbi": {
            "stability": 2.0,
            "repetitions": 2,
            "next_review_at": (now - timedelta(days=4)).isoformat(),
            "last_reviewed_at": (now - timedelta(days=6)).isoformat()
        },
        "economy_monetary_policy": {
            "stability": 1.0,
            "repetitions": 1,
            "next_review_at": (now - timedelta(days=3)).isoformat(),
            "last_reviewed_at": (now - timedelta(days=4)).isoformat()
        }
    }
    twin.memory_readiness = 0.4
    
    test_session.add(twin)
    await test_session.commit()

    # Recalculate plan
    res = await client.post("/api/v1/optimization/recalculate", headers=headers)
    assert res.status_code == 200
    plan = res.json()["data"]
    
    # Plan should be rebalanced pushing Revise topic actions to the top
    actions = plan["ordered_actions"]
    assert len(actions) > 0
    assert actions[0]["category"] == "Revise topic"


@pytest.mark.asyncio
async def test_roi_and_explainability(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, other = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Recalculate plan to persist in database
    res = await client.post("/api/v1/optimization/recalculate", headers=headers)
    assert res.status_code == 200
    plan = res.json()["data"]
    plan_id = plan["id"]

    # 1. ROI endpoint
    roi_res = await client.get("/api/v1/optimization/roi", headers=headers)
    assert roi_res.status_code == 200
    roi_data = roi_res.json()["data"]
    assert len(roi_data) > 0
    # Sorted by ROI descending
    for idx in range(len(roi_data) - 1):
        assert roi_data[idx]["roi"] >= roi_data[idx+1]["roi"]

    # 2. Explain plan by ID
    explain_res = await client.get(f"/api/v1/optimization/explain/{plan_id}", headers=headers)
    assert explain_res.status_code == 200
    explanation = explain_res.json()["data"]
    assert explanation["plan_id"] == plan_id
    assert "ordered_actions" in explanation
    assert "expected_outcomes" in explanation

    # 3. Security row-level authentication check
    token_b = create_access_token(subject=str(other.id), extra_claims={"role": "user"})
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # Implicit non-disclosure returns 404
    cross_res_404 = await client.get(f"/api/v1/optimization/explain/{plan_id}", headers=headers_b)
    assert cross_res_404.status_code == 404

    # Explicit access query returns 403
    cross_res_403 = await client.get(f"/api/v1/optimization/explain/{plan_id}?student_id={student.id}", headers=headers_b)
    assert cross_res_403.status_code == 403
