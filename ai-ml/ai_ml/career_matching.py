from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CareerSkillMatcher:
    """
    NLP & Cosine-Similarity Skill Matcher.
    Maps student skill descriptions to target industry role profiles.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def match_skills(self, student_skills_text, role_definitions):
        """
        student_skills_text: e.g. "Python, SQL, Pandas, Machine Learning"
        role_definitions: dict of {role_name: "required skills and description"}
        """
        if not student_skills_text or not role_definitions:
            return []

        roles = list(role_definitions.keys())
        documents = [student_skills_text] + [role_definitions[r] for r in roles]

        tfidf_matrix = self.vectorizer.fit_transform(documents)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

        results = []
        for i, role in enumerate(roles):
            results.append({
                'role': role,
                'similarity_score': round(float(similarities[i]), 3),
                'match_percentage': round(float(similarities[i] * 100), 1)
            })

        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results
