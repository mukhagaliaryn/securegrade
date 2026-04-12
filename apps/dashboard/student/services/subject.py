from django.contrib import messages
from core.models import Option


# user_lesson_task_view
# ----------------------------------------------------------------------------------------------------------------------
# get_related_data
def get_related_data(user_task):
    task_type = user_task.task.task_type
    data = {}

    if task_type == 'theory':
        data['user_theories'] = user_task.user_theories.select_related('theory').all()

    elif task_type == 'video':
        data['user_videos'] = user_task.user_videos.all()

    elif task_type == 'test':
        data['user_answers'] = user_task.user_options.select_related('question').prefetch_related('options').order_by('question__order')

    elif task_type == 'simulator':
        data['user_simulators'] = user_task.user_simulators.select_related('simulator').all()

    return data


# handle_post_request
def handle_post_request(request, user_task):
    handlers = {
        'theory': handle_theory,
        'video': handle_video,
        'test': handle_test,
        'simulator': handle_simulator,
    }
    handler = handlers.get(user_task.task.task_type)
    if handler:
        return handler(request, user_task)


# ---------------------- THEORY ----------------------
def handle_theory(request, user_task):
    theories = user_task.user_theories.all()

    for ut in theories:
        ut.is_completed = True
        ut.save()

    if theories.exists() and all(ut.is_completed for ut in theories):
        user_task.is_completed = True
        user_task.rating = user_task.task.rating
        user_task.percentage = 100
        user_task.save()
        messages.success(request, 'Теория оқылды')


# ---------------------- VIDEO ----------------------
def handle_video(request, user_task):
    videos = user_task.user_videos.all()
    for uv in videos:
        uv.watched_seconds = int(request.POST.get(f'watched_{uv.id}', 0))
        uv.is_completed = True
        uv.save()

    if all(uv.is_completed for uv in videos):
        user_task.is_completed = True
        user_task.rating = user_task.task.rating
        user_task.save()
        messages.success(request, 'Видеосабақ аяқталды')


# ---------------------- TEST ----------------------
def handle_test(request, user_task):
    questions = [ua.question for ua in user_task.user_options.all()]
    total_questions = len(questions)
    total_score = 0

    for user_answer in user_task.user_options.select_related('question').prefetch_related('question__options'):
        question = user_answer.question
        selected_ids = request.POST.getlist(f'question_{question.id}')
        selected_ids = list(map(int, selected_ids)) if selected_ids else []

        valid_ids = set(question.options.values_list('id', flat=True))
        selected_ids = [opt_id for opt_id in selected_ids if opt_id in valid_ids]

        selected_options = Option.objects.filter(id__in=selected_ids)
        user_answer.options.set(selected_options)

        correct_ids = set(question.options.filter(is_correct=True).values_list('id', flat=True))
        selected_set = set(selected_ids)

        if question.question_type == 'simple':
            # Тек 1 дұрыс таңдау болса ғана дұрыс
            if len(selected_set) == 1 and selected_set.pop() in correct_ids:
                total_score += 1

        elif question.question_type == 'multiple':
            if correct_ids:
                correct_selected = len(selected_set & correct_ids)
                wrong_selected = len(selected_set - correct_ids)

                partial_score = (correct_selected - wrong_selected) / len(correct_ids)
                if partial_score < 0:
                    partial_score = 0

                total_score += partial_score
            else:
                total_score += 0

    full_rating = user_task.task.rating or 1
    if total_questions == 0:
        score = 0
        messages.error(request, 'Тестте сұрақтар жоқ.')
    else:
        ratio = total_score / total_questions
        score = round(full_rating * ratio)

        if ratio == 1:
            messages.success(request, 'Барлық сұраққа дұрыс жауап бердіңіз!')
        elif ratio == 0:
            messages.error(request, 'Барлық жауап қате.')
        else:
            messages.info(
                request,
                f'Ұпай {score} қойылды ({round(ratio*100)}% дұрыс жауап).'
            )

    user_task.rating = score
    user_task.is_completed = True
    user_task.save()


# ---------------------- SIMULATOR ----------------------
def handle_simulator(request, user_task):
    simulators = user_task.user_simulators.all()

    for us in simulators:
        us.is_completed = True
        us.save()

    if simulators.exists() and all(us.is_completed for us in simulators):
        user_task.is_completed = True
        user_task.rating = user_task.task.rating
        user_task.percentage = 100
        user_task.save()
        messages.success(request, 'Симулятор аяқталды')


# convert_rating_to_five_scale
def convert_rating_to_five_scale(rating):
    try:
        rating = float(rating or 0)
    except (TypeError, ValueError):
        return 0

    if rating >= 9:
        return 5
    elif rating >= 7:
        return 4
    elif rating >= 4:
        return 3
    elif rating >= 1:
        return 2
    return 0