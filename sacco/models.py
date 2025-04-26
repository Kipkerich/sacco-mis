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

    def __str__(self):
        return f"{self.name} ({self.membership_number})"

class Saving(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.member.name} - {self.amount} on {self.date}"

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

    def __str__(self):
        return f"{self.member.name} - {self.amount} ({self.status})"

class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.loan.member.name} - {self.amount} on {self.date}"

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

class Borrower(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='borrower')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.member)
