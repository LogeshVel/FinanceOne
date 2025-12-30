from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
import json
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.template.loader import render_to_string
from finance.models import Asset, Retirement, Income, Expense, Loan, Insurance
from .models import Budget, FinancialGoal
from .utils import calculate_projections, calculate_loan_outstanding
from datetime import datetime
from .forms import UserRegistrationForm, BudgetCreationForm, FinancialGoalForm
from datetime import datetime, timezone
import calendar

def format_labels(keys, values):
    total = sum(values)
    if total == 0:
        return keys
    return [f"{k} ({(v/total*100):.1f}%)" for k, v in zip(keys, values)]

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
        'asset_labels': format_labels(list(asset_types.keys()), list(asset_types.values())),
        'asset_values': list(asset_types.values()),
        'incomes': incomes,
        'expenses': expenses,
        'retirements': retirements,
        'zip_assets': zip(list(asset_types.keys()), list(asset_types.values())),
        'income_chart_labels': format_labels(list(income_cats.keys()), list(income_cats.values())),
        'income_chart_values': list(income_cats.values()),
        'total_current_income': current_year_income,
        'expense_chart_labels': format_labels(list(expense_cats.keys()), list(expense_cats.values())),
        'expense_chart_values': list(expense_cats.values()),
        'total_current_expense': current_year_expense,
        
        # New Definitions
        'total_annual_emi': round(total_annual_emi, 2),
        'loan_chart_labels': format_labels(list(loan_cats.keys()), list(loan_cats.values())),
        'loan_chart_values': list(loan_cats.values()),
        
        'total_annual_premium': round(total_annual_premium, 2),
        'insurance_chart_labels': format_labels(list(insurance_cats.keys()), list(insurance_cats.values())),
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
    current_month = datetime.now().month
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
            
    # Category Pie Chart Data (Yearly & Monthly specific context)
    # Refined logic: Both charts should respect the table filter scope.
    selected_year = request.GET.get('year')
    if selected_year is None:
        selected_year = str(current_year)
    
    selected_month = request.GET.get('month')
    if selected_month is None:
        selected_month = str(current_month)

    # Determine display titles
    target_year_display = selected_year if selected_year != 'all' else "All Time"
    
    if selected_month != 'all':
        target_month_display = calendar.month_name[int(selected_month)]
        if selected_year != 'all':
             target_month_display = f"{target_month_display} {selected_year}"
        else:
             target_month_display = f"All {target_month_display}s" # e.g. "All Januarys"
    else:
        target_month_display = "All Months"
        if selected_year != 'all':
             target_month_display = f"All Months ({selected_year})"
        else:
             target_month_display = "All Time"

    # Determine filter constraints for Aggregation
    filter_year = int(selected_year) if selected_year != 'all' else None
    filter_month = int(selected_month) if selected_month != 'all' else None
    
    yearly_pie_cats = {}
    monthly_pie_cats = {}
    
    for e in all_expenses:
        amount = float(e.amount)
        
        # Yearly Pie Logic: 
        # Context is the Year selector.
        if filter_year is None or e.date.year == filter_year:
            yearly_pie_cats[e.category] = yearly_pie_cats.get(e.category, 0) + amount
            
        # Monthly Pie Logic:
        # Context is Year selector + Month selector.
        match_year = (filter_year is None or e.date.year == filter_year)
        match_month = (filter_month is None or e.date.month == filter_month)
        
        if match_year and match_month:
             monthly_pie_cats[e.category] = monthly_pie_cats.get(e.category, 0) + amount
                
    yearly_pie_labels = format_labels(list(yearly_pie_cats.keys()), list(yearly_pie_cats.values()))
    yearly_pie_values = list(yearly_pie_cats.values())
    
    monthly_pie_labels = format_labels(list(monthly_pie_cats.keys()), list(monthly_pie_cats.values()))
    monthly_pie_values = list(monthly_pie_cats.values())
            
    highest_category = max(cats, key=cats.get) if cats else "None"
    
    # Daily Average
    day_of_year = datetime.now().timetuple().tm_yday
    daily_avg = round(current_year_total / day_of_year, 2) if day_of_year > 0 else 0
    
    # Filtering for Table
    expenses = all_expenses
    
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
        'target_year_display': target_year_display,
        'target_month_display': target_month_display,
        'yearly_pie_labels': yearly_pie_labels,
        'yearly_pie_values': yearly_pie_values,
        'monthly_pie_labels': monthly_pie_labels,
        'monthly_pie_values': monthly_pie_values,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        table_html = render_to_string('partials/expense_list.html', context)
        return JsonResponse({
            'table_html': table_html,
            'yearly_pie_labels': yearly_pie_labels,
            'yearly_pie_values': yearly_pie_values,
            'monthly_pie_labels': monthly_pie_labels,
            'monthly_pie_values': monthly_pie_values,
            'target_year_display': target_year_display,
            'target_month_display': target_month_display
        })

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
        'chart_labels': format_labels(list(type_alloc.keys()), list(type_alloc.values())),
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

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        table_html = render_to_string('partials/loan_list.html', context)
        return JsonResponse({
            'table_html': table_html,
            'total_loan_amount': total_loan_amount,
            'total_outstanding_amount': round(total_outstanding_amount, 2),
            'total_monthly_emi': round(total_monthly_emi, 2)
        })

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

