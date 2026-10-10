class PlacementReadinessEvaluator:
    """
    Weighted placement assessment and candidate benchmarking model.
    """

    WEIGHTS = {
        'coding': 0.35,
        'aptitude': 0.25,
        'communication': 0.20,
        'interview': 0.20
    }

    @classmethod
    def evaluate(cls, coding_score, aptitude_score, communication_score, interview_score):
        """
        Calculates composite readiness index (0-100) and identify gap areas.
        """
        composite = (
            (coding_score * cls.WEIGHTS['coding']) +
            (aptitude_score * cls.WEIGHTS['aptitude']) +
            (communication_score * cls.WEIGHTS['communication']) +
            (interview_score * cls.WEIGHTS['interview'])
        )
        composite = round(max(0.0, min(100.0, composite)), 1)

        tier = (
            'Tier 1 (Product & High-Growth Ready)' if composite >= 80.0
            else ('Tier 2 (Core Enterprise Ready)' if composite >= 65.0
            else ('Tier 3 (Developing Readiness)' if composite >= 50.0
            else 'Needs Structured Foundation Training'))
        )

        gaps = []
        if coding_score < 65.0:
            gaps.append('Data Structures & Algorithms problem-solving velocity')
        if aptitude_score < 65.0:
            gaps.append('Quantitative and Logical Reasoning speed drills')
        if communication_score < 70.0:
            gaps.append('Technical articulation and verbal communication clarity')
        if interview_score < 65.0:
            gaps.append('Behavioral and situational STAR-method interview practice')

        return {
            'readiness_score': composite,
            'placement_tier': tier,
            'identified_gaps': gaps,
            'is_job_ready': composite >= 65.0
        }
