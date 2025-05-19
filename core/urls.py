from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TransactionViewSet, BudgetViewSet, index, dashboard, register, add_transaction, load_categories, budget_list, budget_create,  budget_edit, edit_transaction, delete_transaction, delete_budget, load_categories, transaction_list, category_delete, category_update, category_create, category_list
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.views import LogoutView, LoginView
from . import views

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'budgets', BudgetViewSet, basename='budget')


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('', index, name='index'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', register, name='register'),
    path('ajax/load-categories/', load_categories, name='ajax_load_categories'),
    path('budgets/', budget_list, name='budget_list'),
    path('budgets/add/', budget_create, name='budget_create'),
    path('budgets/<int:pk>/edit/', budget_edit, name='budget_edit'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/edit/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('budgets/<int:pk>/delete/', delete_budget, name='delete_budget'),
    path('ajax/load-categories/', views.load_categories, name='ajax_load_categories'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('', lambda request: redirect('dashboard'), name='index'),
]


