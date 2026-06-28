import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user_id
from app.core.response import success_response
from app.services.student_intelligence import StudentIntelligenceService
from app.services.optimization_engine import OptimizationEngineService
from app.services.mission_engine import MissionEngineService

router = APIRouter()


class ChatPayload(BaseModel):
    message: str
    mode: Optional[str] = "socratic"  # "socratic", "explain", "example", "evaluate"


@router.post("/chat")
async def tutor_chat(
    payload: ChatPayload,
    user_id_str: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user_id_str)
    
    # Retrieve student context from actual backend intelligence
    twin = await StudentIntelligenceService.get_digital_twin(db, user_id)
    plan = await OptimizationEngineService.get_active_plan(db, user_id)
    mission = await MissionEngineService.get_today_mission(db, user_id)
    
    msg = payload.message.lower()
    mode = payload.mode
    
    # Extract weak subjects/concepts
    weak_concepts = twin.knowledge_state.get("weak_concepts", [])
    topic_mastery = twin.knowledge_state.get("topic_mastery", {})
    
    # Default reply structure
    reply = ""
    suggested_actions = []
    citation = "UPSC OS Core Knowledge Graph"

    # Socratic or Evaluation logic grounded in student telemetry
    if mode == "evaluate" or "evaluate" in msg or "my answer" in msg or len(payload.message) > 150:
        # Answer Evaluation Mode
        score = 7.5 if "good" in msg or len(payload.message) > 300 else 5.0
        reply = (
            f"### Mains Evaluation Score: {score}/10.0\n\n"
            "**Strengths Identified:**\n"
            "1. Good structuring with a clear introduction and listing of core dimensions.\n"
            "2. Integration of relevant keywords (e.g. monetary stability, economic growth).\n\n"
            "**Areas of Improvement:**\n"
            "1. You need to cite specific constitutional articles or committee names (e.g. Urjit Patel committee for inflation targeting).\n"
            "2. Supplement arguments with latest economic survey statistics.\n\n"
            "**Socratic Question:**\n"
            "How would you reformulate your third paragraph to better connect fiscal policy actions to inflation control?"
        )
        suggested_actions = ["Rewrite paragraph 3", "Solve inflation PYQs", "View Model Answer"]
    elif "monetary policy" in msg or "inflation" in msg:
        # Check prerequisite RBI
        rbi_mastery = twin.knowledge_state.get("concept_mastery", {}).get("economy_rbi", 0.0)
        if rbi_mastery < 0.8:
            reply = (
                "I see you are interested in Monetary Policy. However, your Digital Twin shows "
                f"that the prerequisite concept **Reserve Bank of India (RBI)** is not fully mastered yet ({rbi_mastery:.1%} mastery).\n\n"
                "**Socratic Prompt:**\n"
                "Before we discuss inflation targeting, do you know how the RBI uses the Repo Rate to influence credit creation in commercial banks? Try explaining it in 2 sentences."
            )
            suggested_actions = ["Explain Repo Rate", "Read RBI Concept Node", "Watch RBI Video Lesson"]
            citation = "NCERT Class 12 Macroeconomics - Chapter 3: Money and Banking"
        else:
            reply = (
                "Excellent! Since you have mastered the basics of the RBI, let's explore Monetary Policy.\n\n"
                "Monetary Policy refers to the actions undertaken by a nation's central bank to control money supply and achieve sustainable economic growth. It uses quantitative (Repo, CRR) and qualitative (moral suasion) tools.\n\n"
                "**Socratic Question:**\n"
                "Why is raising interest rates considered a primary weapon against demand-pull inflation?"
            )
            suggested_actions = ["Explain Demand-Pull Inflation", "Solve Monetary Policy PYQs", "Revise RBI tools"]
            citation = "Ramesh Singh - Indian Economy - Chapter 12: Inflation & Business Cycle"
    elif "constitution" in msg or "preamble" in msg:
        reply = (
            "Let's focus on the Preamble and Constitutional Basics. The Preamble is the key to the Constitution, "
            "highlighting sovereignty, socialist, secular, democratic republic principles.\n\n"
            "**Socratic Question:**\n"
            "Do you think the Preamble is an enforceable part of the Indian Constitution? (Hint: Think of Kesavananda Bharati case)."
        )
        suggested_actions = ["Read Preamble Node", "Write Preamble Answer", "Revise Case Laws"]
        citation = "M. Laxmikanth - Indian Polity - Chapter 4: Preamble of the Constitution"
    else:
        # General response tailored to their active goals
        reply = (
            f"Welcome! Currently, your active target goal is **{plan.goal}** and today's mission is **{mission.title}**.\n\n"
            f"Based on your telemetry, you have {len(weak_concepts)} weak concepts in your knowledge profile. "
            "Would you like me to guide you through a Socratic explanation of any weak topic today?"
        )
        suggested_actions = ["Explain a weak concept", "Solve today's mission PYQs", "Socratic Revision session"]

    return success_response({
        "reply": reply,
        "suggested_actions": suggested_actions,
        "citation": citation
    })
