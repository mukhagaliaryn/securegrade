from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q, Prefetch
from django.shortcuts import render, get_object_or_404

from apps.dashboard.student.services.subject import convert_rating_to_five_scale
from core.models import Subject, UserSubject, UserChapter, UserLesson, User, UserTask, UserTheory, UserVideo, \
    UserAnswer, UserSimulator
from core.utils.decorators import role_required


def _convert_rating_10_to_5(value):
    if value is None:
        return 0

    value = float(value)

    if value >= 9:
        return 5
    elif value >= 7:
        return 4
    elif value >= 4:
        return 3
    elif value >= 1:
        return 2
    return 0


def _round_or_zero(value, digits=0):
    if value is None:
        return 0
    return round(float(value), digits)


@login_required
@role_required('teacher')
def teacher_dashboard_view(request):
    user = request.user

    # filters
    user_id = request.GET.get('user', '').strip()
    subject_id = request.GET.get('subject', '').strip()
    user_q = request.GET.get('user_q', '').strip()
    subject_q = request.GET.get('subject_q', '').strip()

    # base queryset
    user_subjects = (
        UserSubject.objects
        .select_related('user', 'subject')
        .filter(user__user_type='student')
        .order_by('-created_at', '-id')
    )

    # select filters
    if user_id:
        user_subjects = user_subjects.filter(user_id=user_id)

    if subject_id:
        user_subjects = user_subjects.filter(subject_id=subject_id)

    # search filters
    if user_q:
        user_subjects = user_subjects.filter(
            Q(user__first_name__icontains=user_q) |
            Q(user__last_name__icontains=user_q) |
            Q(user__username__icontains=user_q)
        )

    if subject_q:
        user_subjects = user_subjects.filter(subject__name__icontains=subject_q)

    # top counts
    total_students_count = User.objects.filter(user_type='student').count()
    enrolled_students_count = (
        UserSubject.objects
        .filter(user__user_type='student')
        .values('user_id')
        .distinct()
        .count()
    )
    subjects_count = Subject.objects.count()

    # overall statistics
    subject_avg = UserSubject.objects.filter(user__user_type='student').aggregate(
        avg_rating=Avg('rating'),
        avg_percentage=Avg('percentage'),
    )
    chapter_avg = UserChapter.objects.filter(user__user_type='student').aggregate(
        avg_rating=Avg('rating'),
        avg_percentage=Avg('percentage'),
    )
    lesson_avg = UserLesson.objects.filter(user__user_type='student').aggregate(
        avg_rating=Avg('rating'),
        avg_percentage=Avg('percentage'),
    )

    subject_rating = _round_or_zero(subject_avg['avg_rating'])
    chapter_rating = _round_or_zero(chapter_avg['avg_rating'])
    lesson_rating = _round_or_zero(lesson_avg['avg_rating'])

    statistics = {
        'subject_rating': subject_rating,
        'subject_rating_5': _convert_rating_10_to_5(subject_rating),
        'subject_percentage': _round_or_zero(subject_avg['avg_percentage'], 2),

        'chapter_rating': chapter_rating,
        'chapter_rating_5': _convert_rating_10_to_5(chapter_rating),
        'chapter_percentage': _round_or_zero(chapter_avg['avg_percentage'], 2),

        'lesson_rating': lesson_rating,
        'lesson_rating_5': _convert_rating_10_to_5(lesson_rating),
        'lesson_percentage': _round_or_zero(lesson_avg['avg_percentage'], 2),
    }

    # filter data
    filter_users = (
        User.objects
        .filter(user_type='student', user_subjects__isnull=False)
        .distinct()
        .order_by('first_name', 'last_name', 'username')
    )

    filter_subjects = (
        Subject.objects
        .filter(user_subjects__isnull=False)
        .distinct()
        .order_by('name')
    )
    for item in user_subjects:
        item.rating_5 = _convert_rating_10_to_5(item.rating)

    context = {
        'generics': {
            'total_students_count': total_students_count,
            'enrolled_students_count': enrolled_students_count,
            'subjects_count': subjects_count,
        },
        'statistics': statistics,
        'user_subjects': user_subjects,
        'filter_users': filter_users,
        'filter_subjects': filter_subjects,
        'filters': {
            'user': user_id,
            'subject': subject_id,
            'user_q': user_q,
            'subject_q': subject_q,
        }
    }
    return render(request, 'app/dashboard/teacher/page.html', context)


