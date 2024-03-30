from django.urls import path
from . import views
urlpatterns = [
    # path('createinterval/',views.IntervalCreateView.as_view(),name='create_interval'),
    # path('intervallist/',views.IntervalListView.as_view(), name='interval_list'),
    # path('updateinterval/<int:pk>',views.IntervalUpdateView.as_view(),name='update_interval'),
    # path('deleteinterval/<int:pk>',views.IntervalDeleteView.as_view(),name='delete_interval'),
    path('tasklist/',views.TaskListView.as_view(),name='task_list'),
    path('createtask/',views.TaskCreateView.as_view(),name='task_create'),
    path('updatetask/<int:pk>',views.TaskUpdateView.as_view(),name='task_update'),
    path('deletetask/<int:pk>',views.TaskDeleteView.as_view(),name='task_delete'),
    path('posttaskitem/<int:pk>',views.TaskItemPostView.as_view(),name='post_task'),
    path('pendingtaskitems/',views.TaskItemListView.as_view(),name='pending_tasks'),
    path('taskitem/<int:pk>',views.TaskItemView.as_view(),name='task_item'),




    ]