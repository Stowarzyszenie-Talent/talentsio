from oioioi.scoresreveal.models import ScoreReveal, ScoreRevealConfig, ScoreRevealContestConfig


def get_scores_reveal_config(problem_instance):
    try:
        return problem_instance.scores_reveal_config
    except ScoreRevealConfig.DoesNotExist:
        try:
            return problem_instance.contest.scores_reveal_config
        except ScoreRevealContestConfig.DoesNotExist:
            return None


def has_scores_reveal(problem_instance):
    return bool(get_scores_reveal_config(problem_instance))


def is_revealed(submission):
    try:
        return bool(submission.revealed)
    except ScoreReveal.DoesNotExist:
        return False
