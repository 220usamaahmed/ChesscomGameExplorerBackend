from django.http import HttpResponse
from .tasks import generate_game_trees


def get_game_trees(request, username):

    task = generate_game_trees.delay(username)

    return HttpResponse(f"<a href='http://127.0.0.1:8000/api/progress/{task.id}'>Progress link: {task.id}</a>")
