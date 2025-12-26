from django.db import models
from django.contrib.auth.models import User

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source_name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    frequency = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default='Active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_name} - {self.amount}"

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.amount}"

class Asset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    ticker = models.CharField(max_length=20, blank=True, null=True)
    type = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    buy_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Insurance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255)
    type = models.CharField(max_length=50)
    policy_number = models.CharField(max_length=100)
    premium = models.DecimalField(max_digits=10, decimal_places=2)
    premium_frequency = models.CharField(max_length=20, default='Monthly')
    renewal_date = models.DateField()
    status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} - {self.type}"

class Retirement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=100)
    provider = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    monthly_contribution = models.DecimalField(max_digits=10, decimal_places=2)
    return_rate = models.DecimalField(max_digits=5, decimal_places=2, default=7.00)
    employer_match = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ytd_return = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} - {self.account_type}"

class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lender_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tenure = models.IntegerField(help_text="Tenure in years")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField(default=None, null=True, blank=True)
    loan_type = models.CharField(max_length=50)  # bike, car, home, personal, education, other
    is_property_loan = models.BooleanField(default=False)
    resale_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lender_name} - {self.loan_type}"
