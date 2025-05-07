from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile, Member, Saving, Loan, LoanRepayment, Borrower, LoanPlan, LoanProductType, LoanRepaymentSchedule, NextOfKin, SourceOfIncome
from .forms import MemberForm, SavingForm, LoanForm, LoanRepaymentForm, NextOfKinForm, BorrowerForm
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from datetime import date
from django.db.models.functions import TruncMonth
from django.db.models import Count
from dateutil.relativedelta import relativedelta
from django.contrib.auth import authenticate, login
from django.db import models
from django.db.models import Sum
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.template.loader import render_to_string
import weasyprint
from decimal import Decimal, InvalidOperation
import requests
import os
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from .models import Member
    # --- Map JSON data to models ---
from .models import Profile, Member, Saving, Loan, LoanRepayment, LoanRepaymentSchedule, LoanProductType, LoanPlan, Borrower, SavingStatement
from django.forms import modelformset_factory, inlineformset_factory
def register_view(request):
    if request.method == 'POST':
        from django.contrib.auth.models import User
        name = request.POST.get('name')
        type_val = request.POST.get('type')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        # Basic validation
        if not (name and type_val and username and password1 and password2):
            form_errors = 'All fields are required.'
            return render(request, 'register.html', {'form_errors': form_errors})
        if password1 != password2:
            form_errors = 'Passwords do not match.'
            return render(request, 'register.html', {'form_errors': form_errors})
        if User.objects.filter(username=username).exists():
            form_errors = 'Username already exists.'
            return render(request, 'register.html', {'form_errors': form_errors})
        user = User.objects.create_user(username=username, password=password1)
        profile = Profile.objects.create(user=user, name=name, type=type_val)
        return redirect('users-url')
    else:
        return render(request, 'register.html')

