class LearningRecommendationEngine:
    """
    Algorithmic knowledge-gap recommender for learning resources.
    """

    @staticmethod
    def rank_study_topics(weak_subjects, current_learning_progress=None):
        """
        Ranks study topics by urgency and prerequisite dependencies.
        """
        ranked = []
        for s in weak_subjects:
            urgency = 'High' if s.get('percentage', 100) < 50.0 or not s.get('is_passed', True) else 'Medium'
            ranked.append({
                'topic': s.get('subject_name'),
                'subject_code': s.get('subject_code'),
                'current_score': s.get('percentage'),
                'urgency': urgency,
                'recommended_focus': f"Focus on foundational problem solving and review previous semester exam papers for {s.get('subject_name')}."
            })

        # Sort High urgency first
        ranked.sort(key=lambda x: (x['urgency'] != 'High', x['current_score']))
        return ranked
