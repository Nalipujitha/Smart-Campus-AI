from datetime import datetime
from backend.extensions import db
from backend.models.placement import PlacementProfile, PracticeQuestion, PracticeAttempt
from backend.models.student import Student

class PlacementService:
    """
    Placement Preparation & Skill Assessment Service.
    Evaluates student practice submissions, tracks readiness index, and generates mock interview feedback.
    """

    @classmethod
    def get_questions(cls, category=None, difficulty=None):
        """Retrieves questions filtered by category and difficulty."""
        query = PracticeQuestion.query
        if category:
            query = query.filter_by(category=category)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        return query.all()

    @classmethod
    def submit_practice_answer(cls, student_id, question_id, user_answer):
        """
        Evaluates submitted answer, records attempt, updates category scores, and updates readiness.
        """
        question = PracticeQuestion.query.get(question_id)
        if not question:
            return None, "Question not found."

        # Normalization and scoring
        user_clean = str(user_answer).strip().lower()
        correct_clean = str(question.correct_answer).strip().lower()

        is_correct = (user_clean == correct_clean)
        score_earned = 100.0 if is_correct else 0.0

        feedback = (
            f"Correct! {question.explanation or ''}" if is_correct
            else f"Incorrect. Correct answer was: '{question.correct_answer}'. {question.explanation or ''}"
        )

        attempt = PracticeAttempt(
            student_id=student_id,
            question_id=question_id,
            user_answer=str(user_answer),
            is_correct=is_correct,
            score_earned=score_earned,
            feedback=feedback,
            attempted_at=datetime.utcnow()
        )
        db.session.add(attempt)

        # Update placement profile category averages
        profile = PlacementProfile.query.filter_by(student_id=student_id).first()
        if not profile:
            profile = PlacementProfile(student_id=student_id)
            db.session.add(profile)

        # Recalculate category scores based on all student attempts
        attempts = PracticeAttempt.query.join(PracticeQuestion).filter(PracticeAttempt.student_id == student_id).all()
        cat_scores = {'Aptitude': [], 'Coding': [], 'Communication': [], 'Interview': []}
        for a in attempts:
            cat = a.question.category if a.question else None
            if cat in cat_scores:
                cat_scores[cat].append(a.score_earned)

        if cat_scores['Aptitude']:
            profile.aptitude_score = round(sum(cat_scores['Aptitude']) / len(cat_scores['Aptitude']), 1)
        if cat_scores['Coding']:
            profile.coding_score = round(sum(cat_scores['Coding']) / len(cat_scores['Coding']), 1)
        if cat_scores['Communication']:
            profile.communication_score = round(sum(cat_scores['Communication']) / len(cat_scores['Communication']), 1)
        if cat_scores['Interview']:
            profile.interview_score = round(sum(cat_scores['Interview']) / len(cat_scores['Interview']), 1)

        profile.calculate_readiness()
        db.session.commit()

        # Update composite success score
        from backend.services.success_score import SuccessScoreService
        stu = Student.query.filter_by(student_id=student_id).first()
        if stu:
            SuccessScoreService.calculate_student_score(stu, save_db=True)

        return attempt, None

    @classmethod
    def get_student_placement_summary(cls, student_id):
        """Returns student readiness breakdown, recent attempts, and skill gaps."""
        profile = PlacementProfile.query.filter_by(student_id=student_id).first()
        if not profile:
            profile = PlacementProfile(student_id=student_id)
            profile.calculate_readiness()
            db.session.add(profile)
            db.session.commit()

        attempts = PracticeAttempt.query.filter_by(student_id=student_id).order_by(PracticeAttempt.attempted_at.desc()).limit(15).all()

        return {
            'profile': profile.to_dict(),
            'recent_attempts': [a.to_dict() for a in attempts],
            'readiness_percentage': profile.readiness_percentage,
            'aptitude_score': profile.aptitude_score,
            'coding_score': profile.coding_score,
            'communication_score': profile.communication_score,
            'interview_score': profile.interview_score
        }
