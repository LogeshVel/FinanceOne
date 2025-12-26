import numpy as np
from datetime import datetime, timezone

def linear_projection(values, years_ahead=1):
    """Simple linear regression projection"""
    if len(values) < 2:
        return values[-1] if values else 0
    x = np.arange(len(values))
    y = np.array(values)
    slope, intercept = np.polyfit(x, y, 1)
    return float(intercept + slope * (len(values) + years_ahead - 1))

def calculate_projections(user, assets, retirements, incomes, expenses):
    # This logic mirrors the get_projections endpoint in FastAPI
    total_assets = sum(a.quantity * a.current_price for a in assets)
    total_retirement = sum(r.balance for r in retirements)
    current_net_worth = float(total_assets + total_retirement)

    # Monthly savings calculation
    monthly_income = 0
    for inc in incomes:
        if inc.frequency == "Monthly":
            monthly_income += float(inc.amount)
        elif inc.frequency == "Yearly":
            monthly_income += float(inc.amount) / 12
        elif inc.frequency == "Quarterly":
            monthly_income += float(inc.amount) / 3

    monthly_expense = sum(float(e.amount) for e in expenses) / max(1, len(set(e.date.strftime('%Y-%m') for e in expenses)))
    monthly_retirement = sum(float(r.monthly_contribution) for r in retirements)
    
    # Generate 5-year projection
    now = datetime.now(timezone.utc)
    current_year = now.year
    projections = []

    # Historical simulation removed
    # for i in range(5, 0, -1):
    #     year_value = current_net_worth * (0.93 ** i)  # Assume 7% annual growth
    #     projections.append({"year": current_year - i, "value": round(year_value, 2)})

    projections.append({"year": current_year, "value": round(current_net_worth, 2)})

    # Future projection (5 years)
    values = [p["value"] for p in projections]
    for i in range(1, 6):
        projected = linear_projection(values, i) * (1.07 ** i)
        projections.append({"year": current_year + i, "value": round(projected, 2)})
    
    return projections

def calculate_loan_outstanding(loan):
    """
    Calculate outstanding loan amount based on amortization logic.
    Returns: float
    """
    P = float(loan.amount)
    r = float(loan.interest_rate) / (12 * 100)
    n = loan.tenure * 12
    current_date = datetime.now().date()
    
    outstanding = P # Default to full amount
    
    if loan.start_date:
        # Calculate months elapsed
        months_elapsed = (current_date.year - loan.start_date.year) * 12 + (current_date.month - loan.start_date.month)
        
        if months_elapsed > 0:
            if months_elapsed >= n:
                outstanding = 0
            else:
                k = months_elapsed
                if r > 0:
                     balance = P * (((1 + r) ** n) - ((1 + r) ** k)) / (((1 + r) ** n) - 1)
                     outstanding = balance
                else:
                    outstanding = P - (P/n * k)
    
    return round(max(0, outstanding), 2)
