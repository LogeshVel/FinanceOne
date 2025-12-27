from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard_view, name='dashboard'), # Root URL points to dashboard (which redirects to login if needed)
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('retirement/', views.retirement_view, name='retirement'),
    path('income/', views.income_view, name='income'),
    path('expense/', views.expense_view, name='expense'),
    path('assets/', views.assets_view, name='assets'),
    path('insurance/', views.insurance_view, name='insurance'),
    path('loans/', views.loans_view, name='loans'),
    path('income/delete/<int:id>/', views.delete_income, name='delete_income'),
    path('expense/delete/<int:id>/', views.delete_expense, name='delete_expense'),
    path('loans/delete/<int:id>/', views.delete_loan, name='delete_loan'),
    path('insurance/delete/<int:id>/', views.delete_insurance, name='delete_insurance'),
    path('retirement/delete/<int:id>/', views.delete_retirement, name='delete_retirement'),
    path('assets/delete/<int:id>/', views.delete_asset, name='delete_asset'),
    path('budget/', views.budget_page, name='budget'),
    path('budget/activate/<int:id>/', views.activate_budget, name='activate_budget'),
    path('budget/delete/<int:id>/', views.delete_budget, name='delete_budget'),
    path('budget/details/<int:id>/', views.get_budget_details, name='get_budget_details'),
    path('goals/', views.goals_page, name='goals'),
    path('goals/delete/<int:id>/', views.delete_goal, name='delete_goal'),
]
