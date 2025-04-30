from django.db import models
from django.contrib.auth.models import User
import datetime

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profile')
    name = models.CharField(max_length=100, default='name', null=True, blank=True)
    type = models.IntegerField(default=1, choices=[
        (1, 'Admin'),
        (2, 'Auditor'),
        (3, 'Accountant'),
        (4, 'Supervisor'),
        (5, 'General Manager'),
    ])
    def __str__(self):
        return self.name

    def get_role_display(self):
        return dict(self._meta.get_field('type').choices).get(self.type, 'Unknown')

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

class Member(models.Model):
    MEMBER_TYPE_CHOICES = [
        (1, 'Junior'),
        (2, 'Normal'),
    ]
    type = models.IntegerField(default=1, choices=MEMBER_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    membership_number = models.CharField(max_length=30, unique=True,blank=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_joined = models.DateField(null=True, blank=True,default=datetime.date.today)
    pending_loan = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_repaid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    due_date = models.DateField(null=True, blank=True)
    status = models.BooleanField(default=True)  # Active/Inactive
    national_id = models.CharField(max_length=30, blank=True, null=True)
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    fellowship = models.CharField(max_length=100, blank=True, null=True)
    employment_status = models.CharField(max_length=50, blank=True, null=True)
    similar_sacco = models.CharField(max_length=100, blank=True, null=True)
    TERMS_OF_SERVICE_CHOICES = [
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
    ]
    terms_of_service = models.CharField(max_length=10, choices=TERMS_OF_SERVICE_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.membership_number})"

class Saving(models.Model):
    CATEGORY_CHOICES = [
        ("capital_share", "Capital Share"),
        ("member_deposit", "Member Deposit"),
    ]
    DEPOSIT_TYPE_CHOICES = [
        ("school_fees", "School Fees"),
        ("vacation", "Vacation"),
        ("other", "Other"),
    ]
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(blank=True,null=True)
    receipt_no = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="capital_share")
    deposit_type = models.CharField(max_length=20, choices=DEPOSIT_TYPE_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.member.name} - {self.amount} on {self.date} ({self.get_category_display()})"

class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('repaid', 'Repaid'),
    ]
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='loans')
    loan_plan = models.ForeignKey('LoanPlan', on_delete=models.SET_NULL, null=True, blank=True, related_name='loans')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    date_issued = models.DateField(auto_now_add=True)
    id_document = models.FileField(upload_to='loan_docs/id_documents/', null=True, blank=True)
    current_payslip = models.FileField(upload_to='loan_docs/payslips/', null=True, blank=True)
    bank_statement = models.FileField(upload_to='loan_docs/bank_statements/', null=True, blank=True)
    reference_number = models.CharField(max_length=100, null=True, blank=True)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)
    cheque_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.member.name} - {self.amount} ({self.status})"

class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(blank=True,null=True)

    def __str__(self):
        return f"{self.loan.member.name} - {self.amount} on {self.date}"

class LoanRepaymentSchedule(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayment_schedule')
    month = models.PositiveIntegerField()
    due_date = models.DateField(null=True, blank=True)
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    interest = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Loan {self.loan.id} - Month {self.month}: {self.total}"

class LoanProductType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class LoanPlan(models.Model):
    product_type = models.ForeignKey(LoanProductType, on_delete=models.CASCADE, related_name='loan_plans', null=True, blank=True)
    name = models.CharField(max_length=100)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration_months = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SourceOfIncome(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Borrower(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='borrower')
    date_added = models.DateTimeField(auto_now_add=True)
    EMPLOYMENT_STATUS_CHOICES = [
        ('employed', 'Employed'),
        ('self_employed', 'Self-employed'),
        ('unemployed', 'Unemployed'),
        ('other', 'Other'),
    ]
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, blank=True, null=True)
    # Employer details
    employer_name = models.CharField(max_length=100, blank=True, null=True)
    employer_address = models.CharField(max_length=255, blank=True, null=True)
    employer_phone = models.CharField(max_length=20, blank=True, null=True)
    # Business details
    business_name = models.CharField(max_length=100, blank=True, null=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    business_location = models.CharField(max_length=255, blank=True, null=True)
    # Sources of income
    sources_of_income = models.ManyToManyField(SourceOfIncome, blank=True)
    # Guarantors
    guarantors = models.ManyToManyField(Member, related_name='guaranteed_borrowers', blank=True)

    def __str__(self):
        return str(self.member)

class NextOfKin(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='next_of_kins')
    name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=30)
    relationship = models.CharField(max_length=50)
    tel = models.CharField(max_length=20)
    email = models.EmailField(max_length=100, blank=True, null=True)
    physical_address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.id_number}) - {self.relationship}"

class Witness(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='witnesses')
    name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=30)
    relationship = models.CharField(max_length=50)
    tel = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} ({self.id_number}) - {self.relationship}"

class SavingStatement(models.Model):
    CATEGORY_CHOICES = [
        ("capital_share", "Capital Share"),
        ("member_deposit", "Member Deposit"),
    ]
    DEPOSIT_TYPE_CHOICES = [
        ("school_fees", "School Fees"),
        ("vacation", "Vacation"),
        ("other", "Other"),
    ]
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='saving_statements')
    date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    running_balance = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="capital_share")
    deposit_type = models.CharField(max_length=20, choices=DEPOSIT_TYPE_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.member.name} | {self.amount} on {self.date.date()}"
