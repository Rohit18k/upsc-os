import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import User, UserSession
from app.models.digital_twin import StudentDigitalTwin, KnowledgeNode
from app.models.mentor import StudentMentorMemory, MentorInteraction
from app.models.mission import StudentMission
from app.models.optimization import StudentOptimizationPlan
from app.models.reasoning import StudentDecision


@pytest.fixture(autouse=True)
async def cleanup_e2e_db(test_session: AsyncSession):
    # Wipe database clean before and after E2E runs
    for model in [User, UserSession, StudentDigitalTwin, KnowledgeNode, StudentMentorMemory, MentorInteraction, StudentMission, StudentOptimizationPlan, StudentDecision]:
        await test_session.execute(delete(model))
    await test_session.commit()
    yield
    for model in [User, UserSession, StudentDigitalTwin, KnowledgeNode, StudentMentorMemory, MentorInteraction, StudentMission, StudentOptimizationPlan, StudentDecision]:
        await test_session.execute(delete(model))
    await test_session.commit()


@pytest.mark.asyncio
async def test_e2e_flow_scenario(client: AsyncClient, test_session: AsyncSession):
    # Step 1: Liveness and Readiness check
    res_live = await client.get("/liveness")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    res_ready = await client.get("/readiness")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"

    # Step 2: Register a new student
    email = "e2e_student@upscos.io"
    password = "SecurePassword123!"
    reg_payload = {
        "email": email,
        "password": password,
        "full_name": "E2E Student"
    }
    res_reg = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    reg_data = res_reg.json()
    assert reg_data["user"]["email"] == email

    # Step 3: Login to retrieve access tokens
    login_payload = {
        "email": email,
        "password": password
    }
    res_login = await client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    login_data = res_login.json()
    access_token = login_data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 4: Digital Twin auto-initializes on fetch
    res_twin = await client.get("/api/v1/student/twin", headers=headers)
    assert res_twin.status_code == 200
    twin_data = res_twin.json()
    assert twin_data["knowledge_readiness"] == 0.0

    # Step 5: Send telemetry study event log
    event_payload = {
        "event_type": "lesson_completed",
        "payload": {
            "subject": "Indian Polity",
            "topic_code": "polity_fundamental_rights",
            "concept_code": "polity_equality_before_law",
            "score": 0.85,
            "study_duration": 45
        }
    }
    res_event = await client.post("/api/v1/student/events", json=event_payload, headers=headers)
    assert res_event.status_code == 200


    # Step 6: Trigger Cognitive Diagnosis & Reasoning
    res_diag = await client.get("/api/v1/reasoning/diagnosis", headers=headers)
    assert res_diag.status_code == 200
    diag_data = res_diag.json()["data"]
    assert "root_cause" in diag_data

    # Step 7: Trigger Study Plan Optimization (Recalculate)
    res_opt = await client.post("/api/v1/optimization/recalculate?goal=Prelims&daily_hours=4.5&days_until_exam=90", headers=headers)
    assert res_opt.status_code == 200
    opt_data = res_opt.json()["data"]
    assert opt_data["goal"] == "Prelims"
    assert opt_data["status"] == "active"

    # Step 8: Build and Composition of Missions (Recalculate)
    res_mission = await client.post("/api/v1/missions/recalculate?daily_hours=4.5&days_until_exam=90", headers=headers)
    assert res_mission.status_code == 200
    mission_data = res_mission.json()["data"]
    mission_id = mission_data["id"]

    # Step 9: Complete active mission
    res_comp = await client.post(f"/api/v1/missions/{mission_id}/complete", json={"score": 0.9}, headers=headers)
    assert res_comp.status_code == 200
    assert res_comp.json()["data"]["status"] == "completed"

    # Step 10: Socratic Tutor Chat conversation
    chat_payload = {
        "message": "Explain basic structure doctrine",
        "mode": "socratic"
    }
    res_chat = await client.post("/api/v1/tutor/chat", json=chat_payload, headers=headers)
    assert res_chat.status_code == 200
    assert "reply" in res_chat.json()["data"]

    # Step 11: Call Morning Briefing
    res_brief = await client.get("/api/v1/mentor/briefing", headers=headers)
    assert res_brief.status_code == 200
    assert "briefing_text" in res_brief.json()["data"]

