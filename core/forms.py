from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'bg-[#101922] border border-[#223649] text-white placeholder:text-[#586e82] focus:border-[#0d7ff2] rounded-md p-2 w-full',
        'placeholder': 'John Doe'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'bg-[#101922] border border-[#223649] text-white placeholder:text-[#586e82] focus:border-[#0d7ff2] rounded-md p-2 w-full',
        'placeholder': 'you@example.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'bg-[#101922] border border-[#223649] text-white placeholder:text-[#586e82] focus:border-[#0d7ff2] rounded-md p-2 w-full',
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
        'class': 'bg-[#101922] border border-[#223649] text-white rounded-md p-2 w-full focus:outline-none focus:border-[#0d7ff2]'
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
