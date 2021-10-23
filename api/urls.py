from django.urls import path, include
from . import views


app_name = 'api'

urlpatterns = [
    path('get_game_trees/<str:username>', views.get_game_trees, name='get-game-trees'),
    path('progress/', include('celery_progress.urls')),
    path('get_task_progress/<str:task_id>', views.get_task_progress, name='get-progress'),
]