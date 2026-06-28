import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import User
from app.models.digital_twin import KnowledgeNode, StudentDigitalTwin, knowledge_node_dependencies
from app.models.optimization import StudentOptimizationPlan
from app.models.mission import StudentMission
from app.security.jwt import create_access_token
from app.services.student_intelligence import StudentIntelligenceService
from app.services.optimization_engine import OptimizationEngineService
from app.services.mission_engine import MissionEngineService


@pytest.fixture
async def setup_knowledge_graph(test_session: AsyncSession):
    # Clear existing dependency map and nodes
    await test_session.execute(knowledge_node_dependencies.delete())
    await test_session.execute(delete(StudentMission))
    await test_session.execute(delete(StudentOptimizationPlan))
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
    test_session.add(c_preamble)
    await test_session.commit()

    yield

    # Teardown
    await test_session.execute(knowledge_node_dependencies.delete())
    await test_session.execute(delete(StudentMission))
    await test_session.execute(delete(StudentOptimizationPlan))
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
async def test_scenario_a_finish_early(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Recalculate plan and generate mission
    res = await client.post("/api/v1/missions/recalculate", headers=headers)
    assert res.status_code == 200
    mission = res.json()["data"]
    mission_id = mission["id"]

    # Mark mission completed
    comp_res = await client.post(f"/api/v1/missions/{mission_id}/complete", headers=headers)
    assert comp_res.status_code == 200
    comp_mission = comp_res.json()["data"]
    assert comp_mission["status"] == "completed"

    # Scenario A trigger: Student completes tasks early -> Append bonus challenge task
    bonus_res = await client.get("/api/v1/missions/today", headers=headers)
    assert bonus_res.status_code == 200
    # Because today's mission was completed early, add_bonus_tasks is triggered in test scenario manual service call:
    bonus_mission = await MissionEngineService.add_bonus_tasks(test_session, student.id, uuid.UUID(mission_id))
    assert len(bonus_mission.ordered_tasks) > len(comp_mission["ordered_tasks"])
    assert any("Bonus" in t["description"] for t in bonus_mission.ordered_tasks)


@pytest.mark.asyncio
async def test_scenario_b_skip_revisions_recovery(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Generate a revision plan/mission
    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    # Seed overdue revisions
    now = datetime.now(timezone.utc)
    twin.memory_state["items"] = {
        "polity_basics_preamble": {
            "stability": 1.0,
            "repetitions": 1,
            "next_review_at": (now - timedelta(days=5)).isoformat(),
            "last_reviewed_at": (now - timedelta(days=6)).isoformat()
        }
    }
    test_session.add(twin)
    await test_session.commit()

    # Recalculate to generate revision mission
    res = await client.post("/api/v1/missions/recalculate", headers=headers)
    assert res.status_code == 200
    mission = res.json()["data"]
    mission_id = mission["id"]

    # Scenario B trigger: Student skips revision mission -> Skip endpoint called
    skip_res = await client.post(f"/api/v1/missions/{mission_id}/skip", headers=headers)
    assert skip_res.status_code == 200
    skipped_mission = skip_res.json()["data"]
    assert skipped_mission["status"] == "skipped"

    # A recovery mission should now be generated in the history database
    history_res = await client.get("/api/v1/missions/history", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()["data"]
    assert any(m["type"] == "recovery" for m in history)


@pytest.mark.asyncio
async def test_scenario_c_upload_economics_inject(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Recalculate standard mission
    await client.post("/api/v1/missions/recalculate", headers=headers)

    # Scenario C trigger: student uploads a new Economics book. Injects relevant reading tasks
    # We call the service helper directly to simulate document tasks injection
    updated_mission = await MissionEngineService.inject_document_tasks(
        test_session, student.id, ["economy_inflation", "economy_monetary_policy"]
    )
    assert len(updated_mission.ordered_tasks) >= 2
    assert any("economy_inflation" in t["content_reference"] for t in updated_mission.ordered_tasks)


@pytest.mark.asyncio
async def test_scenario_d_exam_in_30_days(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Scenario D trigger: exam is in 30 days -> Shortens missions & revision weight to top
    res = await client.post("/api/v1/missions/recalculate?days_until_exam=30", headers=headers)
    assert res.status_code == 200
    mission = res.json()["data"]
    assert "Revision" in mission["title"]


@pytest.mark.asyncio
async def test_scenarios_e_and_f_difficulty_adaptation(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, _ = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Scenario E: Student improves significantly -> Consistency >= 0.8 & mastery >= 0.8 -> Dial difficulty up to "challenge"
    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    twin.behaviour_state["daily_study_consistency"] = 0.9
    twin.knowledge_state["concept_mastery"] = {"polity_basics_preamble": 0.9}
    test_session.add(twin)
    await test_session.commit()

    res_e = await client.post("/api/v1/missions/recalculate", headers=headers)
    assert res_e.status_code == 200
    mission_e = res_e.json()["data"]
    assert mission_e["difficulty_level"] == "challenge"

    # Scenario F: Student struggles -> Consistency < 0.45 & mastery < 0.45 -> Dial difficulty down to "recovery"
    twin.behaviour_state["daily_study_consistency"] = 0.3
    twin.knowledge_state["concept_mastery"] = {"polity_basics_preamble": 0.3}
    test_session.add(twin)
    await test_session.commit()

    res_f = await client.post("/api/v1/missions/recalculate", headers=headers)
    assert res_f.status_code == 200
    mission_f = res_f.json()["data"]
    assert mission_f["difficulty_level"] == "recovery"


@pytest.mark.asyncio
async def test_security_and_explainability(
    client: AsyncClient,
    test_session: AsyncSession,
    test_users,
    setup_knowledge_graph
):
    student, other = test_users
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/api/v1/missions/recalculate", headers=headers)
    mission_id = res.json()["data"]["id"]

    # 1. Explain mission
    explain_res = await client.get(f"/api/v1/missions/explain/{mission_id}", headers=headers)
    assert explain_res.status_code == 200
    explanation = explain_res.json()["data"]
    assert explanation["mission_id"] == mission_id
    assert "overall_why" in explanation
    assert "task_explanations" in explanation

    # 2. Row-Level Authorization: Request B tries to fetch A's explanation or mission
    token_b = create_access_token(subject=str(other.id), extra_claims={"role": "user"})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Implicit non-disclosure returns 404
    cross_res_404 = await client.get(f"/api/v1/missions/{mission_id}", headers=headers_b)
    assert cross_res_404.status_code == 404

    # Explicit cross-user query returns 403
    cross_res_403 = await client.get(f"/api/v1/missions/{mission_id}?student_id={student.id}", headers=headers_b)
    assert cross_res_403.status_code == 403
