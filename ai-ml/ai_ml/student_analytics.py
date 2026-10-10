# pyrefly: ignore [missing-import]
import numpy as np

class StudentAnalyticsEngine:
    """
    Statistical student cohort and distribution analysis engine.
    Computes percentiles, Z-scores, and performance standard deviations.
    """

    @staticmethod
    def calculate_cohort_stats(scores_list):
        """
        Calculates descriptive statistics for a list of numeric scores.
        """
        if not scores_list:
            return {
                'count': 0,
                'mean': 0.0,
                'median': 0.0,
                'std_dev': 0.0,
                'min': 0.0,
                'max': 0.0,
                'p25': 0.0,
                'p75': 0.0
            }

        arr = np.array(scores_list, dtype=float)
        return {
            'count': int(len(arr)),
            'mean': round(float(np.mean(arr)), 2),
            'median': round(float(np.median(arr)), 2),
            'std_dev': round(float(np.std(arr)), 2),
            'min': round(float(np.min(arr)), 2),
            'max': round(float(np.max(arr)), 2),
            'p25': round(float(np.percentile(arr, 25)), 2),
            'p75': round(float(np.percentile(arr, 75)), 2)
        }

    @staticmethod
    def compute_student_percentile(target_score, all_scores):
        """Calculates relative percentile rank of an individual student."""
        if not all_scores:
            return 50.0
        arr = np.array(all_scores, dtype=float)
        return round(float(np.mean(arr <= target_score) * 100), 1)
