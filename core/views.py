from django.shortcuts import render, redirect
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from finance.models import Asset, Retirement, Income, Expense, Loan, Insurance
from .utils import calculate_projections, calculate_loan_outstanding
from datetime import datetime
from .forms import UserRegistrationForm
from datetime import datetime, timezone
import calendar

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def dashboard_view(request):
    user = request.user
    
    # Fetch Data
    incomes = Income.objects.filter(user=user, status='Active')
    expenses = Expense.objects.filter(user=user)
    assets = Asset.objects.filter(user=user)
    retirements = Retirement.objects.filter(user=user)
    
    # Calculations
    total_assets = round(sum(a.quantity * a.current_price for a in assets), 2)
    total_retirement = round(sum(r.balance for r in retirements), 2)
    net_worth = round(total_assets + total_retirement, 2)
    
    # Projections
    # Projections (Extended for 5Y view)
    projections = calculate_projections(user, assets, retirements, incomes, expenses)
    projection_labels = [p['year'] for p in projections]
    projection_values = [p['value'] for p in projections]
    
    # Net Worth Change Calculation - REMOVED per user request (requires historical snapshots)
    net_worth_change = 0 
    
    # Asset Allocation
    # Income Categories (Annualized)
    income_cats = {}
    current_year_income = 0
    for inc in incomes:
        yearly_amt = 0
        val = float(inc.amount)
        if inc.frequency == 'Monthly': yearly_amt = val * 12
        elif inc.frequency == 'Yearly': yearly_amt = val
        elif inc.frequency == 'Quarterly': yearly_amt = val * 4
        
        income_cats[inc.type] = income_cats.get(inc.type, 0) + yearly_amt
        current_year_income += yearly_amt

    # Expense Categories (Current Year)
    current_year = datetime.now().year
    current_year_expenses = [e for e in expenses if e.date.year == current_year]
    expense_cats = {}
    current_year_expense = 0
    
    for exp in current_year_expenses:
        val = float(exp.amount)
        expense_cats[exp.category] = expense_cats.get(exp.category, 0) + val
        current_year_expense += val
        
    asset_types = {}
    for a in assets:
        val = float(a.quantity * a.current_price)
        asset_types[a.type] = asset_types.get(a.type, 0) + val

    # Loans Calculation (Annual EMI)
    loans = Loan.objects.filter(user=user)
    loan_cats = {}
    total_annual_emi = 0
    for loan in loans:
        # Calculate Monthly EMI
        P = float(loan.amount)
        r = float(loan.interest_rate) / (12 * 100) # Monthly Rate
        n = loan.tenure * 12 # Months
        
        if r > 0 and n > 0:
            emi = (P * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)
        else:
            emi = 0 if n > 0 else P
            
        annual_emi = emi * 12
        loan_cats[loan.loan_type] = loan_cats.get(loan.loan_type, 0) + annual_emi
        total_annual_emi += annual_emi
        
    # Insurance Calculation (Annual Premium)
    insurances = Insurance.objects.filter(user=user, status='Active')
    insurance_cats = {}
    total_annual_premium = 0
    for ins in insurances:
        val = float(ins.premium)
        annual_amt = 0
        if ins.premium_frequency == 'Monthly': annual_amt = val * 12
        elif ins.premium_frequency == 'Yearly': annual_amt = val
        elif ins.premium_frequency == 'Quarterly': annual_amt = val * 4
        
        insurance_cats[ins.type] = insurance_cats.get(ins.type, 0) + annual_amt
        total_annual_premium += annual_amt
    
    # Real Net Worth Calculation
    # 1. Total Outstanding Loans
    total_outstanding_loans = 0
    loans = Loan.objects.filter(user=user)
    for loan in loans:
        total_outstanding_loans += calculate_loan_outstanding(loan)
        
    # 2. Monthly Cashflow (Income - Expense for current Month)
    today = datetime.now().date()
    
    # Income is stored as "sources", so we assume the total of all active sources contributes to monthly income.
    # We must normalize based on frequency.
    active_incomes = Income.objects.filter(user=user, status='Active')
    total_monthly_income = 0
    for inc in active_incomes:
        val = float(inc.amount)
        if inc.frequency == 'Monthly':
            total_monthly_income += val
        elif inc.frequency == 'Yearly':
            total_monthly_income += val / 12
        elif inc.frequency == 'Quarterly':
            total_monthly_income += val / 3
            
    # Expense is transactional, so we filter by current month.
    current_month_expenses = Expense.objects.filter(user=user, date__year=today.year, date__month=today.month)
    total_monthly_expense = sum(float(e.amount) for e in current_month_expenses)
    
    monthly_cashflow = total_monthly_income - total_monthly_expense
    
    # 3. Property Resale Value
    total_resale_value = 0
    for loan in loans:
        if loan.is_property_loan:
            total_resale_value += float(loan.resale_value)

    # Formula: Assets + Retirement - Outstanding Loans + Resale Value + Cashflow
    real_net_worth = float(total_assets) + float(total_retirement) - float(total_outstanding_loans) + float(total_resale_value) + float(monthly_cashflow)

    context = {
        'net_worth': net_worth,
        'net_worth_change': net_worth_change if net_worth_change else 0,
        'real_net_worth': round(real_net_worth, 2),
        'total_outstanding_loans': round(total_outstanding_loans, 2),
        'total_resale_value': round(total_resale_value, 2),
        'monthly_cashflow': round(monthly_cashflow, 2),
        'total_assets': total_assets,
        'total_retirement': total_retirement,
        'projection_labels': projection_labels,
        'projection_values': projection_values,
        'asset_labels': list(asset_types.keys()),
        'asset_values': list(asset_types.values()),
        'incomes': incomes,
        'expenses': expenses,
        'retirements': retirements,
        'zip_assets': zip(list(asset_types.keys()), list(asset_types.values())),
        'income_chart_labels': list(income_cats.keys()),
        'income_chart_values': list(income_cats.values()),
        'total_current_income': current_year_income,
        'expense_chart_labels': list(expense_cats.keys()),
        'expense_chart_values': list(expense_cats.values()),
        'total_current_expense': current_year_expense,
        
        # New Definitions
        'total_annual_emi': round(total_annual_emi, 2),
        'loan_chart_labels': list(loan_cats.keys()),
        'loan_chart_values': list(loan_cats.values()),
        
        'total_annual_premium': round(total_annual_premium, 2),
        'insurance_chart_labels': list(insurance_cats.keys()),
        'insurance_chart_values': list(insurance_cats.values()),
    }
    return render(request, 'dashboard.html', context)

