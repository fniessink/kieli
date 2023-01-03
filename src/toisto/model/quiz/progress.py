"""Progress model class."""

import itertools
import random

from ..model_types import equal_or_prefix

from .quiz import easiest_quizzes, Quiz, Quizzes
from .retention import Retention
from .topic import Topics, Topic


class Progress:
    """Keep track of progress on quizzes."""
    def __init__(self, progress_dict: dict[str, dict[str, str | int]]) -> None:
        self.__progress_dict = {key: Retention.from_dict(value) for key, value in progress_dict.items()}
        self.__current_quiz: Quiz | None = None

    def update(self, quiz: Quiz, correct: bool) -> None:
        """Update the progress on the quiz."""
        self.__progress_dict.setdefault(str(quiz), Retention()).update(correct)

    def get_retention(self, quiz: Quiz) -> Retention:
        """Return the quiz retention."""
        return self.__progress_dict.get(str(quiz), Retention())

    def next_quiz(self, topics: Topics) -> Quiz | None:
        """Return the next quiz."""
        all_quizzes = set(itertools.chain(*[topic.quizzes for topic in topics]))
        for must_have_progress in (True, False):
            for topic in topics:
                if quizzes := self.__eligible_quizzes(topic, all_quizzes, must_have_progress):
                    self.__current_quiz = random.choice(list(quizzes))
                    return self.__current_quiz
        self.__current_quiz = None
        return None

    def __eligible_quizzes(self, topic: Topic, quizzes: Quizzes, must_have_progress: bool) -> Quizzes:
        """Return the eligible next quizzes for the topic if possible."""
        eligible = set(quiz for quiz in quizzes if self.__is_eligible(topic, quiz))
        eligible = set(quiz for quiz in eligible if not self.__used_concepts_have_quizzes(quiz, quizzes))
        eligible_with_progress = set(quiz for quiz in eligible if self.__has_progress(quiz))
        return easiest_quizzes(eligible_with_progress if must_have_progress else eligible_with_progress or eligible)

    def __is_eligible(self, topic: Topic, quiz: Quiz) -> bool:
        """Is the quiz eligible?"""
        return quiz in topic.quizzes and \
            not self.get_retention(quiz).is_silenced() and \
            not quiz.has_same_concept(self.__current_quiz)

    def __has_progress(self, quiz: Quiz) -> bool:
        """Has the quiz been presented to the user before?"""
        return str(quiz) in self.__progress_dict

    def __used_concepts_have_quizzes(self, quiz: Quiz, quizzes: Quizzes) -> bool:
        """Return whether the quiz uses concepts that have quizzes."""
        for each_quiz in quizzes:
            for concept_id in quiz.uses:
                if each_quiz != quiz and equal_or_prefix(each_quiz.concept_id, concept_id):
                    return True
        return False

    def as_dict(self) -> dict[str, dict[str, int | str]]:
        """Return the progress as dict."""
        return {key: value.as_dict() for key, value in self.__progress_dict.items()}
