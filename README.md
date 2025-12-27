# FinancialOne

FinancialOne is a comprehensive personal finance dashboard that helps you track your net worth, budgeting, goals, income, expenses, assets, loans, and retirement planning.

## Tech Stack

- **Backend**: Django 5, Python 3.10+, SQLite
- **Frontend**: Django Templates, Tailwind CSS, Chart.js
- **Styling**: Inter Font, Material Symbols

## Features

- **Dashboard**: Real-time overview of Net Worth, Asset Allocation, and Financial Projections.
    - **Real Net Worth**: Calculated as `Assets + Retirement - Outstanding Loans + Property Resale Value + Monthly Cashflow`.
- **Budget Planner**: Comprehensive budgeting tool.
    - **Active/Inactive Budgets**: Create multiple scenarios and activate one.
    - **Monthly & Yearly Views**: Track recurring expenses and annual costs separately.
    - **Copy Functionality**: Clone existing budgets to save time.
    - **Analytics**: "Income vs Expense" visualization.
- **Financial Goals**: Goal setting and tracking.
    - **Categorized Goals**: Immediate, Short, Medium, and Long-term horizons.
    - **Smart Status**: Auto-calculated statuses (New, In Progress, Completed, Overdue).
    - **Visualization**: **Progress bars** and cards with dynamic funding strategies.
- **Income & Expense**:
    - Detailed transaction logging.
    - **Analytics**: Year-wise and Month-wise bar charts for expenses.
- **Assets Management**: Track various asset classes.
- **Loan Management**:
    - Track loans with Amortization schedules.
    - **Outstanding Principal**: Automatically calculated based on interest rate, tenure, and start date.
    - **Property Loans**: Track resale value of underlying assets.
- **Retirement Planning**: Future value projections.
- **Insurance**: Policy tracking.

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

1.  Navigate to the Django project directory:
    ```bash
    cd django_app
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install django pillow numpy
    ```

4.  Apply Database Migrations:
    ```bash
    python manage.py migrate
    ```

5.  Run the Development Server:
    ```bash
    python manage.py runserver
    ```

    The application will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Project Structure

```
django_app/
├── core/                 # Core views, templates, authentication, utilities
├── finance/              # Domain models (Income, Expense, Asset, Loan, etc.)
├── financial_project/    # Project configuration (settings.py, urls.py)
├── templates/            # HTML Templates (Tailwind + Django Template Language)
└── manage.py
```
