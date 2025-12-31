from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Budget, FinancialGoal

class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'bg-background border border-border text-text-main placeholder-text-muted focus:border-primary rounded-md p-2 w-full',
        'placeholder': 'John Doe'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'bg-background border border-border text-text-main placeholder-text-muted focus:border-primary rounded-md p-2 w-full',
        'placeholder': 'you@example.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'bg-background border border-border text-text-main placeholder-text-muted focus:border-primary rounded-md p-2 w-full',
        'placeholder': 'Min 6 characters'
    }))
    currency = forms.ChoiceField(choices=[
        ('INR', 'Indian Rupee (₹)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('JPY', 'Japanese Yen (¥)'),
        ('CNY', 'Chinese Yuan (¥)'),
        ('AED', 'UAE Dirham (د.إ)'),
        ('CHF', 'Swiss Franc (CHF)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('CAD', 'Canadian Dollar (C$)'),
    ], initial='INR', widget=forms.Select(attrs={
        'class': 'bg-background border border-border text-text-main rounded-md p-2 w-full focus:outline-none focus:border-primary'
    }))

    class Meta:
        model = User
        fields = ['first_name', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            UserProfile.objects.create(user=user, currency=self.cleaned_data['currency'])
        return user

class BudgetCreationForm(forms.ModelForm):
    copy_from = forms.ModelChoiceField(
        queryset=Budget.objects.none(),
        required=False,
        empty_label="Start from Scratch",
        label="Copy from existing budget"
    )

    class Meta:
        model = Budget
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary placeholder-text-muted'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['copy_from'].queryset = Budget.objects.filter(user=user).order_by('-updated_at')
        self.fields['copy_from'].widget.attrs.update({'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary'})

class MonthlyBudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['monthly_income']
        widgets = {
            'monthly_income': forms.NumberInput(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary'}),
        }

class YearlyBudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['yearly_income']
        widgets = {
            'yearly_income': forms.NumberInput(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary'}),
        }

class FinancialGoalForm(forms.ModelForm):
    class Meta:
        model = FinancialGoal
        fields = ['category', 'name', 'description', 'target_amount', 'current_amount', 'target_date', 'funding_strategy']
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary'}),
            'name': forms.TextInput(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary placeholder-text-muted'}),
            'description': forms.Textarea(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary placeholder-text-muted', 'rows': 2}),
            'target_amount': forms.NumberInput(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary placeholder-text-muted'}),
            'current_amount': forms.NumberInput(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary placeholder-text-muted'}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary placeholder-text-muted'}),
            'funding_strategy': forms.Textarea(attrs={'class': 'w-full bg-background border border-border text-text-main rounded-lg px-4 py-3 focus:outline-none focus:border-primary placeholder-text-muted', 'rows': 2}),
        }