@login_required
def budget_page(request):
    user = request.user
    
    # Handle Budget Creation
    if request.method == 'POST' and 'create_budget' in request.POST:
        form = BudgetCreationForm(user, request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = user
            budget.save()
            
            # Handle Copy/Clone
            copy_from_id = request.POST.get('copy_from')
            if copy_from_id:
                try:
                    source_budget = Budget.objects.get(id=copy_from_id, user=user)
                    budget.copy_from(source_budget)
                except Budget.DoesNotExist:
                    pass
            
            budget.activate()
            # Redirect to Monthly Edit Mode
            return redirect(f"{reverse('budget')}?mode=edit_monthly")

    # Handle Budget Updates (Monthly/Yearly)
    active_budget = Budget.objects.filter(user=user, is_active=True).first()
    
    if request.method == 'POST' and active_budget:
        if 'update_monthly' in request.POST:
            active_budget.monthly_income = request.POST.get('monthly_income', 0)
            
            # Process Dynamic Fields
            # Helper to extract key-value pairs from POST starting with specific prefix
            def extract_pairs(prefix):
                data = {}
                keys = request.POST.getlist(f'{prefix}_key[]')
                values = request.POST.getlist(f'{prefix}_value[]')
                for k, v in zip(keys, values):
                    if k and v:
                        data[k] = float(v)
                return data

            active_budget.fixed_expenses = extract_pairs('fixed')
            active_budget.variable_expenses = extract_pairs('variable')
            active_budget.savings_investments = extract_pairs('savings')
            active_budget.save()
            # Redirect to Yearly Edit Mode
            return redirect(f"{reverse('budget')}?mode=edit_yearly")

        if 'update_yearly' in request.POST:
            active_budget.yearly_income = request.POST.get('yearly_income', 0)
            
            def extract_pairs(prefix):
                data = {}
                keys = request.POST.getlist(f'{prefix}_key[]')
                values = request.POST.getlist(f'{prefix}_value[]')
                for k, v in zip(keys, values):
                    if k and v:
                        data[k] = float(v)
                return data

            active_budget.annual_costs = extract_pairs('annual')
            active_budget.save()
            return redirect('budget')


    creation_form = BudgetCreationForm(user=user)
    inactive_budgets = Budget.objects.filter(user=user, is_active=False).order_by('-updated_at')
    
    # Calculations for View
    monthly_data = {}
    yearly_data = {}
    
    if active_budget:
        # Monthly Calc
        m_income = float(active_budget.monthly_income)
        m_fixed = sum(float(v) for v in active_budget.fixed_expenses.values())
        m_variable = sum(float(v) for v in active_budget.variable_expenses.values())
        m_savings = sum(float(v) for v in active_budget.savings_investments.values())
        m_total_expense = m_fixed + m_variable + m_savings
        m_balance = m_income - m_total_expense
        
        monthly_data = {
            'income': m_income,
            'fixed_total': m_fixed,
            'variable_total': m_variable,
            'savings_total': m_savings,
            'total_expense': m_total_expense,
            'balance': m_balance,
            'is_surplus': m_balance > 0
        }
        
        # Yearly Calc
        y_income = float(active_budget.yearly_income)
        # Yearly Expenses = Monthly Expenses * 12
        y_monthly_expenses = (m_fixed + m_variable + m_savings) * 12
        y_annual_costs = sum(float(v) for v in active_budget.annual_costs.values())
        y_total_expense = y_monthly_expenses + y_annual_costs
        y_balance = y_income - y_total_expense
        
        yearly_data = {
            'income': y_income,
            'monthly_expenses_annualized': y_monthly_expenses,
            'annual_costs_total': y_annual_costs,
            'total_expense': y_total_expense,
            'balance': y_balance,
            'is_surplus': y_balance > 0
        }

    context = {
        'active_budget': active_budget,
        'inactive_budgets': inactive_budgets,
        'creation_form': creation_form,
        'monthly_data': monthly_data,
        'yearly_data': yearly_data,
        'monthly_budget_labels': format_labels(['Fixed', 'Variable', 'Savings'], [monthly_data.get('fixed_total', 0), monthly_data.get('variable_total', 0), monthly_data.get('savings_total', 0)]) if active_budget else [],
        'mode': request.GET.get('mode', '')
    }
    return render(request, 'budget.html', context)

@login_required
def activate_budget(request, id):
    budget = get_object_or_404(Budget, id=id, user=request.user)
    budget.activate()
    return redirect('budget')

@login_required
def delete_budget(request, id):
    budget = get_object_or_404(Budget, id=id, user=request.user)
    budget.delete()
    return redirect('budget')

@login_required
def get_budget_details(request, id):
    budget = get_object_or_404(Budget, id=id, user=request.user)
    
    # Calculate Totals
    m_fixed = sum(float(v) for v in budget.fixed_expenses.values())
    m_variable = sum(float(v) for v in budget.variable_expenses.values())
    m_savings = sum(float(v) for v in budget.savings_investments.values())
    m_total = m_fixed + m_variable + m_savings
    
    y_income = float(budget.yearly_income)
    y_annual_costs = sum(float(v) for v in budget.annual_costs.values())
    y_total = (m_total * 12) + y_annual_costs
    
    data = {
        'name': budget.name,
        'monthly_income': float(budget.monthly_income),
        'fixed_expenses': budget.fixed_expenses,
        'variable_expenses': budget.variable_expenses,
        'savings_investments': budget.savings_investments,
        'yearly_income': y_income,
        'annual_costs': budget.annual_costs,
        'monthly_total': m_total,
        'yearly_total': y_total,
        'monthly_balance': float(budget.monthly_income) - m_total,
        'yearly_balance': y_income - y_total
    }
    return JsonResponse(data)

@login_required
def delete_goal(request, id):
    goal = get_object_or_404(FinancialGoal, id=id, user=request.user)
    goal.delete()
    return redirect('goals')

@login_required
def goals_page(request):
    if request.method == 'POST':
        goal_id = request.POST.get('goal_id')
        if goal_id:
            goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)
            form = FinancialGoalForm(request.POST, instance=goal)
        else:
            form = FinancialGoalForm(request.POST)
            
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('goals')
    else:
        form = FinancialGoalForm()
    
    goals = FinancialGoal.objects.filter(user=request.user).order_by('target_date')
    
    context = {
        'immediate_goals': goals.filter(category='IMMEDIATE'),
        'short_goals': goals.filter(category='SHORT'),
        'medium_goals': goals.filter(category='MEDIUM'),
        'long_goals': goals.filter(category='LONG'),
        'form': form
    }
    return render(request, 'goals.html', context)

