from datetime import datetime, timezone
import math
from typing import Dict, Any, List

class MemoryEngine:
    DEFAULT_EF = 2.5
    DEFAULT_STABILITY = 1.0  # day

    @classmethod
    def calculate_recall_probability(cls, last_reviewed_at_str: str, current_time: datetime, stability: float) -> float:
        """
        Calculate recall probability using forgetting curve: R = 2^(-t/S)
        where t is days elapsed, S is stability.
        """
        if not last_reviewed_at_str:
            return 1.0
        
        last_reviewed_at = datetime.fromisoformat(last_reviewed_at_str)
        if last_reviewed_at.tzinfo is None:
            last_reviewed_at = last_reviewed_at.replace(tzinfo=timezone.utc)
            
        elapsed_seconds = (current_time - last_reviewed_at).total_seconds()
        elapsed_days = max(0.0, elapsed_seconds / 86400.0)
        
        # Avoid division by zero
        stability = max(0.1, stability)
        
        # Calculate R
        recall_prob = 2.0 ** (-elapsed_days / stability)
        return max(0.0, min(1.0, recall_prob))

    @classmethod
    def update_spaced_repetition(
        cls,
        rating: int,  # 1 to 5 SM-2 rating
        previous_state: Dict[str, Any],
        current_time: datetime
    ) -> Dict[str, Any]:
        """
        Process SM-2 spaced repetition update for a single item.
        Inputs:
            rating: quality of recall (1 = forgot completely, 5 = perfect recall)
            previous_state: Dict with keys ('stability', 'easiness_factor', 'repetitions')
        Returns:
            Dict containing updated spaced repetition values
        """
        # Load previous parameters or defaults
        stability = previous_state.get("stability", cls.DEFAULT_STABILITY)
        ef = previous_state.get("easiness_factor", cls.DEFAULT_EF)
        repetitions = previous_state.get("repetitions", 0)

        # Standard SM-2 logic
        # rating q: 1 (worst) to 5 (best)
        # Convert rating scale to match SM-2 quality (0 to 5).
        # We will assume incoming rating is 1 to 5. We map 1->1, 2->2, 3->3, 4->4, 5->5.
        q = max(1, min(5, rating))

        if q < 3:
            # Forgotten: reset repetitions, stability
            repetitions = 0
            stability = cls.DEFAULT_STABILITY
        else:
            # Successful recall
            if repetitions == 0:
                stability = 1.0  # 1 day
            elif repetitions == 1:
                stability = 6.0  # 6 days
            else:
                stability = stability * ef
            
            repetitions += 1

        # Adjust Easiness Factor (EF)
        ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ef = max(1.3, ef)

        # Difficulty mapping: 1.0 (hardest) to 0.0 (easiest)
        # Derived from EF where 1.3 is hardest and 2.5+ is easiest
        difficulty = max(0.0, min(1.0, (3.0 - ef) / 1.7))

        # Schedule next review
        # stability is in days
        next_review_seconds = stability * 86400.0
        next_review_at = datetime.fromtimestamp(current_time.timestamp() + next_review_seconds, tz=timezone.utc)

        return {
            "stability": float(stability),
            "easiness_factor": float(ef),
            "difficulty": float(difficulty),
            "repetitions": int(repetitions),
            "last_reviewed_at": current_time.isoformat(),
            "next_review_at": next_review_at.isoformat(),
            "recall_probability": 1.0  # immediately after review, recall probability is 1.0
        }

    @classmethod
    def calculate_overall_retention_score(cls, memory_items: Dict[str, Dict[str, Any]], current_time: datetime) -> float:
        """
        Compute average recall probability across all cards in memory.
        Defaults to 1.0 if empty.
        """
        if not memory_items:
            return 1.0
        
        total_recall = 0.0
        for item in memory_items.values():
            last_rev = item.get("last_reviewed_at")
            stab = item.get("stability", cls.DEFAULT_STABILITY)
            total_recall += cls.calculate_recall_probability(last_rev, current_time, stab)
            
        return total_recall / len(memory_items)