@login_required
def retirement_view(request):
    user = request.user
    
    if request.method == 'POST':
        Retirement.objects.create(
            user=user,
            account_type=request.POST.get('account_type'),
            provider=request.POST.get('provider'),
            balance=request.POST.get('balance'),
            monthly_contribution=request.POST.get('monthly_contribution'),
            return_rate=request.POST.get('return_rate', 7.00)
        )
        return redirect('retirement')
        
    retirements = Retirement.objects.filter(user=user)
    total_corpus = sum(r.balance for r in retirements)
    
    # Calculate Weighted Average Return for "Growth vs Last Year" proxy
    weighted_growth = 0
    if total_corpus > 0:
        weighted_income = sum(r.balance * r.return_rate for r in retirements)
        weighted_growth = round(float(weighted_income / total_corpus), 2)
    else:
        weighted_growth = 7.0 # Default fallback
        
    # Total Monthly Contribution
    total_contribution = sum(r.monthly_contribution for r in retirements)
        
    context = {
        'corpus': total_corpus,
        'growth_pct': weighted_growth,
        'total_contribution': total_contribution,
        'retirements': retirements,
    }
    return render(request, 'retirement.html', context)

@login_required
def income_view(request):
    user = request.user

    if request.method == 'POST':
        Income.objects.create(
            user=user,
            source_name=request.POST.get('source_name'),
            type=request.POST.get('type'),
            frequency=request.POST.get('frequency'),
            amount=request.POST.get('amount')
        )
    
    incomes = Income.objects.filter(user=user)
    active_incomes = incomes.filter(status='Active')
    
    # Simple totals
    monthly_total = 0
    for inc in active_incomes:
        val = float(inc.amount)
        if inc.frequency == 'Monthly': monthly_total += val
        elif inc.frequency == 'Yearly': monthly_total += val / 12
        
    context = {
        'incomes': incomes,
        'monthly_total': monthly_total,
        'yearly_total': monthly_total * 12,
        'active_count': active_incomes.count(),
        'inactive_count': incomes.count() - active_incomes.count()
    }
    return render(request, 'income.html', context)

