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

class FinancialGoal(models.Model):
    GOAL_TYPES = [
        ('IMMEDIATE', 'Immediate (0-12 Months)'),
        ('SHORT', 'Short-Term (1-3 Years)'),
        ('MEDIUM', 'Medium-Term (3-7 Years)'),
        ('LONG', 'Long-Term (7+ Years)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    category = models.CharField(max_length=20, choices=GOAL_TYPES, default='SHORT')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text="Why do I want it?")
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField()
    funding_strategy = models.TextField(blank=True, help_text="How will I fund it?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            percent = (self.current_amount / self.target_amount) * 100
            return min(percent, 100)
        return 0

    @property
    def status(self):
        from django.utils import timezone
        today = timezone.now().date()
        
        # 1. Check Completed
        if self.current_amount >= self.target_amount:
            return 'COMPLETED'
            
        # 2. Check Overdue
        if self.target_date < today:
            return 'OVERDUE'
            
        # 3. Check New (Created within last 3 days and 0 savings)
        delta = today - self.created_at.date()
        if delta.days <= 3 and self.current_amount == 0:
            return 'NEW'
            
        # 4. Default
        return 'IN_PROGRESS'
