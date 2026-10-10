import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class StudentRiskPredictor:
    """
    Explainable Risk Classifier using Random Forest and Rule-Based Fallback.
    Demonstration benchmark model trained on normalized multidimensional student indicators.
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=4)
        self.is_trained = False
        self.feature_names = [
            'academic_score',
            'attendance_pct',
            'lms_engagement',
            'placement_score',
            'backlog_count'
        ]

    def train_baseline(self, X=None, y=None):
        """
        Trains on provided features or generates synthetic institutional benchmark samples.
        Labels: 0 = Low Risk, 1 = Medium Risk, 2 = High Risk.
        """
        if X is None or y is None:
            # Generate deterministic synthetic benchmark distribution
            np.random.seed(42)
            n_samples = 200
            
            # Features: academic (30-100), attendance (40-100), lms (20-100), placement (20-100), backlogs (0-4)
            acad = np.random.uniform(40, 95, n_samples)
            att = np.random.uniform(45, 98, n_samples)
            lms = np.random.uniform(30, 95, n_samples)
            plac = np.random.uniform(30, 90, n_samples)
            backlogs = np.random.choice([0, 1, 2, 3], size=n_samples, p=[0.7, 0.18, 0.08, 0.04])

            X = np.column_stack([acad, att, lms, plac, backlogs])
            y = np.zeros(n_samples, dtype=int)

            for i in range(n_samples):
                composite = (acad[i] * 0.35) + (att[i] * 0.25) + (lms[i] * 0.15) + (plac[i] * 0.25) - (backlogs[i] * 12)
                if composite < 52 or att[i] < 60 or backlogs[i] >= 2:
                    y[i] = 2 # High Risk
                elif composite < 72 or att[i] < 75 or backlogs[i] >= 1:
                    y[i] = 1 # Medium Risk
                else:
                    y[i] = 0 # Low Risk

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        return self

    def predict_risk(self, academic_score, attendance_pct, lms_engagement, placement_score, backlog_count=0):
        """
        Predicts risk level with feature importance explanations.
        """
        if not self.is_trained:
            self.train_baseline()

        x = np.array([[academic_score, attendance_pct, lms_engagement, placement_score, backlog_count]])
        x_scaled = self.scaler.transform(x)
        
        pred_idx = int(self.model.predict(x_scaled)[0])
        probs = self.model.predict_proba(x_scaled)[0]
        
        labels = ['Low', 'Medium', 'High']
        risk_label = labels[pred_idx]

        feature_importances = dict(zip(self.feature_names, [round(float(v), 3) for v in self.model.feature_importances_]))

        return {
            'predicted_risk_level': risk_label,
            'confidence': round(float(probs[pred_idx]), 2),
            'class_probabilities': {
                'Low': round(float(probs[0]), 2) if len(probs) > 0 else 0,
                'Medium': round(float(probs[1]), 2) if len(probs) > 1 else 0,
                'High': round(float(probs[2]), 2) if len(probs) > 2 else 0,
            },
            'model_type': 'Scikit-Learn Random Forest Benchmark',
            'feature_importances': feature_importances
        }
