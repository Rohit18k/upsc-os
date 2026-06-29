import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.brain.models import Intent, IntentType


INTENT_PATTERNS: Dict[IntentType, List[str]] = {
    IntentType.LEARN_CONCEPT: [
        r"(what|explain|understand|learn|teach|what is|what are|define|describe|meaning of)",
        r"(concept|topic|subject|chapter|module|syllabus)",
    ],
    IntentType.REVISION: [
        r"(revise|revision|quick|summary|key points|important points|cram|last minute)",
        r"(notes|revision notes|one page|short notes|gist)",
    ],
    IntentType.PYQ_DISCUSSION: [
        r"(pyq|previous year|past paper|question paper|past question|last year)",
        r"(201[3-9]|202[0-9])",
        r"(how.*asked|pattern|weightage|frequency|trend)",
    ],
    IntentType.BOOK_EXPLANATION: [
        r"(book|reference|chapter|page|ncert|laxmikanth|spectrum|shankar|ramesh singh|nitin singhania|goh.*leong|gc leong|india year)",
        r"(explain.*book|from.*book|according to|reference)",
    ],
    IntentType.ANSWER_REVIEW: [
        r"(answer|evaluate|review|mark|grade|feedback|improve|score)",
        r"(my answer|essay|structure|introduction|conclusion)",
    ],
    IntentType.CURRENT_AFFAIRS: [
        r"(current affairs|news|recent|latest|today|this week|this month|budget|scheme|policy|bill|act)",
        r"(202[4-6])",
    ],
    IntentType.MENTOR_COACHING: [
        r"(mentor|coach|guide|advice|strategy|path|plan|roadmap|suggest|recommend)",
        r"(how to|how should|what should|tips)",
    ],
    IntentType.MISSION_HELP: [
        r"(mission|daily plan|today.*plan|weekly|study plan|schedule|task|goal|target)",
        r"(what.*do|what.*study|what.*today|organize|plan)",
    ],
    IntentType.WEAK_AREA: [
        r"(weak|improve|struggle|difficult|hard|challenging|gap|problem area|failing)",
        r"(my weakness|where.*focus|what.*focus|priority)",
    ],
    IntentType.GAP_SIMULATION: [
        r"(gap|simulat|what if|scenario|imagine|suppose|if I)",
        r"(preparation.*gap|coverage|miss)",
    ],
    IntentType.AIR_PREDICTION: [
        r"(my rank|my score|my air|expected rank|rank prediction|percentile|cutoff)",
        r"(air|rank)\s+(prediction|chances|estimate|expected)",
        r"(qualify|clear)\s+(exam|prelims|mains|upsc)",
    ],
}


INTENT_KEYWORDS: Dict[IntentType, List[str]] = {
    IntentType.LEARN_CONCEPT: ["concept", "meaning", "define", "what is", "explain", "learn"],
    IntentType.REVISION: ["revision", "revise", "quick notes", "summary"],
    IntentType.PYQ_DISCUSSION: ["pyq", "previous year", "question", "trend"],
    IntentType.BOOK_EXPLANATION: ["book", "ncert", "chapter", "reference"],
    IntentType.ANSWER_REVIEW: ["answer", "review", "evaluate", "feedback"],
    IntentType.CURRENT_AFFAIRS: ["current affairs", "news", "recent", "budget"],
    IntentType.MENTOR_COACHING: ["mentor", "advice", "strategy", "guide", "suggest"],
    IntentType.MISSION_HELP: ["mission", "plan", "schedule", "today", "task"],
    IntentType.WEAK_AREA: ["weak", "improve", "difficult", "struggle"],
    IntentType.GAP_SIMULATION: ["gap", "simulate", "scenario", "what if"],
    IntentType.AIR_PREDICTION: ["rank", "air", "prediction", "cutoff", "chances"],
    IntentType.GENERAL_CHAT: ["hi", "hello", "thanks", "help", "who", "what can"],
}


class IntentRouter:
    def __init__(self):
        self.patterns = INTENT_PATTERNS
        self.keywords = INTENT_KEYWORDS

    async def detect(self, query: str) -> Intent:
        clean = query.lower().strip()
        scores: Dict[IntentType, float] = {}

        for intent_type, patterns in self.patterns.items():
            score = 0.0
            for i, pattern in enumerate(patterns):
                if re.search(pattern, clean):
                    weight = 1.0 - (i * 0.3)
                    score += weight
            if score > 0:
                scores[intent_type] = score

        for intent_type, kw_list in self.keywords.items():
            if intent_type not in scores:
                match_count = sum(1 for kw in kw_list if kw in clean)
                if match_count >= 2:
                    scores[intent_type] = match_count * 0.4
                elif match_count == 1:
                    scores[intent_type] = 0.3

        if not scores:
            return Intent(
                type=IntentType.CLARIFICATION,
                confidence=0.0,
                raw_query=query,
                sub_intent="No intent detected — needs clarification",
            )

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        if best_score < 0.3:
            return Intent(
                type=IntentType.CLARIFICATION,
                confidence=best_score,
                raw_query=query,
                sub_intent=f"Low confidence ({best_score:.2f}) — needs clarification",
            )

        entities = self._extract_entities(clean, best_type)

        return Intent(
            type=best_type,
            confidence=min(best_score / 2.0, 1.0),
            raw_query=query,
            extracted_entities=entities,
        )

    def _extract_entities(self, clean: str, intent: IntentType) -> Dict[str, Any]:
        entities = {}
        subject_match = re.search(
            r"(history|geography|polity|economics|environment|science|society|art|culture)",
            clean,
        )
        if subject_match:
            entities["subject"] = subject_match.group(1)

        topic_match = re.search(
            r"(constitution|federalism|rights|dpsp|judiciary|parliament|amendment|monsoon|climate|biodiversity|pollution|revolt|movement|mughal|maurya|gupta|vedic|indus|planning|budget|rbi|banking|ecosystem)",
            clean,
        )
        if topic_match:
            entities["topic"] = topic_match.group(1)

        year_match = re.search(r"(201[3-9]|202[0-9])", clean)
        if year_match:
            entities["year"] = year_match.group(1)

        return entities


router = IntentRouter()