@login_required
def home_view(request):
    members_count = Member.objects.count()
    savers_count = Member.objects.filter(savings__isnull=False).distinct().count()
    borrowers_count = Borrower.objects.count()
    defaulters_count = Loan.objects.filter(status='pending', due_date__lt=date.today()).count()
    recent_loans = Loan.objects.select_related('member').order_by('-date_issued')[:5]
    recent_members = Member.objects.order_by('-date_joined')[:5]
    role=Profile.objects.get(user=request.user).type
    # Loans per month (last 12 months)
    loans_by_month_qs = (
        Loan.objects.annotate(month=TruncMonth('date_issued'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    loans_by_month = {item['month'].strftime('%b %Y'): item['count'] for item in loans_by_month_qs if item['month']}

    # Savings per month (last 12 months)
    savings_by_month_qs = (
        Saving.objects.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    savings_by_month = {item['month'].strftime('%b %Y'): float(item['total'] or 0) for item in savings_by_month_qs if item['month']}

    # Build last 12 months labels
    today = date.today()
    months = [(today - relativedelta(months=i)).strftime('%b %Y') for i in reversed(range(12))]
    loans_data = [loans_by_month.get(month, 0) for month in months]
    savings_data = [savings_by_month.get(month, 0) for month in months]
    print(role)
    return render(request, 'index.html', {
        'members_count': members_count,
        'savers_count': savers_count,
        'borrowers_count': borrowers_count,
        'defaulters_count': defaulters_count,
        'recent_loans': recent_loans,
        'recent_members': recent_members,
        'chart_months': months,
        'chart_loans_data': loans_data,
        'chart_savings_data': savings_data,
        'role': role
    })

@login_required
def users_view(request):
    role=Profile.objects.get(user=request.user).type
    users = User.objects.all()
    profiles = Profile.objects.all()
    return render(request, 'users.html', {'users': users, 'profiles': profiles, 'role': role})

@login_required
def manage_user(request, id):
    if request.method == 'POST':
        user = User.objects.get(id=id)
        profile = Profile.objects.get(user=user)
        profile.name = request.POST['name']
        profile.type = request.POST['type']
        if request.POST['password']:
            user.set_password(request.POST['password'])
        profile.save()
        user.save()
        return redirect('users-url')
    user = User.objects.get(id=id)
    profile = Profile.objects.get(user=user)
    role=Profile.objects.get(user=request.user).type
    return render(request, 'manage_user.html', {'user': user, 'profile': profile})

@login_required
def delete_user(request, id):
    user = User.objects.get(id=id)
    profile = Profile.objects.get(user=user)
    user.delete()
    profile.delete()
    return redirect('users-url')

@login_required
def members_list(request):
    members = Member.objects.all()
    members_data = []
    for member in members:
        total_saved = member.savings.aggregate(total=models.Sum('amount'))['total'] or 0
        total_repaid = member.loans.aggregate(total=models.Sum('repayments__amount'))['total'] or 0
        pending_loan = member.loans.filter(status='pending').aggregate(total=models.Sum('amount'))['total'] or 0
        due_date = member.loans.filter(status='pending').order_by('due_date').values_list('due_date', flat=True).first()
        members_data.append({
            'member': member,
            'total_saved': total_saved,
            'amount_repaid': total_repaid,
            'pending_loan': pending_loan,
            'due_date': due_date,
        })
    role=Profile.objects.get(user=request.user).type
    return render(request, 'members.html', {'members_data': members_data, 'role': role})

@login_required
def member_add(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('members-list')
    else:
        form = MemberForm()
    return render(request, 'member_form.html', {'form': form, 'action': 'Add'})

@login_required
def member_edit(request, id):
    member = get_object_or_404(Member, id=id)
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            return redirect('members-list')
    else:
        form = MemberForm(instance=member)
    return render(request, 'member_form.html', {'form': form, 'action': 'Edit'})

@login_required
def member_delete(request, id):
    member = get_object_or_404(Member, id=id)
    if request.method == 'POST':
        member.delete()
        return redirect('members-list')
    return render(request, 'member_confirm_delete.html', {'member': member})

@login_required
def member_toggle_status(request, id):
    
    member = get_object_or_404(Member, id=id)
    if request.method == 'POST':
        member.status = not member.status
        member.save()
   
    return redirect('member_detail', id=member.id )

# Dashboard
@login_required
def dashboard(request):
    total_members = Member.objects.count()
    total_savings = Saving.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_loans = Loan.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    return render(request, 'dashboard.html', {
        'total_members': total_members,
        'total_savings': total_savings,
        'total_loans': total_loans,
    })

# Member Detail
@login_required
def member_detail(request, id):
    role=Profile.objects.get(user=request.user).type
    member = get_object_or_404(Member, id=id)
    return render(request, 'member_detail.html', {'member': member, 'role': role})

# --- Member AJAX Search ---
@require_GET
def member_search_by_ref_number(request):
    ref_number = request.GET.get('ref_number')
    if not ref_number:
        return JsonResponse({'success': False, 'error': 'No reference number provided.'})
    try:
        member = Member.objects.get(membership_number=ref_number)
        return JsonResponse({'success': True, 'member': {'name': member.name}})
    except Member.DoesNotExist:
        return JsonResponse({'success': False})

# Savings Views
@login_required
def savings_list(request):
    from django.db.models import Sum
    members = Member.objects.all()
    members_savings = []
    for member in members:
        savings = member.savings.all().order_by('-date')
        total = savings.aggregate(total=Sum('amount'))['total'] or 0
        members_savings.append({
            'member': member,
            'total_saved': total,
            'savings': savings
        })
    role=Profile.objects.get(user=request.user).type
    return render(request, 'savings.html', {'members_savings': members_savings, 'members': members, 'role': role})

@login_required
def saving_add(request):
    role = Profile.objects.get(user=request.user).type
    if request.method == 'POST':
        form = SavingForm(request.POST)
        capital_share_total = 0
        member = None
        if form.is_valid():
            member = form.cleaned_data['member']
        else:
            # Try to get member from POST if form is invalid
            member_id = request.POST.get('member')
            if member_id:
                from .models import Member, Saving
                try:
                    member = Member.objects.get(id=member_id)
                    capital_share_total = Saving.objects.filter(member=member, category='capital_share').aggregate(total=models.Sum('amount'))['total'] or 0
                except Member.DoesNotExist:
                    pass
        if member and capital_share_total == 0:
            from .models import Saving
            capital_share_total = Saving.objects.filter(member=member, category='capital_share').aggregate(total=models.Sum('amount'))['total'] or 0
        if form.is_valid():
            amount = form.cleaned_data['amount']
            date=form.cleaned_data['date']
            receiptNo = form.cleaned_data['receipt_no']

            # Calculate total capital share so far
            to_capital_share = 0
            to_member_deposit = 0
            # If member hasn't reached 10,000 in capital share, allocate up to 10,000
            if capital_share_total < 10000:
                remaining = 10000 - capital_share_total
                if amount <= remaining:
                    to_capital_share = amount
                else:
                    to_capital_share = remaining
                    to_member_deposit = amount - remaining
            else:
                to_member_deposit = amount
            # Save Capital Share part if any
            if to_capital_share > 0:
                Saving.objects.create(
                    member=member,
                    amount=to_capital_share,
                    receipt_no=receiptNo,
                    category='capital_share',
                    date=date
                )
                from sacco.utils import create_saving_statement
                create_saving_statement(
                    member=member,
                    amount=to_capital_share,
                    category='capital_share',
                    deposit_type=form.cleaned_data.get('deposit_type'),
                    description=f"Capital Share deposit of {to_capital_share}"
                )
            # Save Member Deposit part if any
            if to_member_deposit > 0:
                deposit_type = form.cleaned_data.get('deposit_type')
                Saving.objects.create(
                    member=member,
                    amount=to_member_deposit,
                    receipt_no=receiptNo,
                    category='member_deposit',
                    date=date,
                    deposit_type=deposit_type
                )
                from sacco.utils import create_saving_statement
                create_saving_statement(
                    member=member,
                    amount=to_member_deposit,
                    category='member_deposit',
                    deposit_type=deposit_type,
                    description=f"Member Deposit of {to_member_deposit}"
                )
            return redirect('savings')
        else:
            print('SavingForm errors:', form.errors)
    else:
        form = SavingForm()
        member = form.fields['member'].queryset.first() if form.fields['member'].queryset.exists() else None
        capital_share_total = 0
        if member:
            from .models import Saving
            capital_share_total = Saving.objects.filter(member=member, category='capital_share').aggregate(total=models.Sum('amount'))['total'] or 0
    return render(request, 'saving_form.html', {
        'form': form,
        'action': 'Add',
        'capital_share_total': capital_share_total,
        'role': role,
        'members': Member.objects.all()
    })

@login_required
def saving_edit(request, id):
    saving = get_object_or_404(Saving, id=id)
    if request.method == 'POST':
        form = SavingForm(request.POST, instance=saving)
        if form.is_valid():
            form.save()
            return redirect('savings')
    else:
        form = SavingForm(instance=saving)
    return render(request, 'member_form.html', {'form': form, 'action': 'Edit Saving'})

@login_required
def saving_delete(request, id):
    saving = get_object_or_404(Saving, id=id)
    if request.method == 'POST':
        saving.delete()
        return redirect('savings')
    return render(request, 'member_confirm_delete.html', {'member': saving})

@login_required
def saving_edit_type(request, id):
    saving = get_object_or_404(Saving, id=id)
    if request.method == 'POST':
        savings_type = request.POST.get('savings_type')
        if savings_type:
            # Update Saving
            saving.savings_type = savings_type
            # Update category/deposit_type fields
            if savings_type == 'capital_share':
                saving.category = 'capital_share'
                saving.deposit_type = ''
            else:
                saving.category = 'member_deposit'
                saving.deposit_type = savings_type
            saving.save()
            # Update related SavingStatement(s)
            from .models import SavingStatement
            statements = SavingStatement.objects.filter(
                member=saving.member,
                amount=saving.amount,
                date__date=saving.date
            )
            for statement in statements:
                if savings_type == 'capital_share':
                    statement.category = 'capital_share'
                    statement.deposit_type = ''
                else:
                    statement.category = 'member_deposit'
                    statement.deposit_type = savings_type
                statement.save()
        return redirect(request.META.get('HTTP_REFERER', 'savings'))
    return redirect('savings')

# Loans Views
@login_required
def loans_list(request):
    role=Profile.objects.get(user=request.user).type
    loans = Loan.objects.select_related('member', 'loan_plan').all()
    loan_plans = LoanPlan.objects.all()
    return render(request, 'loans.html', {'loans': loans, 'loan_plans': loan_plans, 'role': role})

@login_required
def loan_add(request):
    if request.method == 'POST':
        form = LoanForm(request.POST, request.FILES)
        ref_number = request.POST.get('ref_number')
        member = Member.objects.filter(membership_number=ref_number).first()
        if not member:
            print('Loan NOT saved: Member not found for ref_number:', ref_number)
        if not form.is_valid():
            print('LoanForm errors:', form.errors)
        if form.is_valid() and member:
            loan = form.save(commit=False)
            loan.member = member
            loan.save()
            # Generate and save repayment schedule
            loan_plan = loan.loan_plan
            months = loan_plan.duration_months if loan_plan else 0
            rate = loan_plan.interest_rate / Decimal('100') if loan_plan else 0
            principal = loan.amount
            if months > 0 and principal > 0:
                monthly_interest = principal * rate / months
                monthly_payment = (principal + (principal * rate)) / months
                for i in range(1, months + 1):
                    LoanRepaymentSchedule.objects.create(
                        loan=loan,
                        month=i,
                        due_date=None,  # Optionally calculate real due dates
                        principal=round(principal / months, 2),
                        interest=round(monthly_interest, 2),
                        total=round(monthly_payment, 2),
                    )
        return redirect('loans')
    else:
        form = LoanForm()
    return redirect('loans')

@login_required
def loan_edit(request, id):
    loan = get_object_or_404(Loan, id=id)
    if request.method == 'POST':
        # Update fields from modal form POST
        loan_plan_id = request.POST.get('loan_plan')
        ref_number = request.POST.get('ref_number')
        amount = request.POST.get('amount')
        status = request.POST.get('status')
        due_date = request.POST.get('due_date')
        # Update loan fields
        if loan_plan_id:
            loan.loan_plan_id = loan_plan_id
        if amount:
            loan.amount = amount
        if status:
            loan.status = status
        if due_date:
            loan.due_date = due_date
        loan.save()
        return redirect('loans')
    else:
        form = LoanForm(instance=loan)
    return render(request, 'member_form.html', {'form': form, 'action': 'Edit Loan'})

@login_required
def loan_delete(request, id):
    loan = get_object_or_404(Loan, id=id)
    if request.method == 'POST':
        loan.delete()
        return redirect('loans')
    return render(request, 'member_confirm_delete.html', {'member': loan})

@login_required
def loan_detail(request, loan_id):
    role=Profile.objects.get(user=request.user).type
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = loan.repayments.all()
    # Filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if start_date:
        repayments = repayments.filter(date__gte=start_date)
    if end_date:
        repayments = repayments.filter(date__lte=end_date)
    if min_amount:
        repayments = repayments.filter(amount__gte=min_amount)
    if max_amount:
        repayments = repayments.filter(amount__lte=max_amount)
    repayments = repayments.order_by('-date')
    return render(request, 'loan_detail.html', {'loan': loan, 'repayments': repayments, 'start_date': start_date, 'end_date': end_date, 'min_amount': min_amount, 'max_amount': max_amount, 'role': role})

import csv
from django.http import HttpResponse
@login_required
def download_repayments_csv(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = loan.repayments.all()
    # Apply same filters as in detail view
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if start_date:
        repayments = repayments.filter(date__gte=start_date)
    if end_date:
        repayments = repayments.filter(date__lte=end_date)
    if min_amount:
        repayments = repayments.filter(amount__gte=min_amount)
    if max_amount:
        repayments = repayments.filter(amount__lte=max_amount)
    # CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="loan_{loan.id}_repayments.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Amount', 'Date'])
    for i, rep in enumerate(repayments, 1):
        writer.writerow([i, rep.amount, rep.date])
    return response

@login_required
def loan_repayment(request, loan_id):
    role=Profile.objects.get(user=request.user).type
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = LoanRepayment.objects.filter(loan=loan)
    total_repaid = repayments.aggregate(total=models.Sum('amount'))['total'] or 0
    pending = loan.amount - total_repaid
    feedback = None
    if request.method == 'POST':
        print(request)
        model=LoanRepayment
        form = LoanRepaymentForm(request.POST)
        if form.is_valid():
            repayment = form.save(commit=False)
            repayment.loan = loan
            repay_amount = repayment.amount
            if repay_amount > pending:
                repayment.amount = pending
                repayment.save()
                excess = repay_amount - pending
                if excess > 0:
                    Saving.objects.create(member=loan.member, amount=excess, note=f'Excess loan repayment for Loan #{loan.id}')
                    feedback = f"Excess repayment of {excess} added to savings."
            else:
                repayment.save()
            return render(request, 'loan_repayment.html', {'form': LoanRepaymentForm(initial={'loan': loan}), 'repayments': LoanRepayment.objects.filter(loan=loan), 'pending': loan.amount - (total_repaid + repay_amount if repay_amount <= pending else pending), 'feedback': feedback})
    else:
        form = LoanRepaymentForm(initial={'loan': loan})
    return render(request, 'loan_repayment.html', {'form': form, 'repayments': repayments, 'pending': pending, 'feedback': feedback,'role': role})

@login_required
def loan_repayments_list(request, loan_id):
    role=Profile.objects.get(user=request.user).type
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = loan.repayments.order_by('-date')
    if request.method == 'POST':
        amount = request.POST.get('amount')
        date=request.POST.get('date')
        if amount:
            LoanRepayment.objects.create(loan=loan, amount=amount,date=date)
            return redirect('loan-repayments-list', loan_id=loan.id)
    return render(request, 'loan_repayments.html', {'loan': loan, 'repayments': repayments, 'role': role})

@login_required
def loan_repayments_pdf(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = loan.repayments.order_by('-date')
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    import weasyprint
    html = render_to_string('loan_repayments_pdf.html', {'loan': loan, 'repayments': repayments})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="loan_{loan.id}_repayments.pdf"'
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response

# Borrowers Views
@login_required
def borrowers_list(request):
    role=Profile.objects.get(user=request.user).type
    borrowers = Borrower.objects.select_related('member').all()
    # Calculate total savings for each borrower
    borrowers_data = []
    for borrower in borrowers:
        savings_total = borrower.member.savings.aggregate(total=Sum('amount'))['total'] or 0
        borrowers_data.append({
            'borrower': borrower,
            'savings_total': savings_total
        })
    members = Member.objects.exclude(borrower__isnull=False)
    return render(request, 'borrowers.html', {'borrowers_data': borrowers_data, 'members': members, 'role': role})

@login_required
def borrower_add(request):
    role=Profile.objects.get(user=request.user).type
    if request.method == 'POST':
        form = BorrowerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('borrowers-url')
    else:
        form = BorrowerForm()
    return render(request, 'borrower_form.html', {'form': form, 'role': role})

# Loan Plans Views
@login_required
def loan_plans_list(request):
    role=Profile.objects.get(user=request.user).type
    loan_product_types = LoanProductType.objects.all()
    loan_plans = LoanPlan.objects.all().order_by('-date_created')
    return render(request, 'loan_plans.html', {'loan_plans': loan_plans, 'loan_product_types': loan_product_types, 'role': role})

@login_required
@login_required
def loan_plan_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        interest_rate = request.POST.get('interest_rate')
        duration_months = request.POST.get('duration_months')
        description = request.POST.get('description')
        if name and interest_rate and duration_months:
            LoanPlan.objects.create(
                name=name,
                interest_rate=interest_rate,
                duration_months=duration_months,
                description=description or ''
            )
    return redirect('loan-plans-url')

# Loan Product Types Management

@login_required
def loan_product_type_list(request):
    role=Profile.objects.get(user=request.user).type
    product_types = LoanProductType.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            LoanProductType.objects.create(name=name, description=description)
        return redirect('loan-product-type-list')
    return render(request, 'loan_product_types.html', {'product_types': product_types, 'role': role})

@login_required
@require_POST
def loan_product_type_edit(request, id):
    product_type = get_object_or_404(LoanProductType, id=id)
    name = request.POST.get('name')
    description = request.POST.get('description')
    if name:
        product_type.name = name
        product_type.description = description
        product_type.save()
    return redirect('loan-product-type-list')

@login_required
@require_POST
def loan_product_type_delete(request, id):
    product_type = get_object_or_404(LoanProductType, id=id)
    product_type.delete()
    return redirect('loan-product-type-list')

# Reports
@login_required
def reports(request):
    role=Profile.objects.get(user=request.user).type
    report_type = request.GET.get('report_type', 'members')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    results = []
    if report_type == 'members':
        qs = Member.objects.all()
        if date_from:
            qs = qs.filter(date_joined__gte=date_from)
        if date_to:
            qs = qs.filter(date_joined__lte=date_to)
        results = list(qs)
    elif report_type == 'savings':
        qs = Saving.objects.select_related('member')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        results = list(qs)
    elif report_type == 'loans':
        qs = Loan.objects.select_related('member', 'loan_plan')
        if date_from:
            qs = qs.filter(date_issued__gte=date_from)
        if date_to:
            qs = qs.filter(date_issued__lte=date_to)
        results = list(qs)
    elif report_type == 'repayments':
        qs = LoanRepayment.objects.select_related('loan__member')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        results = list(qs)
    return render(request, 'reports.html', {
        'report_type': report_type,
        'date_from': date_from,
        'date_to': date_to,
        'results': results,
        'now': timezone.now(),
        'role': role
    })

@login_required
def repayments_page(request):
    role=Profile.objects.get(user=request.user).type
    loans = Loan.objects.select_related('member', 'loan_plan')
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if query:
        loans = loans.filter(
            models.Q(member__name__icontains=query) |
            models.Q(member__membership_number__icontains=query)
        )
    if status:
        loans = loans.filter(status=status)
    loans = loans.order_by('-date_issued')
    # Calculate total repayments and pending amount for each loan
    for loan in loans:
        loan.total_repaid = loan.repayments.aggregate(total=models.Sum('amount'))['total'] or 0
        loan.pending_amount = loan.amount - loan.total_repaid
    return render(request, 'repayments.html', {'loans': loans, 'q': query, 'status': status, 'role': role})

@login_required
@require_http_methods(["GET", "POST"])
def loan_approvals(request):
    role=Profile.objects.get(user=request.user).type
    if request.method == "POST":
        loan_id = request.POST.get("loan_id")
        action = request.POST.get("action")
        loan = get_object_or_404(Loan, id=loan_id, status="pending")
        if action == "approve":
            loan.status = "approved"
            loan.cheque_number = request.POST.get("cheque_number")
            loan.cheque_date = request.POST.get("cheque_date")
            loan.save()
        elif action == "reject":
            loan.status = "rejected"
            loan.save()
        return redirect("loan-approvals")
    # GET: list all pending loans
    loans = Loan.objects.filter(status="pending").select_related("member", "loan_plan")
    return render(request, "loan_approvals.html", {"loans": loans, 'role': role})

def login_view(request):
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                profile = user.profile
                request.session['user_type'] = profile.type
            except Profile.DoesNotExist:
                request.session['user_type'] = None
            return redirect('dashboard')
        else:
            error_message = 'Invalid username or password.'
    return render(request, 'login.html', {'error_message': error_message})

@login_required
def generate_statement(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    statements = member.saving_statements.all().order_by('date')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        statements = statements.filter(date__date__gte=parse_date(start_date))
    if end_date:
        statements = statements.filter(date__date__lte=parse_date(end_date))

    capital_share_statements = statements.filter(category='capital_share')
    member_deposit_school_fees = statements.filter(category='member_deposit', deposit_type='school_fees')
    member_deposit_vacation = statements.filter(category='member_deposit', deposit_type='vacation')
    member_deposit_other = statements.filter(category='member_deposit', deposit_type='other')
    context = {
        'member': member,
        'statements': statements,
        'capital_share_statements': capital_share_statements,
        'member_deposit_school_fees': member_deposit_school_fees,
        'member_deposit_vacation': member_deposit_vacation,
        'member_deposit_other': member_deposit_other,
        'start_date': start_date or '',
        'end_date': end_date or '',
    }
    type = Profile.objects.get(user=request.user).type
    context['role'] = type
    return render(request, 'saving_statement.html', context)

@login_required
def statement_pdf(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    statements = member.saving_statements.all().order_by('date')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    from django.utils import timezone
    now = timezone.now()
    from django.utils.dateparse import parse_date
    if start_date:
        statements = statements.filter(date__date__gte=parse_date(start_date))
    if end_date:
        statements = statements.filter(date__date__lte=parse_date(end_date))
    capital_share_statements = statements.filter(category='capital_share')
    member_deposit_school_fees = statements.filter(category='member_deposit', deposit_type='school_fees')
    member_deposit_vacation = statements.filter(category='member_deposit', deposit_type='vacation')
    member_deposit_other = statements.filter(category='member_deposit', deposit_type='other')
    html = render_to_string('saving_statement_pdf.html', {
        'member': member,
        'statements': statements,
        'capital_share_statements': capital_share_statements,
        'member_deposit_school_fees': member_deposit_school_fees,
        'member_deposit_vacation': member_deposit_vacation,
        'member_deposit_other': member_deposit_other,
        'now': now,
        'start_date': start_date or '',
        'end_date': end_date or '',
    })
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="statement_{member.membership_number}.pdf"'
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response

@login_required
def general_statement(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    show_savings = request.GET.get('show_savings', '1') == '1'
    show_loans = request.GET.get('show_loans', '1') == '1'
    show_repayments = request.GET.get('show_repayments', '1') == '1'

    savings = member.saving_statements.all().order_by('date') if show_savings else []
    loans = member.loans.all().order_by('date_issued') if show_loans else []
    repayments = LoanRepayment.objects.filter(loan__member=member).order_by('date') if show_repayments else []

    if start_date:
        if show_savings:
            savings = savings.filter(date__date__gte=parse_date(start_date))
        if show_loans:
            loans = loans.filter(date_issued__date__gte=parse_date(start_date))
        if show_repayments:
            repayments = repayments.filter(date__date__gte=parse_date(start_date))
    if end_date:
        if show_savings:
            savings = savings.filter(date__date__lte=parse_date(end_date))
        if show_loans:
            loans = loans.filter(date_issued__date__lte=parse_date(end_date))
        if show_repayments:
            repayments = repayments.filter(date__date__lte=parse_date(end_date))
    type = Profile.objects.get(user=request.user).type
    context = {
        'member': member,
        'savings': savings,
        'loans': loans,
        'repayments': repayments,
        'start_date': start_date or '',
        'end_date': end_date or '',
        'show_savings': show_savings,
        'show_loans': show_loans,
        'show_repayments': show_repayments,
        'role': type
    }
    return render(request, 'general_statement.html', context)

@login_required
def general_statement_pdf(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    show_savings = request.GET.get('show_savings', '1') == '1'
    show_loans = request.GET.get('show_loans', '1') == '1'
    show_repayments = request.GET.get('show_repayments', '1') == '1'

    savings = member.saving_statements.all().order_by('date') if show_savings else []
    loans = member.loans.all().order_by('date_issued') if show_loans else []
    repayments = LoanRepayment.objects.filter(loan__member=member).order_by('date') if show_repayments else []

    if start_date:
        if show_savings:
            savings = savings.filter(date__date__gte=parse_date(start_date))
        if show_loans:
            loans = loans.filter(date_issued__date__gte=parse_date(start_date))
        if show_repayments:
            repayments = repayments.filter(date__date__gte=parse_date(start_date))
    if end_date:
        if show_savings:
            savings = savings.filter(date__date__lte=parse_date(end_date))
        if show_loans:
            loans = loans.filter(date_issued__date__lte=parse_date(end_date))
        if show_repayments:
            repayments = repayments.filter(date__date__lte=parse_date(end_date))

    from django.template.loader import render_to_string
    from django.http import HttpResponse
    import weasyprint
    html = render_to_string('general_statement_pdf.html', {
        'member': member,
        'savings': savings,
        'loans': loans,
        'repayments': repayments,
        'start_date': start_date or '',
        'end_date': end_date or '',
        'show_savings': show_savings,
        'show_loans': show_loans,
        'show_repayments': show_repayments,
    })
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="general_statement_{member.membership_number}.pdf"'
    weasyprint.HTML(string=html).write_pdf(response)
    return response

@login_required
def loan_schedule_view(request, loan_id):
    role=Profile.objects.get(user=request.user).type
    loan = get_object_or_404(Loan, id=loan_id)
    schedule = loan.repayment_schedule.order_by('month')
    return render(request, 'loan_schedule_view.html', {'loan': loan, 'schedule': schedule, 'role': role})

@login_required
def loan_schedule_view_pdf(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    schedule = loan.repayment_schedule.order_by('month')
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    import weasyprint
    html = render_to_string('partials/loan_schedule_table_pdf.html', {'schedule': schedule, 'plan': loan.loan_plan, 'amount': loan.amount, 'loan': loan})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="loan_{loan.id}_schedule.pdf"'
    weasyprint.HTML(string=html).write_pdf(response)
    return response

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def process_sql_data_view(request):
    """
    View to process large SQL-formatted data using Gemini AI, map to all models, and save in the database.
    Expects POST with 'sql_data' in request.POST.
    """
    sql_data = request.POST.get('sql_data')
    if not sql_data:
        return JsonResponse({'success': False, 'error': 'No SQL data provided.'}, status=400)

    # --- Gemini AI API call ---
    # Set your Gemini API key here or in your environment variables
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCYgM0mbrRIzyr8maQRVsQ0qlGZaRS71pg')
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY

    # Prompt Gemini to convert SQL data to a JSON structure matching all models
    prompt = f"""
    You are a data transformation assistant. Given the following SQL-formatted data, convert it into JSON arrays for each Django model: Profile, Member, Saving, Loan, LoanRepayment, LoanRepaymentSchedule, LoanProductType, LoanPlan, Borrower, SavingStatement. Each array should contain objects mapping model field names to values. Example output: {{'Profile': [{{...}}, ...], 'Member': [{{...}}, ...], ...}}

    SQL DATA:
    {sql_data}
    """
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(data), timeout=60)
        response.raise_for_status()
        try:
            # Try to parse the full response as JSON and return it for inspection
            gemini_result = response.json()
            return JsonResponse({'success': False, 'error': 'Full Gemini API JSON response', 'response': gemini_result}, status=200)
        except Exception as json_ex:
            # If not JSON, return the full raw text
            return JsonResponse({'success': False, 'error': f'Gemini API non-JSON response (status {response.status_code}):', 'response': response.text}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Gemini API error: {str(e)}'}, status=500)


    model_classes = {
        'Profile': Profile,
        'Member': Member,
        'Saving': Saving,
        'Loan': Loan,
        'LoanRepayment': LoanRepayment,
        'LoanRepaymentSchedule': LoanRepaymentSchedule,
        'LoanProductType': LoanProductType,
        'LoanPlan': LoanPlan,
        'Borrower': Borrower,
        'Loan': Loan,
        'SavingStatement': SavingStatement,
    }
    results = {}
    for model_name, model_class in model_classes.items():
        items = model_data.get(model_name, [])
        created = 0
        for item in items:
            try:
                # Remove PK if present
                item.pop('id', None)
                # Foreign keys: convert from string/ID to object if needed (basic handling)
                for field in model_class._meta.fields:
                    if isinstance(field, models.ForeignKey):
                        fk_name = field.name
                        if fk_name in item and item[fk_name]:
                            rel_model = field.related_model
                            try:
                                item[fk_name] = rel_model.objects.get(pk=item[fk_name])
                            except Exception:
                                item.pop(fk_name)
                model_class.objects.create(**item)
                created += 1
            except Exception as ex:
                continue  # Optionally, collect errors
        results[model_name] = created
    return JsonResponse({'success': True, 'imported': results})

@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def upload_sql_view(request):
    role=Profile.objects.get(user=request.user).type
    member_count = Member.objects.count()
    message = None
    if request.method == "POST":
        sql_data = request.POST.get('sql_data', '')
        sql_file = request.FILES.get('sql_file')
        if sql_file:
            try:
                sql_data = sql_file.read().decode('utf-8')
            except Exception as ex:
                message = f"Could not read uploaded file: {str(ex)}"
                return render(request, 'upload_sql.html', {'member_count': member_count, 'message': message})
        if not sql_data.strip():
            message = 'No SQL data provided.'
        else:
            from django.test import RequestFactory
            factory = RequestFactory()
            fake_post = factory.post('/process-sql/', {'sql_data': sql_data})
            fake_post.user = request.user
            resp = process_sql_data_view(fake_post)
            try:
                result = json.loads(resp.content)
                if result.get('success'):
                    member_count = Member.objects.count()
                    message = f"Import successful! Imported: {result.get('imported', {})}"
                else:
                    message = f"Error: {result.get('error', 'Unknown error')}"
            except Exception as ex:
                message = f"Processing error: {str(ex)}"
    return render(request, 'upload_sql.html', {'member_count': member_count, 'message': message, 'role': role})

@require_GET
def loan_schedule(request):
    from django.shortcuts import render
    amount = request.GET.get('amount', '0')
    try:
        principal = Decimal(amount)
    except InvalidOperation:
        principal = Decimal('0.00')
    plan_id = request.GET.get('plan_id')
    due_date = request.GET.get('due_date')
    ref_number = request.GET.get('ref_number')
    from .models import LoanPlan
    try:
        plan = LoanPlan.objects.get(id=plan_id)
    except LoanPlan.DoesNotExist:
        return render(request, 'partials/loan_schedule_table.html', {'schedule': [], 'error': 'Invalid loan plan.'})
    months = plan.duration_months
    rate = plan.interest_rate / Decimal('100')
    schedule = []
    if months > 0 and principal > 0:
        monthly_interest = principal * rate / months
        monthly_payment = (principal + (principal * rate)) / months
        for i in range(1, months + 1):
            schedule.append({
                'month': i,
                'due_date': '',
                'principal': round(principal / months, 2),
                'interest': round(monthly_interest, 2),
                'total': round(monthly_payment, 2),
            })
    return render(request, 'partials/loan_schedule_table.html', {'schedule': schedule, 'error': None})

@require_GET
def loan_schedule_pdf(request):
    amount = request.GET.get('amount', '0')
    try:
        principal = Decimal(amount)
    except InvalidOperation:
        principal = Decimal('0.00')
    plan_id = request.GET.get('plan_id')
    due_date = request.GET.get('due_date')
    ref_number = request.GET.get('ref_number')
    from .models import LoanPlan
    try:
        plan = LoanPlan.objects.get(id=plan_id)
    except LoanPlan.DoesNotExist:
        from django.http import HttpResponse
        return HttpResponse('Invalid loan plan.', content_type='text/plain')
    months = plan.duration_months
    rate = plan.interest_rate / Decimal('100')
    schedule = []
    if months > 0 and principal > 0:
        monthly_interest = principal * rate / months
        monthly_payment = (principal + (principal * rate)) / months
        for i in range(1, months + 1):
            schedule.append({
                'month': i,
                'due_date': '',
                'principal': round(principal / months, 2),
                'interest': round(monthly_interest, 2),
                'total': round(monthly_payment, 2),
            })
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    import weasyprint
    html = render_to_string('partials/loan_schedule_table_pdf.html', {'schedule': schedule, 'plan': plan, 'amount': principal})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="loan_schedule.pdf"'
    weasyprint.HTML(string=html).write_pdf(response)
    return response

@login_required
def next_of_kin_manage(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    NextOfKinFormSet = inlineformset_factory(Member, NextOfKin, form=NextOfKinForm, extra=1, can_delete=True)
    if request.method == 'POST':
        formset = NextOfKinFormSet(request.POST, instance=member)
        if formset.is_valid():
            formset.save()
            return redirect('members-list')
    else:
        formset = NextOfKinFormSet(instance=member)
    return render(request, 'next_of_kin_form.html', {'formset': formset, 'member': member})

@csrf_exempt
@login_required
def add_source_of_income(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            source, created = SourceOfIncome.objects.get_or_create(name=name)
            return JsonResponse({'id': source.id, 'name': source.name, 'created': created})
        else:
            return JsonResponse({'error': 'Name required'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def settings_page(request):
    role=Profile.objects.get(user=request.user).type
    sources = SourceOfIncome.objects.all().order_by('name')
    return render(request, 'settings.html', {'sources': sources, 'role': role})

@csrf_exempt
@login_required
def update_source_of_income(request):
    if request.method == 'POST':
        source_id = request.POST.get('id')
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'error': 'Name required'}, status=400)
        source = SourceOfIncome.objects.filter(id=source_id).first()
        if not source:
            return JsonResponse({'error': 'Source not found'}, status=404)
        source.name = name
        source.save()
        return JsonResponse({'id': source.id, 'name': source.name})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
def delete_source_of_income(request):
    if request.method == 'POST':
        source_id = request.POST.get('id')
        source = SourceOfIncome.objects.filter(id=source_id).first()
        if not source:
            return JsonResponse({'error': 'Source not found'}, status=404)
        source.delete()
        return JsonResponse({'deleted': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@require_POST
def saving_edit_type(request, id):
    print(f"Received request to edit saving with ID: {id}")  # Debugging line
    print(f"Request POST data: {request.POST}")  # Debugging line

    saving_statement = get_object_or_404(SavingStatement, id=id)
    print(f"Found saving statement: {saving_statement}")  # Debugging line
    new_deposit_type = request.POST.get('savings_type')
    saving_statement.deposit_type = new_deposit_type
    saving_statement.save()
    print(f"Updated saving deposit type to: {new_deposit_type}")  # Debugging line
    
    return JsonResponse({'status': 'success', 'message': 'Deposit type updated successfully.'})