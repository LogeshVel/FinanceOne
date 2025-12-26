from django.contrib import admin
from .models import Income, Expense, Asset, Retirement, Insurance, Loan

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('source_name', 'amount', 'created_at', 'user')
    list_filter = ('user', 'created_at')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'category', 'date', 'user')
    list_filter = ('user', 'category', 'date')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'current_price', 'user')
    list_filter = ('user', 'type')

@admin.register(Retirement)
class RetirementAdmin(admin.ModelAdmin):
    list_display = ('provider', 'balance', 'monthly_contribution', 'user')
    list_filter = ('user', 'provider')

@admin.register(Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = ('provider', 'premium', 'renewal_date', 'user')
    list_filter = ('user',)

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('lender_name', 'amount', 'interest_rate', 'start_date', 'user')
    list_filter = ('user', 'loan_type')
