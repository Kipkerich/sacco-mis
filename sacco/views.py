from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile, Member, Saving, Loan, LoanRepayment, Borrower, LoanPlan, LoanProductType
from .forms import MemberForm, SavingForm, LoanForm, LoanRepaymentForm
from django.db.models import Sum
from django.http import JsonResponse
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
        return redirect('login-url')
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
    })

@login_required
def users_view(request):
    users = User.objects.all()
    profiles = Profile.objects.all()
    return render(request, 'users.html', {'users': users, 'profiles': profiles})

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
    return render(request, 'members.html', {'members_data': members_data})

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
    member = get_object_or_404(Member, id=id)
    return render(request, 'member_detail.html', {'member': member})

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
    return render(request, 'savings.html', {'members_savings': members_savings, 'members': members})

@login_required
def saving_add(request):
    if request.method == 'POST':
        form = SavingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('savings')
    else:
        form = SavingForm()
    return render(request, 'member_form.html', {'form': form, 'action': 'Add Saving'})

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

# Loans Views
@login_required
def loans_list(request):
    loans = Loan.objects.select_related('member', 'loan_plan').all()
    loan_plans = LoanPlan.objects.all()
    return render(request, 'loans.html', {'loans': loans, 'loan_plans': loan_plans})

@login_required
def loan_add(request):
    if request.method == 'POST':
        ref_number = request.POST.get('ref_number')
        amount = request.POST.get('amount')
        status = request.POST.get('status')
        due_date = request.POST.get('due_date')
        loan_plan_id = request.POST.get('loan_plan')
        member = Member.objects.filter(membership_number=ref_number).first()
        loan_plan = LoanPlan.objects.filter(id=loan_plan_id).first() if loan_plan_id else None
        if member and amount and due_date and loan_plan:
            Loan.objects.create(
                member=member,
                amount=amount,
                status=status,
                due_date=due_date,
                loan_plan=loan_plan
            )
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
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = loan.repayments.order_by('-date')
    return render(request, 'loan_detail.html', {'loan': loan, 'repayments': repayments})

# Loan Repayment
@login_required
def loan_repayment(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = LoanRepayment.objects.filter(loan=loan)
    total_repaid = repayments.aggregate(total=models.Sum('amount'))['total'] or 0
    pending = loan.amount - total_repaid
    feedback = None
    if request.method == 'POST':
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
    return render(request, 'loan_repayment.html', {'form': form, 'repayments': repayments, 'pending': pending, 'feedback': feedback})

@login_required
def loan_repayments_list(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = loan.repayments.order_by('-date')
    if request.method == 'POST':
        amount = request.POST.get('amount')
        if amount:
            LoanRepayment.objects.create(loan=loan, amount=amount)
            return redirect('loan-repayments-list', loan_id=loan.id)
    return render(request, 'loan_repayments.html', {'loan': loan, 'repayments': repayments})

# Borrowers Views
@login_required
def borrowers_list(request):
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
    return render(request, 'borrowers.html', {'borrowers_data': borrowers_data, 'members': members})

@login_required
def borrower_add(request):
    if request.method == 'POST':
        member_id = request.POST.get('member')
        if member_id:
            member = Member.objects.get(id=member_id)
            Borrower.objects.create(member=member)
    return redirect('borrowers-url')

# Loan Plans Views
@login_required
def loan_plans_list(request):
    loan_product_types = LoanProductType.objects.all()
    loan_plans = LoanPlan.objects.all().order_by('-date_created')
    return render(request, 'loan_plans.html', {'loan_plans': loan_plans, 'loan_product_types': loan_product_types})

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
    product_types = LoanProductType.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            LoanProductType.objects.create(name=name, description=description)
        return redirect('loan-product-type-list')
    return render(request, 'loan_product_types.html', {'product_types': product_types})

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
    })

@login_required
def repayments_page(request):
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
    return render(request, 'repayments.html', {'loans': loans, 'q': query, 'status': status})

@login_required
@require_http_methods(["GET", "POST"])
def loan_approvals(request):
    if request.method == "POST":
        loan_id = request.POST.get("loan_id")
        action = request.POST.get("action")
        loan = get_object_or_404(Loan, id=loan_id, status="pending")
        if action == "approve":
            loan.status = "approved"
            loan.save()
        elif action == "reject":
            loan.status = "rejected"
            loan.save()
        return redirect("loan-approvals")
    # GET: list all pending loans
    loans = Loan.objects.filter(status="pending").select_related("member", "loan_plan")
    return render(request, "loan_approvals.html", {"loans": loans})

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
