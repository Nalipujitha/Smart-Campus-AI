# Smart Campus AI/ML & Explainable Analytics Architecture

This subsystem provides explainable analytics, predictive risk benchmarking, semantic skill matching, and adaptive recommendations without reliance on third-party cloud APIs.

## Modules Overview

1. **`risk_model.py` (`StudentRiskPredictor`)**:
   - Uses Scikit-learn's Random Forest Classifier calibrated with standardized multi-dimensional inputs (Academic GPA, Attendance %, LMS engagement %, Placement index, Active backlogs).
   - Produces probability distributions and feature importance weights to guarantee algorithmic transparency for human advisors.

2. **`student_analytics.py` (`StudentAnalyticsEngine`)**:
   - Computes statistical cohort distributions: percentiles, standard deviations, Z-scores, and quartiles across departments.

3. **`career_matching.py` (`CareerSkillMatcher`)**:
   - NLP TF-IDF vectorization and Cosine Similarity calculation to map student competencies against 6 core industry profiles.

4. **`learning_recommendations.py` (`LearningRecommendationEngine`)**:
   - Algorithmic prioritization of academic weaknesses and prerequisite-aligned study suggestions.

5. **`placement_readiness.py` (`PlacementReadinessEvaluator`)**:
   - Multi-metric weighted model (Coding 35%, Aptitude 25%, Communication 20%, Mock Interview 20%) delivering actionable tier classifications and skill gap identification.

6. **`recommendation_engine.py` (`AdaptiveRecommendationRanker`)**:
   - Priority-weighted ranking engine prioritizing urgent attendance and academic intervention workflows.
