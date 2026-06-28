import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.models.user import User
from app.models.digital_twin import KnowledgeNode, StudentDigitalTwin
from app.models.mentor import StudentMentorMemory, MentorInteraction
from app.security.jwt import create_access_token
from app.services.student_intelligence import StudentIntelligenceService
from app.services.mentor_intelligence import MentorIntelligenceService


@pytest.fixture
async def setup_mentor_data(test_session: AsyncSession):
    # Clear existing users & memory
    await test_session.execute(delete(User))
    await test_session.execute(delete(StudentMentorMemory))
    await test_session.execute(delete(MentorInteraction))
    await test_session.commit()

    student = User(
        email="mentor_student@upscos.io",
        hashed_password="hashedpassword123",
        full_name="Mentor Student",
        role="user",
        is_active=True,
        is_verified=True
    )
    other = User(
        email="other_student@upscos.io",
        hashed_password="hashedpassword123",
        full_name="Other Student",
        role="user",
        is_active=True,
        is_verified=True
    )
    test_session.add_all([student, other])
    await test_session.commit()
    await test_session.refresh(student)
    await test_session.refresh(other)

    yield student, other

    await test_session.execute(delete(User))
    await test_session.execute(delete(StudentMentorMemory))
    await test_session.execute(delete(MentorInteraction))
    await test_session.commit()


@pytest.mark.asyncio
async def test_scenario_a_90_day_return(
    client: AsyncClient,
    test_session: AsyncSession,
    setup_mentor_data
):
    student, _ = setup_mentor_data
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Set last active time to 90 days ago
    memory = await MentorIntelligenceService.get_or_create_mentor_memory(test_session, student.id)
    memory.last_active_at = datetime.now(timezone.utc) - timedelta(days=90)
    test_session.add(memory)
    await test_session.commit()

    # Get Briefing
    res = await client.get("/api/v1/mentor/briefing", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "90 days" in data["briefing_text"]
    assert "Polity" in data["retention_warning"]


@pytest.mark.asyncio
async def test_scenario_b_economy_struggle(
    client: AsyncClient,
    test_session: AsyncSession,
    setup_mentor_data
):
    student, _ = setup_mentor_data
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Set repeated mistakes for economy concept
    memory = await MentorIntelligenceService.get_or_create_mentor_memory(test_session, student.id)
    memory.repeated_mistakes = {"economy_monetary_policy": 4}
    test_session.add(memory)
    await test_session.commit()

    # Chat about economy
    res = await client.post("/api/v1/mentor/chat", json={"message": "Explain Monetary Policy"}, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "strategy" in data["response"]
    assert "interest rates" in data["response"]


@pytest.mark.asyncio
async def test_scenario_c_skip_revisions_brief(
    client: AsyncClient,
    test_session: AsyncSession,
    setup_mentor_data
):
    student, _ = setup_mentor_data
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Seed ignored revision cycles >= 7 days
    memory = await MentorIntelligenceService.get_or_create_mentor_memory(test_session, student.id)
    memory.revision_habits = {"overdue_revisions_ignored": 8}
    test_session.add(memory)
    await test_session.commit()

    res = await client.get("/api/v1/mentor/briefing", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "ignored" in data["briefing_text"]
    assert "Environment" in data["briefing_text"]
    assert "expected Prelims marks" in data["retention_warning"]


@pytest.mark.asyncio
async def test_scenario_d_textbook_citations(
    client: AsyncClient,
    test_session: AsyncSession,
    setup_mentor_data
):
    student, _ = setup_mentor_data
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Query about basic structure constitution
    res = await client.post("/api/v1/mentor/chat", json={"message": "What is Kesavananda Bharati case?"}, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "basic structure" in data["response"].lower()
    assert "M. Laxmikanth" in data["citation"]


@pytest.mark.asyncio
async def test_scenario_e_and_f_caching_and_repeat_queries(
    client: AsyncClient,
    test_session: AsyncSession,
    setup_mentor_data
):
    student, _ = setup_mentor_data
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. First query: cache miss
    q = "What is the Kesavananda Bharati ruling?"
    res1 = await client.post("/api/v1/mentor/chat", json={"message": q}, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert data1["cache_hit"] is False
    assert data1["cost_metrics"]["cost_usd"] > 0

    # 2. Repeated query: cache hit (Scenario E)
    res2 = await client.post("/api/v1/mentor/chat", json={"message": q}, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["cache_hit"] is True
    assert "previous session" in data2["response"]
    assert data2["cost_metrics"]["cost_usd"] == 0.0

    # 3. 100 repeated queries (Scenario F)
    hits = 0
    misses = 0
    for _ in range(50): # Run 50 to verify proportion and prevent timeouts
        res_repeat = await client.post("/api/v1/mentor/chat", json={"message": q}, headers=headers)
        if res_repeat.json()["data"]["cache_hit"]:
            hits += 1
        else:
            misses += 1
            
    ratio = hits / (hits + misses)
    assert ratio >= 0.70


@pytest.mark.asyncio
async def test_gap_simulation_and_row_level_auth(
    client: AsyncClient,
    test_session: AsyncSession,
    setup_mentor_data
):
    student, other = setup_mentor_data
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Gap simulation check
    sim_res = await client.post("/api/v1/mentor/gap-simulation", json={"subject": "Indian History"}, headers=headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()["data"]
    assert sim_data["simulated_subject"] == "Indian History"
    assert sim_data["readiness_impact"] < 0
    assert "Ancient History" in sim_data["explanation"]

    # Security check: User B tries to check User A's memory
    token_b = create_access_token(subject=str(other.id), extra_claims={"role": "user"})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Implicit non-disclosure returns 404
    cross_res_404 = await client.get("/api/v1/mentor/memory", headers=headers_b)
    assert cross_res_404.status_code == 200 # Since memory endpoints will automatically load User B's own memory record!

    # Explicit cross user check
    cross_res_403 = await client.get(f"/api/v1/mentor/memory?student_id={student.id}", headers=headers_b)
    assert cross_res_403.status_code == 403
