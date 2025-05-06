from django import forms
from .models import Member, Saving, Loan, LoanRepayment, NextOfKin, Borrower, SourceOfIncome

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'type', 'date_of_birth', 'name', 'membership_number', 'email', 'phone', 'address', 'status',
            'national_id', 'marital_status', 'fellowship',
            'employment_status', 'similar_sacco', 'terms_of_service'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'membership_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'fellowship': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_status': forms.TextInput(attrs={'class': 'form-control'}),
            'similar_sacco': forms.TextInput(attrs={'class': 'form-control'}),
            'terms_of_service': forms.Select(attrs={'class': 'form-select'}),
        }

class NextOfKinForm(forms.ModelForm):
    class Meta:
        model = NextOfKin
        exclude = ['member']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'tel': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'physical_address': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SavingForm(forms.ModelForm):
    class Meta:
        model = Saving
        fields = ['member', 'amount', 'date','receipt_no', 'category', 'deposit_type']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class':'form-control'}),
            'receipt_no': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select', 'required':False}),
            'deposit_type': forms.Select(attrs={'class': 'form-select', 'id': 'deposit_type', 'required': False}),
        }

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        exclude = ['member']
        widgets = {
            'loan_plan': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'id_document': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'application/pdf,image/*'}),
            'current_payslip': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'application/pdf,image/*'}),
            'bank_statement': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'application/pdf,image/*'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class LoanRepaymentForm(forms.ModelForm):
    class Meta:
        model = LoanRepayment
        fields = ['loan', 'amount','date']
        widgets = {
            'loan': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date':forms.DateInput(attrs={'types':'date','class':'form-control'}),
        }

class BorrowerForm(forms.ModelForm):
    class Meta:
        model = Borrower
        fields = [
            'member', 'employment_status',
            'employer_name', 'employer_address', 'employer_phone',
            'business_name', 'business_type', 'business_location',
            'sources_of_income', 'guarantors'
        ]
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'employer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'employer_address': forms.TextInput(attrs={'class': 'form-control'}),
            'employer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_type': forms.TextInput(attrs={'class': 'form-control'}),
            'business_location': forms.TextInput(attrs={'class': 'form-control'}),
            'sources_of_income': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'guarantors': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
