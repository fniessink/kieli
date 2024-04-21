"""Unit tests for the output."""

from unittest import TestCase

from toisto.model.language import FI, NL
from toisto.model.language.label import Label
from toisto.model.quiz.quiz_factory import create_quizzes
from toisto.persistence.spelling_alternatives import load_spelling_alternatives
from toisto.ui.dictionary import DICTIONARY_URL, linkify
from toisto.ui.style import INSERTED, QUIZ, SECONDARY
from toisto.ui.text import CORRECT, INCORRECT, feedback_correct, feedback_incorrect, feedback_skip, instruction

from ...base import FI_NL, NL_FI, ToistoTestCase


class FeedbackTestCase(ToistoTestCase):
    """Unit tests for the feedback function."""

    def setUp(self) -> None:
        """Override to set up test fixtures."""
        super().setUp()
        load_spelling_alternatives(FI_NL)
        self.guess = Label(FI_NL.target, "terve")

    def test_correct_first_time(self):
        """Test that the correct feedback is given when the user guesses correctly."""
        concept = self.create_concept("hi", dict(nl="hoi", fi="terve"))
        quiz = create_quizzes(NL_FI, concept).by_quiz_type("read").pop()
        feedback_text = feedback_correct(self.guess, quiz, NL_FI)
        self.assertEqual(CORRECT, feedback_text)

    def test_show_colloquial_language(self):
        """Test that the colloquial language, that is only spoken, is shown."""
        concept = self.create_concept("thanks", dict(nl="dank", fi=["kiitos", "kiitti*"]))
        colloquial = f'[{SECONDARY}]The colloquial Finnish spoken was "kiitti".[/{SECONDARY}]\n'
        meaning = f'[{SECONDARY}]Meaning "{linkify("dank")}".[/{SECONDARY}]\n'
        answer = f'The correct answer is "[{INSERTED}]{linkify("kiitos")}[/{INSERTED}]".\n'
        expected_feedback_correct = CORRECT + colloquial + meaning
        expected_feedback_incorrect = INCORRECT + answer + colloquial + meaning
        expected_feedback_on_skip = f'The correct answer is "{linkify("kiitos")}".\n' + colloquial + meaning
        for quiz in create_quizzes(FI_NL, concept).by_quiz_type("dictate"):
            if quiz.question.is_colloquial:
                self.assertEqual(expected_feedback_correct, feedback_correct(Label(FI, "kiitos"), quiz, FI_NL))
                self.assertEqual(expected_feedback_incorrect, feedback_incorrect(Label(FI, "hei"), quiz))
                self.assertEqual(expected_feedback_on_skip, feedback_skip(quiz))

    def test_show_alternative_answer(self):
        """Test that alternative answers are shown."""
        concept = self.create_concept("hi", dict(nl="hoi", fi=["terve", "hei"]))
        quiz = create_quizzes(NL_FI, concept).by_quiz_type("read").pop()
        expected_other_answer = linkify(quiz.other_answers(self.guess)[0])
        expected_text = f'{CORRECT}[{SECONDARY}]Another correct answer is "{expected_other_answer}".[/{SECONDARY}]\n'
        self.assertEqual(expected_text, feedback_correct(self.guess, quiz, NL_FI))

    def test_show_alternative_answers(self):
        """Test that alternative answers are shown."""
        concept = self.create_concept("hi", dict(nl="hoi", fi=["terve", "hei", "hei hei"]))
        quiz = create_quizzes(NL_FI, concept).by_quiz_type("read").pop()
        other_answers = [f'"{linkify(answer)}"' for answer in quiz.other_answers(self.guess)]
        expected_text = f'{CORRECT}[{SECONDARY}]Other correct answers are {", ".join(other_answers)}.[/{SECONDARY}]\n'
        self.assertEqual(expected_text, feedback_correct(self.guess, quiz, NL_FI))

    def test_show_feedback_on_incorrect_guess(self):
        """Test that the correct feedback is given when the user guesses incorrectly."""
        concept = self.create_concept("hi", dict(nl="hoi", fi="terve"))
        quiz = create_quizzes(FI_NL, concept).by_quiz_type("dictate").pop()
        expected_text = (
            f'{INCORRECT}The correct answer is "[{INSERTED}]{linkify("terve")}[/{INSERTED}]".\n'
            f'[{SECONDARY}]Meaning "{linkify("hoi")}".[/{SECONDARY}]\n'
        )
        self.assertEqual(expected_text, feedback_incorrect(Label(FI, "incorrect"), quiz))

    def test_show_alternative_answers_on_incorrect_guess(self):
        """Test that alternative answers are also given when the user guesses incorrectly."""
        concept = self.create_concept("hi", dict(nl="hoi", fi=["terve", "hei"]))
        quiz = create_quizzes(NL_FI, concept).by_quiz_type("read").pop()
        expected_text = (
            f'{INCORRECT}The correct answer is "[{INSERTED}]{linkify("terve")}[/{INSERTED}]".\n'
            f'[{SECONDARY}]Another correct answer is "{linkify("hei")}".[/{SECONDARY}]\n'
        )
        self.assertEqual(expected_text, feedback_incorrect(Label(FI, "incorrect"), quiz))

    def test_do_not_show_generated_alternative_answers_on_incorrect_guess(self):
        """Test that generated alternative answers are not shown when the user guesses incorrectly."""
        concept = self.create_concept("house", dict(nl="het huis", fi=["talo"]))
        quiz = create_quizzes(FI_NL, concept).by_quiz_type("read").pop()
        expected_text = f'{INCORRECT}The correct answer is "[{INSERTED}]{linkify("het huis")}[/{INSERTED}]".\n'
        self.assertEqual(expected_text, feedback_incorrect(Label(NL, "incorrect"), quiz))

    def test_do_not_show_generated_alternative_answers_on_question_mark(self):
        """Test that generated alternative answers are not shown when the user enters a question mark."""
        concept = self.create_concept("house", dict(nl="het huis", fi=["talo"]))
        quiz = create_quizzes(FI_NL, concept).by_quiz_type("read").pop()
        expected_text = f'The correct answer is "{linkify("het huis")}".\n'
        self.assertEqual(expected_text, feedback_skip(quiz))

    def test_show_feedback_on_question_mark(self):
        """Test that the correct feedback is given when the user doesn't know the answer."""
        concept = self.create_concept("hi", dict(nl="hoi", fi="terve"))
        quiz = create_quizzes(FI_NL, concept).by_quiz_type("dictate").pop()
        expected_text = (
            f'The correct answer is "{linkify("terve")}".\n[{SECONDARY}]Meaning "{linkify("hoi")}".[/{SECONDARY}]\n'
        )
        self.assertEqual(expected_text, feedback_skip(quiz))

    def test_show_feedback_on_question_mark_with_multiple_answers(self):
        """Test that the correct feedback is given when the user doesn't know the answer."""
        concept = self.create_concept("hi", dict(nl="hoi", fi=["terve", "hei"]))
        quiz = create_quizzes(NL_FI, concept).by_quiz_type("read").pop()
        expected_text = (
            'The correct answers are "[link=https://en.wiktionary.org/wiki/terve]terve[/link]", '
            '"[link=https://en.wiktionary.org/wiki/hei]hei[/link]".\n'
        )
        self.assertEqual(expected_text, feedback_skip(quiz))

    def test_instruction(self):
        """Test that the quiz instruction is correctly formatted."""
        concept = self.create_concept("hi", dict(nl="hoi", fi="terve"))
        quiz = create_quizzes(FI_NL, concept).by_quiz_type("write").pop()
        self.assertEqual(f"[{QUIZ}]Translate into Finnish:[/{QUIZ}]", instruction(quiz))

    def test_instruction_multiple_quiz_types(self):
        """Test that the quiz instruction is correctly formatted for multiple quiz types."""
        concept = self.create_concept(
            "eat",
            {"first person": dict(nl="ik eet"), "third person": dict(female=dict(nl="zij eet"))},
        )
        quizzes = create_quizzes(NL_FI, concept)
        quiz = quizzes.by_quiz_type("give third person").by_quiz_type("feminize").pop()
        expected_text = f"[{QUIZ}]Give the [underline]third person female[/underline] in Dutch:[/{QUIZ}]"
        self.assertEqual(expected_text, instruction(quiz))

    def test_post_quiz_note(self):
        """Test that the post quiz note is formatted correctly."""
        concept = self.create_concept("hi", dict(nl="hoi;;Hoi is an informal greeting"))
        quiz = create_quizzes(NL_FI, concept).by_quiz_type("dictate").pop()
        self.assertEqual(
            f"[{SECONDARY}]Note: Hoi is an informal greeting.[/{SECONDARY}]",
            feedback_correct(Label(NL, "hoi"), quiz, NL_FI).split("\n")[-2],
        )

    def test_multiple_post_quiz_notes(self):
        """Test that multiple post quiz notes are formatted correctly."""
        concept = self.create_concept("hi", dict(fi="moi;;Moi is an informal greeting;'Moi moi' means goodbye"))
        quiz = create_quizzes(FI_NL, concept).by_quiz_type("dictate").pop()
        self.assertIn(
            f"[{SECONDARY}]Notes:\n- Moi is an informal greeting.\n- 'Moi moi' means goodbye.[/{SECONDARY}]\n",
            feedback_correct(Label(FI, "moi"), quiz, FI_NL),
        )

    def test_post_quiz_note_on_incorrect_answer(self):
        """Test that the post quiz note is formatted correctly."""
        concept = self.create_concept("hi", dict(fi="moi;;Moi is an informal greeting"))
        quiz = create_quizzes(FI_NL, concept).by_quiz_type("dictate").pop()
        self.assertEqual(
            f"[{SECONDARY}]Note: Moi is an informal greeting.[/{SECONDARY}]",
            feedback_incorrect(Label(FI, "toi"), quiz).split("\n")[-2],
        )

    def test_post_quiz_note_on_skip_to_answer(self):
        """Test that the post quiz note is formatted correctly."""
        concept = self.create_concept("hi", dict(fi="moi;;Moi is an informal greeting"))
        quiz = create_quizzes(FI_NL, concept).by_quiz_type("dictate").pop()
        self.assertEqual(
            f"[{SECONDARY}]Note: Moi is an informal greeting.[/{SECONDARY}]",
            feedback_skip(quiz).split("\n")[-2],
        )

    def test_post_quiz_example_with_spelling_alternatives(self):
        """Test that the post quiz example is formatted correctly when the example has spelling alternatives."""
        hi = self.create_concept("hi", dict(nl="hoi", fi="terve", example="hi alice"))
        self.create_concept("hi alice", dict(fi="Moi Alice!|Hei Alice!", nl="Hoi Alice!"))
        quiz = create_quizzes(FI_NL, hi).by_quiz_type("read").pop()
        feedback_text = feedback_correct(Label(NL, "hoi"), quiz, FI_NL)
        self.assertEqual(
            CORRECT + f'[{SECONDARY}]Example: "Moi Alice!" meaning "Hoi Alice!"[/{SECONDARY}]\n',
            feedback_text,
        )

    def test_post_quiz_example_with_write_quiz(self):
        """Test that the post quiz example is in the right language when the quiz type is write."""
        hi = self.create_concept("hi", dict(nl="hoi", fi="terve", example="hi alice"))
        self.create_concept("hi alice", dict(fi="Terve Alice!", nl="Hoi Alice!"))
        quiz = create_quizzes(FI_NL, hi).by_quiz_type("write").pop()
        feedback_text = feedback_correct(self.guess, quiz, FI_NL)
        self.assertEqual(
            CORRECT + f'[{SECONDARY}]Example: "Terve Alice!" meaning "Hoi Alice!"[/{SECONDARY}]\n',
            feedback_text,
        )


class LinkifyTest(TestCase):
    """Unit tests for the linkify method."""

    def test_linkify(self):
        """Test the linkify method."""
        self.assertEqual(f"[link={DICTIONARY_URL}/test]Test[/link]", linkify("Test"))

    def test_linkify_multiple_words(self):
        """Test the linkify method."""
        expected_text = f"[link={DICTIONARY_URL}/test]Test[/link] [link={DICTIONARY_URL}/words]words[/link]"
        self.assertEqual(expected_text, linkify("Test words"))

    def test_punctuation(self):
        """Test that punctuation is not linked."""
        self.assertEqual(f"[link={DICTIONARY_URL}/test]Test[/link].", linkify("Test."))
