import math
from typing import Dict, List, Tuple

class MasteryEngine:
    @staticmethod
    def calculate_concept_mastery(
        lesson_completed: bool,
        practice_accuracy: float,  # 0.0 to 1.0
        revision_count: int,
        last_review_days: float,  # days since last review
        confidence: float,  # 0.0 to 1.0, student self-reported confidence
        difficulty: float,  # 0.0 to 1.0, concept difficulty
        memory_stability: float = 15.0  # stability from SM-2, defaults to 15 days if new
    ) -> Tuple[float, Tuple[float, float]]:
        """
        Calculate deterministic concept mastery and its confidence interval.
        Returns:
            (mastery_score, (lower_bound, upper_bound))
        """
        # Base mastery calculation
        lesson_factor = 1.0 if lesson_completed else 0.0
        
        # Weighted formula
        base_mastery = (0.3 * lesson_factor) + (0.5 * practice_accuracy) + (0.2 * confidence)
        
        # Difficulty penalty adjustment (harder concepts require more effort to master)
        # Bounded between 0.9 and 1.1 multiplier
        difficulty_adjustment = 1.0 - 0.1 * (difficulty - 0.5)
        base_mastery = base_mastery * difficulty_adjustment
        
        # Decay mastery based on memory retention (forgetting curve)
        # Using recall probability from memory model: P_recall = 2^(-t/S)
        decay_factor = 2.0 ** (-last_review_days / max(memory_stability, 1.0))
        
        mastery = base_mastery * decay_factor
        mastery = max(0.0, min(1.0, mastery))
        
        # Confidence interval calculation (based on interactions count N)
        # More revisions/practice questions -> higher confidence, smaller interval
        interaction_count = lesson_factor + revision_count + (10 if practice_accuracy > 0 else 0)
        
        # Standard error narrows with interaction count
        se = 0.5 / math.sqrt(interaction_count + 1)
        margin = 1.96 * se
        
        lower_bound = max(0.0, mastery - margin)
        upper_bound = min(1.0, mastery + margin)
        
        return mastery, (lower_bound, upper_bound)

    @staticmethod
    def calculate_parent_mastery(child_masteries: List[float]) -> float:
        """
        Compute topic/subject/overall mastery as average of child masteries.
        """
        if not child_masteries:
            return 0.0
        return sum(child_masteries) / len(child_masteries)