@login_required
def expense_view(request):
    user = request.user

    if request.method == 'POST':
        Expense.objects.create(
            user=user,
            description=request.POST.get('description'),
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            date=request.POST.get('date'),
        )
    
    # Base Query
    all_expenses = Expense.objects.filter(user=user).order_by('-date')
    
    # Global Metrics Calculation (using all_expenses)
    total_spend = sum(e.amount for e in all_expenses)
    
    # Category calculation & Current Year Total
    cats = {}
    yearly_data = {}
    monthly_data = {i: 0 for i in range(1, 13)}
    
    current_year = datetime.now().year
    current_year_total = 0
    
    for e in all_expenses:
        # Category
        cats[e.category] = cats.get(e.category, 0) + float(e.amount)
        
        # Yearly Data
        year = e.date.year
        yearly_data[year] = yearly_data.get(year, 0) + float(e.amount)
        
        # Monthly Data (Current Year)
        if year == current_year:
            current_year_total += float(e.amount)
            monthly_data[e.date.month] += float(e.amount)
            
    # Prepare Chart Data
    yearly_labels = sorted(yearly_data.keys())
    yearly_values = [yearly_data[y] for y in yearly_labels]
    
    # Prepare Chart Data
    yearly_labels = sorted(yearly_data.keys())
    yearly_values = [yearly_data[y] for y in yearly_labels]
    
    monthly_labels = [calendar.month_name[i] for i in range(1, 13)]
    monthly_values = [monthly_data[i] for i in range(1, 13)]
            
    highest_category = max(cats, key=cats.get) if cats else "None"
    
    # Daily Average
    day_of_year = datetime.now().timetuple().tm_yday
    daily_avg = round(current_year_total / day_of_year, 2) if day_of_year > 0 else 0
    
    # Filtering for Table
    expenses = all_expenses
    selected_year = request.GET.get('year')
    selected_month = request.GET.get('month')
    
    if selected_year and selected_year != 'all':
        expenses = expenses.filter(date__year=selected_year)
    
    if selected_month and selected_month != 'all':
        expenses = expenses.filter(date__month=selected_month)
        
    # Available Years for Dropdown
    available_years = sorted(list(set(e.date.year for e in all_expenses)), reverse=True)
    
    context = {
        'expenses': expenses,
        'total_spend': total_spend,
        'current_year_total': current_year_total,
        'highest_category': highest_category,
        'daily_avg': daily_avg,
        'available_years': available_years,
        'selected_year': int(selected_year) if selected_year and selected_year != 'all' else None,
        'selected_month': int(selected_month) if selected_month and selected_month != 'all' else None,
        'yearly_labels': yearly_labels,
        'yearly_values': yearly_values,
        'monthly_labels': monthly_labels,
        'monthly_values': monthly_values,
        'current_year': current_year,
    }

    return render(request, 'expense.html', context)

@login_required
def assets_view(request):
    user = request.user

    if request.method == 'POST':
        Asset.objects.create(
            user=user,
            name=request.POST.get('name'),
            ticker=request.POST.get('ticker'),
            type=request.POST.get('type'),
            quantity=request.POST.get('quantity'),
            buy_price=request.POST.get('buy_price'),
            current_price=request.POST.get('current_price')
        )

    assets = Asset.objects.filter(user=user)
    
    # Enrich for template
    asset_list = []
    total_val = 0
    total_inv = 0
    type_alloc = {}
    
    for a in assets:
        val = float(a.quantity * a.current_price)
        inv = float(a.quantity * a.buy_price)
        total_val += val
        total_inv += inv
        type_alloc[a.type] = type_alloc.get(a.type, 0) + val
        
        a.total_val = val
        asset_list.append(a)
        
    total_pl = total_val - total_inv
    pl_percent = round((total_pl / total_inv * 100), 2) if total_inv > 0 else 0
    
    context = {
        'assets': asset_list,
        'total_value': total_val,
        'total_invested': total_inv,
        'total_pl': total_pl,
        'total_pl_abs': abs(total_pl),
        'pl_percent': pl_percent,
        'chart_labels': list(type_alloc.keys()),
        'chart_values': list(type_alloc.values())
    }
    return render(request, 'assets.html', context)

