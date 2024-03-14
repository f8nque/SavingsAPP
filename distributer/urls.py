from django.urls import path
from . import views
urlpatterns = [
    path('chart_form',views.ChartRegistrationView.as_view(),name='chart_form'),
    path('chart_list',views.ChartListView.as_view(),name='chart_list'),
    path('chart_update/<int:pk>',views.ChartUpdateView.as_view(),name='chart_update'),
    path('chart_delete/<int:pk>',views.ChartDeleteView.as_view(),name='chart_delete'),
    path('allocate/',views.AllocateEntryView.as_view(),name='allocate'),
    path('allocate_update/<int:pk>',views.AllocateUpdateView.as_view(),name='allocate_update'),
    path('allocate_delete/<int:pk>',views.AllocateDeleteView.as_view(),name='allocate_delete'),
    path('transaction_list/',views.TransactionListView.as_view(),name='transaction_list'),
    path('individual_list/<int:pk>',views.IndividualTransactionView.as_view(),name='individual_list'),
    path('individual_item/<int:pk>',views.IndividualTransactionForm.as_view(),name='individual_item'),
    path('individual_update/<int:pk>',views.IndividualUpdateForm.as_view(),name='individual_update'),
    path('individual_delete/<int:pk>',views.IndividualDeleteView.as_view(),name='individual_delete'),
    path('transfer_list/<int:pk>',views.TransferIndividualListView.as_view(),name='transfer_list'),
    path('transfer_entry/<int:pk>',views.TransferEntryView.as_view(),name='transfer_entry'),
    path('transfer_update/<int:pk>',views.TransferUpdateView.as_view(),name='transfer_update'),
    path('transfer_delete/<int:pk>',views.TransferDeleteView.as_view(),name='transfer_delete'),
    path('chart_report/',views.ChartReportView.as_view(),name='chart_report'),
    path('transfer_report/',views.TransferReportView.as_view(),name='transfer_report'),


]