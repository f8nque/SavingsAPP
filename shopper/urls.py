from . import views
from django.urls import path
urlpatterns = [
    path('category/',views.CategoryView.as_view(),name='category'),
    path('shoppingcategorylist/',views.CategoryListView.as_view(),name='shopping_category_list'),
    path('categoryupdate/<int:pk>',views.CategoryUpdateView.as_view(),name='category_update'),
    path('categorydelete/<int:pk>',views.CategoryDeleteView.as_view(),name='category_delete'),
    path('shopping/',views.ShoppingItemView.as_view(),name='shopping'),
    path('shoppinglist/',views.ShoppingListView.as_view(),name='shopping_list'),
    path('updateshopping/<int:pk>', views.ShoppingUpdateView.as_view(), name='update_shopping'),
    path('deleteshopping/<int:pk>', views.ShoppingDeleteView.as_view(), name='delete_shopping'),
    path('boughtitem/<int:pk>',views.BoughtItemView.as_view(),name='bought_item'),
    path('boughtlist/<int:pk>',views.BoughtListView.as_view(),name='bought_list'),
    path('updatebought/<int:pk>',views.BoughtUpdateView.as_view(),name='update_bought'),
    path('deletebought/<int:pk>', views.BoughtDeleteView.as_view(), name='delete_bought'),
    ]