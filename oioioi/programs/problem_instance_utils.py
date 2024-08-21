from django.conf import settings


def get_allowed_languages_dict(problem_instance):
    lang_dict = getattr(settings, 'SUBMITTABLE_EXTENSIONS', {})
    allowed_langs = (
        problem_instance.problem.controller.get_allowed_languages_for_problem(
            problem_instance.problem
        )
    )
    contest_langs = problem_instance.controller.get_allowed_languages()
    return {
        lang: lang_dict[lang]
        for lang in lang_dict
        if lang in allowed_langs and lang in contest_langs
    }


def get_allowed_languages_extensions(problem_instance, langs_dict=None):
    if langs_dict is None:
        langs_dict = get_allowed_languages_dict(problem_instance)
    lang_exts = list(langs_dict.values())
    return [ext for lang in lang_exts for ext in lang]


def get_language_by_extension(problem_instance, ext):
    for lang, extension_list in getattr(settings, 'SUBMITTABLE_EXTENSIONS', {}).items():
        if ext in extension_list:
            return lang
    return None