# user_subject_detail_view
# ----------------------------------------------------------------------------------------------------------------------
@login_required
@role_required('teacher')
def user_subject_detail_view(request, user_subject_id):
    user_subject = get_object_or_404(
        UserSubject.objects.select_related('user', 'subject'),
        pk=user_subject_id,
    )

    user_chapters = list(
        UserChapter.objects
        .filter(user_subject=user_subject)
        .select_related('chapter')
        .order_by('chapter__order', 'id')
    )

    user_lessons = list(
        UserLesson.objects
        .filter(user_subject=user_subject)
        .select_related('lesson', 'lesson__chapter')
        .prefetch_related(
            Prefetch(
                'user_tasks',
                queryset=UserTask.objects.select_related('task').prefetch_related(
                    Prefetch('user_theories', queryset=UserTheory.objects.select_related('theory').all()),
                    Prefetch('user_videos', queryset=UserVideo.objects.select_related('video').all()),
                    Prefetch(
                        'user_options',
                        queryset=UserAnswer.objects.select_related('question').prefetch_related(
                            'options',
                            'question__options',
                        ).order_by('question__order'),
                    ),
                    Prefetch('user_simulators', queryset=UserSimulator.objects.select_related('simulator').all()),
                ).order_by('task__order', 'id'),
            )
        )
        .order_by('lesson__chapter__order', 'lesson__order', 'id')
    )

    lesson_stats = UserLesson.objects.filter(user_subject=user_subject).aggregate(
        avg_rating=Avg('rating'),
        avg_percentage=Avg('percentage'),
    )
    chapter_stats = UserChapter.objects.filter(user_subject=user_subject).aggregate(
        avg_rating=Avg('rating'),
        avg_percentage=Avg('percentage'),
    )

    subject_rating = user_subject.rating or 0
    chapter_rating = _round_or_zero(chapter_stats['avg_rating'])
    lesson_rating = _round_or_zero(lesson_stats['avg_rating'])

    statistics = {
        'subject_rating': subject_rating,
        'subject_rating_5': _convert_rating_10_to_5(subject_rating),
        'subject_percentage': float(user_subject.percentage or 0),

        'chapter_rating': chapter_rating,
        'chapter_rating_5': _convert_rating_10_to_5(chapter_rating),
        'chapter_percentage': _round_or_zero(chapter_stats['avg_percentage'], 2),

        'lesson_rating': lesson_rating,
        'lesson_rating_5': _convert_rating_10_to_5(lesson_rating),
        'lesson_percentage': _round_or_zero(lesson_stats['avg_percentage'], 2),
    }

    chapter_map = {chapter.chapter_id: chapter for chapter in user_chapters}
    chapter_blocks = []

    for user_chapter in user_chapters:
        chapter_lessons = [
            lesson for lesson in user_lessons
            if lesson.lesson.chapter_id == user_chapter.chapter_id
        ]

        lesson_cards = []
        for lesson in chapter_lessons:
            task_tabs = []

            user_tasks = list(lesson.user_tasks.all())
            total_task_count = len(user_tasks)
            completed_task_count = len([t for t in user_tasks if t.is_completed])

            for user_task in user_tasks:
                task_payload = {
                    'id': user_task.id,
                    'task_type': user_task.task.task_type,
                    'task_type_display': user_task.task.get_task_type_display(),
                    'rating': user_task.rating,
                    'max_rating': user_task.task.rating,
                    'percentage': float(user_task.percentage or 0),
                    'is_completed': user_task.is_completed,
                    'theories': [],
                    'videos': [],
                    'questions': [],
                    'simulators': [],
                }

                if user_task.task.task_type == 'theory':
                    task_payload['theories'] = list(user_task.user_theories.all())

                elif user_task.task.task_type == 'video':
                    task_payload['videos'] = list(user_task.user_videos.all())

                elif user_task.task.task_type == 'test':
                    questions_payload = []
                    for ua in user_task.user_options.all():
                        selected_option_ids = set(ua.options.values_list('id', flat=True))
                        question_options = []
                        for option in ua.question.options.all():
                            question_options.append({
                                'id': option.id,
                                'text': option.text,
                                'is_correct': option.is_correct,
                                'is_selected': option.id in selected_option_ids,
                            })

                        questions_payload.append({
                            'id': ua.question.id,
                            'text': ua.question.text,
                            'question_type': ua.question.question_type,
                            'question_type_display': ua.question.get_question_type_display(),
                            'options': question_options,
                        })

                    task_payload['questions'] = questions_payload

                elif user_task.task.task_type == 'simulator':
                    task_payload['simulators'] = list(user_task.user_simulators.all())

                task_tabs.append(task_payload)

            lesson_cards.append({
                'instance': lesson,
                'task_tabs': task_tabs,
                'rating_5': _convert_rating_10_to_5(lesson.rating),
                'task_count': total_task_count,
                'completed_task_count': completed_task_count,
            })

        chapter_blocks.append({
            'instance': user_chapter,
            'lessons': lesson_cards,
            'rating_5': _convert_rating_10_to_5(user_chapter.rating),
            'lesson_count': len(chapter_lessons),
            'completed_lesson_count': len([x for x in chapter_lessons if x.is_completed]),
        })

    context = {
        'user_subject': user_subject,
        'statistics': statistics,
        'chapter_blocks': chapter_blocks,
    }
    return render(
        request,
        'app/dashboard/teacher/user_subject/page.html',
        context
    )
