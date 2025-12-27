from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currency = models.CharField(max_length=10, default='INR')

    def __str__(self):
        return self.user.username

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    
    # Monthly Data
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fixed_expenses = models.JSONField(default=dict)
    variable_expenses = models.JSONField(default=dict)
    savings_investments = models.JSONField(default=dict)
    
    # Yearly Data
    yearly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    annual_costs = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    def activate(self):
        # Set this budget as active and all others as inactive for this user
        Budget.objects.filter(user=self.user).update(is_active=False)
        self.is_active = True
        self.save()

    def copy_from(self, other_budget):
        if not other_budget:
            return
        self.monthly_income = other_budget.monthly_income
        self.fixed_expenses = other_budget.fixed_expenses
        self.variable_expenses = other_budget.variable_expenses
        self.savings_investments = other_budget.savings_investments
        self.yearly_income = other_budget.yearly_income
        self.annual_costs = other_budget.annual_costs
        self.save()