@login_required
def insurance_view(request):
    user = request.user

    if request.method == 'POST':
        Insurance.objects.create(
            user=user,
            provider=request.POST.get('provider'),
            type=request.POST.get('type'),
            policy_number=request.POST.get('policy_number'),
            premium=request.POST.get('premium'),
            renewal_date=request.POST.get('renewal_date')
        )
        
    insurance_list = Insurance.objects.filter(user=user)
    return render(request, 'insurance.html', {'insurance_list': insurance_list})

@login_required
def loans_view(request):
    user = request.user

    if request.method == 'POST':
        is_property_loan = request.POST.get('is_property_loan') == 'on'
        resale_val = request.POST.get('resale_value', 0)
        
        Loan.objects.create(
            user=user,
            lender_name=request.POST.get('lender_name'),
            amount=request.POST.get('amount'),
            tenure=request.POST.get('tenure'),
            interest_rate=request.POST.get('interest_rate'),
            loan_type=request.POST.get('loan_type'),
            start_date=request.POST.get('start_date') if request.POST.get('start_date') else datetime.now().date(),
            is_property_loan=is_property_loan,
            resale_value=resale_val if is_property_loan else 0
        )

    # Base Query
    loans = Loan.objects.filter(user=user)

    # Filtering
    loan_type_filter = request.GET.get('type')
    if loan_type_filter and loan_type_filter != 'all':
        loans = loans.filter(loan_type=loan_type_filter)

    # Sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'amount_high':
        loans = loans.order_by('-amount')
    elif sort_by == 'amount_low':
        loans = loans.order_by('amount')
    else:
        loans = loans.order_by('-created_at') # Default sort

    # EMI Calculation and Totals
    total_loan_amount = 0
    total_monthly_emi = 0
    total_outstanding_amount = 0
    
    loan_list = []
    
    current_date = datetime.now().date()
    
    for loan in loans:
        P = float(loan.amount)
        r = float(loan.interest_rate) / (12 * 100)
        n = loan.tenure * 12
        
        # EMI Calculation
        if r > 0 and n > 0:
            emi = (P * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)
        else:
            emi = 0 if n > 0 else P
            
        loan.calculated_emi = round(emi, 2)
        
        # Outstanding Amount Calculation
        loan.outstanding_amount = calculate_loan_outstanding(loan)

        total_loan_amount += P
        total_monthly_emi += emi
        total_outstanding_amount += loan.outstanding_amount
        loan_list.append(loan)
        

    loan_types = ['Home', 'Car', 'Bike', 'Personal', 'Education', 'Other']

    context = {
        'loans': loan_list,
        'total_loan_amount': total_loan_amount,
        'total_outstanding_amount': round(total_outstanding_amount, 2),
        'total_monthly_emi': round(total_monthly_emi, 2),
        'loan_types': loan_types,
        'selected_type': loan_type_filter,
        'selected_sort': sort_by,
    }
    return render(request, 'loans.html', context)

@login_required
def delete_income(request, id):
    user = request.user
    try:
        income = Income.objects.get(id=id, user=user)
        income.delete()
    except Income.DoesNotExist:
        pass
    return redirect('income')

@login_required
def delete_expense(request, id):
    user = request.user
    try:
        expense = Expense.objects.get(id=id, user=user)
        expense.delete()
    except Expense.DoesNotExist:
        pass
    return redirect('expense')

@login_required
def delete_loan(request, id):
    user = request.user
    try:
        loan = Loan.objects.get(id=id, user=user)
        loan.delete()
    except Loan.DoesNotExist:
        pass
    return redirect('loans')

@login_required
def delete_insurance(request, id):
    user = request.user
    try:
        insurance = Insurance.objects.get(id=id, user=user)
        insurance.delete()
    except Insurance.DoesNotExist:
        pass
    return redirect('insurance')

@login_required
def delete_retirement(request, id):
    user = request.user
    try:
        retirement = Retirement.objects.get(id=id, user=user)
        retirement.delete()
    except Retirement.DoesNotExist:
        pass
    return redirect('retirement')

@login_required
def delete_asset(request, id):
    user = request.user
    try:
        asset = Asset.objects.get(id=id, user=user)
        asset.delete()
    except Asset.DoesNotExist:
        pass
    return redirect('assets')
