"""Progress model class."""

from collections import deque

from toisto.model.language.concept import Concept

from ..model_types import ConceptId
from .quiz import Quiz, Quizzes
from .retention import Retention
from .topic import Topics


class Progress:
    """Keep track of progress on quizzes."""

    def __init__(self, progress_dict: dict[str, dict[str, str | int]], topics: Topics) -> None:
        self.__progress_dict = {key: Retention.from_dict(value) for key, value in progress_dict.items()}
        self.__topics = topics
        self.__recent_concepts: deque[Concept] = deque(maxlen=2)  # Recent concepts to skip when selecting next quiz
        self.__quizzes_by_concept_id: dict[ConceptId, Quizzes] = {}
        for quiz in self.__topics.quizzes:
            self.__quizzes_by_concept_id.setdefault(quiz.concept.base_concept.concept_id, set()).add(quiz)

    def increase_retention(self, quiz: Quiz) -> None:
        """Increase the retention of the quiz."""
        self.__progress_dict.setdefault(str(quiz), Retention()).increase()

    def reset_retention(self, quiz: Quiz) -> None:
        """Reset the retention of the quiz."""
        self.__progress_dict.setdefault(str(quiz), Retention()).reset()

    def next_quiz(self) -> Quiz | None:
        """Return the next quiz."""
        eligible_quizzes = {quiz for quiz in self.__topics.quizzes if self.__is_eligible(quiz)}
        quizzes_for_concepts_in_progress = {quiz for quiz in eligible_quizzes if self.__has_concept_in_progress(quiz)}
        quizzes_in_progress = {quiz for quiz in quizzes_for_concepts_in_progress if self.__in_progress(quiz)}
        for potential_quizzes in [quizzes_in_progress, quizzes_for_concepts_in_progress, eligible_quizzes]:
            unblocked_quizzes = self.__unblocked_quizzes(potential_quizzes, eligible_quizzes)
            if unblocked_quizzes:
                quiz = self.__sort_by_language_level(unblocked_quizzes)[0]
                self.__recent_concepts.append(Concept.instances[quiz.concept.base_concept.concept_id])
                return quiz
        return None

    def get_retention(self, quiz: Quiz) -> Retention:
        """Return the quiz retention."""
        return self.__progress_dict.get(str(quiz), Retention())

    def __is_eligible(self, quiz: Quiz) -> bool:
        """Return whether the quiz is not silenced and not the current quiz."""
        base_concept = Concept.instances[quiz.concept.base_concept.concept_id]
        return base_concept not in self.__recent_concepts and not self.get_retention(quiz).is_silenced()

    def __has_concept_in_progress(self, quiz: Quiz) -> bool:
        """Return whether the quiz's concept has been presented to the user before."""
        quizzes_for_same_concept = self.__quizzes_by_concept_id[quiz.concept.base_concept.concept_id]
        return any(self.__in_progress(quiz_for_same_concept) for quiz_for_same_concept in quizzes_for_same_concept)

    def __in_progress(self, quiz: Quiz) -> bool:
        """Return whether the quiz has been presented to the user before."""
        return str(quiz) in self.__progress_dict

    def __unblocked_quizzes(self, quizzes: Quizzes, eligible_quizzes: Quizzes) -> Quizzes:
        """Return the quizzes that are not blocked by other quizzes.

        Quiz A is blocked by quiz B if the concept of quiz A is a compound with a root that is quizzed by quiz B.
        """
        return {
            quiz
            for quiz in quizzes
            if not self.__root_concepts_have_quizzes(quiz, eligible_quizzes)
            and not quiz.is_blocked_by(eligible_quizzes)
        }

    def __root_concepts_have_quizzes(self, quiz: Quiz, quizzes: Quizzes) -> bool:
        """Return whether the quiz's concept has root concepts that have quizzes."""
        return any(
            other_quiz
            for concept in quiz.concept.root_concepts(quiz.question_language)
            for other_quiz in self.__quizzes_by_concept_id.get(concept.concept_id, set())
            if other_quiz != quiz and other_quiz in quizzes
        )

    def __sort_by_language_level(self, quizzes: Quizzes) -> list[Quiz]:
        """Sort the quizzes by the language level of the concept."""
        return sorted(quizzes, key=lambda quiz: str(quiz.concept.level))

    def as_dict(self) -> dict[str, dict[str, int | str]]:
        """Return the progress as dict."""
        return {key: value.as_dict() for key, value in self.__progress_dict.items()}
