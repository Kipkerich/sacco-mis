from django import forms
from .models import Member, Saving, Loan, LoanRepayment

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['type', 'date_of_birth', 'name', 'membership_number', 'email', 'phone', 'address', 'status']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'membership_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SavingForm(forms.ModelForm):
    class Meta:
        model = Saving
        fields = ['member', 'amount', 'note']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'note': forms.TextInput(attrs={'class': 'form-control'}),
        }

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['member', 'amount', 'status', 'due_date']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class LoanRepaymentForm(forms.ModelForm):
    class Meta:
        model = LoanRepayment
        fields = ['loan', 'amount']
        widgets = {
            'loan': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }
