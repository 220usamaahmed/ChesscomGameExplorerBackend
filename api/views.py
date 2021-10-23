from django.http import JsonResponse
from .tasks import generate_game_trees
from celery_progress.views import get_progress


def get_game_trees(request, username):
    task_id = generate_game_trees.delay(username).id
    return JsonResponse({ 'task_id': task_id })


def get_task_progress(request, task_id):
    return get_progress(request, task_id=task_id)