import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.models.user import User
from app.models.digital_twin import KnowledgeNode, StudentDigitalTwin
from app.security.jwt import create_access_token
from app.services.student_intelligence import StudentIntelligenceService


@pytest.fixture
async def setup_test_data(test_session: AsyncSession):
    # Clear existing users & nodes
    await test_session.execute(delete(User))
    await test_session.execute(delete(KnowledgeNode))
    await test_session.commit()

    student = User(
        email="student_tutor@upscos.io",
        hashed_password="hashedpassword123",
        full_name="Tutor Student",
        role="user",
        is_active=True,
        is_verified=True
    )
    test_session.add(student)
    await test_session.commit()
    await test_session.refresh(student)

    # Seed Economy Subject and nodes
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
    test_session.add(c_rbi)
    await test_session.commit()

    yield student

    await test_session.execute(delete(User))
    await test_session.execute(delete(KnowledgeNode))
    await test_session.commit()


@pytest.mark.asyncio
async def test_tutor_socratic_rbi_prerequisite(
    client: AsyncClient,
    test_session: AsyncSession,
    setup_test_data
):
    student = setup_test_data
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Setup twin state: unstudied RBI
    twin = await StudentIntelligenceService.get_digital_twin(test_session, student.id)
    twin.knowledge_state["concept_mastery"] = {"economy_rbi": 0.3}
    test_session.add(twin)
    await test_session.commit()

    # Query about monetary policy
    payload = {"message": "Explain Monetary Policy in detail", "mode": "socratic"}
    res = await client.post("/api/v1/tutor/chat", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "RBI" in data["reply"]
    assert "prerequisite" in data["reply"]
    assert len(data["suggested_actions"]) > 0
    assert "citation" in data


@pytest.mark.asyncio
async def test_tutor_evaluate_answer(
    client: AsyncClient,
    test_session: AsyncSession,
    setup_test_data
):
    student = setup_test_data
    token = create_access_token(subject=str(student.id), extra_claims={"role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # Answer evaluation
    payload = {
        "message": "Inflation refers to the general rise in prices. The RBI aims to maintain inflation at 4% with a band of +/- 2%. Repo rate is the primary tool.",
        "mode": "evaluate"
    }
    res = await client.post("/api/v1/tutor/chat", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "Mains Evaluation Score" in data["reply"]
    assert "Socratic Question" in data["reply"]
