class AdaptiveRecommendationRanker:
    """
    Ranks multi-category student interventions using priority score weighting.
    """

    PRIORITY_MAP = {
        'High': 3,
        'Medium': 2,
        'Low': 1
    }

    CATEGORY_WEIGHTS = {
        'Attendance': 1.2,
        'Academic': 1.1,
        'Placement': 1.0,
        'Skills': 0.9,
        'Learning': 0.8,
        'Career': 0.7
    }

    @classmethod
    def rank_recommendations(cls, recommendations):
        """
        Ranks a list of recommendation objects or dictionaries.
        """
        def score_item(item):
            p = item.get('priority', 'Medium')
            cat = item.get('category', 'Academic')
            p_val = cls.PRIORITY_MAP.get(p, 2)
            c_weight = cls.CATEGORY_WEIGHTS.get(cat, 1.0)
            return p_val * c_weight

        return sorted(recommendations, key=score_item, reverse=True)
