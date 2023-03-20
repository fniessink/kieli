"""Progress model class."""

from collections import deque

from toisto.model.language import Language
from toisto.model.language.concept import Concept

from .quiz import Quiz, Quizzes
from .retention import Retention
from .topic import Topics

ProgressDict = dict[str, dict[str, str | int]]


class Progress:
    """Keep track of progress on quizzes."""

    def __init__(
        self,
        progress_dict: ProgressDict,
        topics: Topics,
        target_language: Language,
        skip_concepts: int = 5,
    ) -> None:
        self.__progress_dict = {key: Retention.from_dict(value) for key, value in progress_dict.items()}
        self.__topics = topics
        self.target_language = target_language
        self.__recent_concepts: deque[Concept] = deque(maxlen=skip_concepts)
        self.__quizzes_by_concept: dict[Concept, Quizzes] = {}
        for quiz in self.__topics.quizzes:
            self.__quizzes_by_concept.setdefault(quiz.concept.base_concept, set()).add(quiz)

    def increase_retention(self, quiz: Quiz) -> None:
        """Increase the retention of the quiz."""
        self.__progress_dict.setdefault(quiz.key, Retention()).increase()

    def reset_retention(self, quiz: Quiz) -> None:
        """Reset the retention of the quiz."""
        self.__progress_dict.setdefault(quiz.key, Retention()).reset()

    def next_quiz(self) -> Quiz | None:
        """Return the next quiz."""
        eligible_quizzes = {quiz for quiz in self.__topics.quizzes if self.__is_eligible(quiz)}
        quizzes_for_concepts_in_progress = {quiz for quiz in eligible_quizzes if self.__has_concept_in_progress(quiz)}
        quizzes_in_progress = {quiz for quiz in quizzes_for_concepts_in_progress if self.__in_progress(quiz)}
        for potential_quizzes in [quizzes_in_progress, quizzes_for_concepts_in_progress, eligible_quizzes]:
            if unblocked_quizzes := self.__unblocked_quizzes(potential_quizzes, eligible_quizzes):
                quiz = self.__sort_by_language_level(unblocked_quizzes)[0]
                self.__recent_concepts.append(quiz.concept.base_concept)
                return quiz
        return None

    def get_retention(self, quiz: Quiz) -> Retention:
        """Return the quiz retention."""
        return self.__progress_dict.get(quiz.key, Retention())

    def __is_eligible(self, quiz: Quiz) -> bool:
        """Return whether the quiz is not silenced and not the current quiz."""
        return quiz.concept.base_concept not in self.__recent_concepts and not self.get_retention(quiz).is_silenced()

    def __has_concept_in_progress(self, quiz: Quiz) -> bool:
        """Return whether the quiz's concept has been presented to the user before."""
        quizzes_for_same_concept = self.__quizzes_by_concept[quiz.concept.base_concept]
        return any(self.__in_progress(quiz_for_same_concept) for quiz_for_same_concept in quizzes_for_same_concept)

    def __in_progress(self, quiz: Quiz) -> bool:
        """Return whether the quiz has been presented to the user before."""
        return quiz.key in self.__progress_dict

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
        target_language = quiz.answer_language if "write" in quiz.quiz_types else quiz.question_language
        return any(
            other_quiz
            for root in quiz.concept.related_concepts.roots(target_language)
            for other_quiz in self.__quizzes_by_concept.get(root.base_concept, set())
            if other_quiz != quiz and other_quiz in quizzes
        )

    def __sort_by_language_level(self, quizzes: Quizzes) -> list[Quiz]:
        """Sort the quizzes by the language level of the concept."""
        return sorted(quizzes, key=lambda quiz: str(quiz.concept.level))

    def as_dict(self) -> dict[str, dict[str, int | str]]:
        """Return the progress as dict."""
        return {key: value.as_dict() for key, value in self.__progress_dict.items()}
