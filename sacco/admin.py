from django.contrib import admin

from .models import Profile, Member, Saving, Loan, LoanRepayment, LoanPlan, Borrower

admin.site.register(Profile)
admin.site.register(Member)
admin.site.register(Saving)
admin.site.register(Loan)
admin.site.register(LoanRepayment)
admin.site.register(LoanPlan)
admin.site.register(Borrower)



