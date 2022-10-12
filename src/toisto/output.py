"""Output for the user."""

from datetime import datetime, timedelta
from .color import grey
from .diff import colored_diff
from .metadata import NAME, VERSION
from .model import QuizProgress


WELCOME = f"""👋 Welcome to {NAME} v{VERSION}!

Practice as many words and phrases as you like, for as long as you like.
Hit Ctrl-C or Ctrl-D to quit.

{grey(f'''{NAME} tracks how many times you correctly translate words and phrases.
When you correctly translate a word or phrase multiple times in a row,
{NAME} will not quiz you on it for a while. The more correct translations
in a row, the longer words and phrases are silenced.''')}
"""

DONE = f"""Very good 👍. You're done for now. Please come back later or try a different deck.
{grey(f'Type `{NAME.lower()} -h` for more information.')}
"""


def format_duration(duration: timedelta) -> str:
    """Format the duration in a human friendly way."""
    if duration.days > 0:
        return f"{duration.days} days"
    if duration.seconds > 1.5 * 3600:  # 1.5 hours
        hours = round(duration.seconds / 3600)
        return f"{hours} hours"
    minutes = round(duration.seconds / 60)
    return f"{minutes} minutes"


def feedback(correct: bool, guess: str, answer: str, quiz_progress: QuizProgress) -> str:
    """Create the user feedback."""
    if correct:
        text = "✅ Correct"
        if quiz_progress.silence_until:
            silence_duration = format_duration(quiz_progress.silence_until - datetime.now())
            text += grey(
                f", {quiz_progress.count} times in a row. I won't quiz you on this one for {silence_duration}."
            )
        else:
            text += "."
    else:
        diff = colored_diff(guess, answer)
        text = f'❌ Incorrect. The correct answer is "{diff}".'
    return text + "\n"
