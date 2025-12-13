"""
Check all statuses in database for this contractor
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from app.models import InvoiceSummary, User
from app.extensions import db

app = create_app()
with app.app_context():
    # Find user
    user = User.query.filter_by(username='70583_100').first()
    if not user:
        print("User not found")
        exit(1)
    
    print(f"User: {user.username}")
    if user.contractor:
        print(f"Contractor: detail_code={user.contractor.detail_code}, supplier_code={user.contractor.supplier_code}")
        
        # Get all summaries for this contractor
        query = InvoiceSummary.query.filter_by(detail_code=user.contractor.detail_code)
        if user.contractor.supplier_code:
            query = query.filter(
                (InvoiceSummary.supplier_code == user.contractor.supplier_code) |
                (InvoiceSummary.supplier_code.is_(None))
            )
        
        all_summaries = query.all()
        print(f"\nTotal summaries: {len(all_summaries)}")
        
        # Get all unique statuses
        statuses = {}
        for summary in all_summaries:
            status = summary.invoice_status
            if status:
                if status not in statuses:
                    statuses[status] = []
                statuses[status].append(summary.cover_number)
        
        print(f"\nUnique statuses found: {len(statuses)}")
        for status, cover_numbers in statuses.items():
            print(f"  - {status}: {len(cover_numbers)} invoices")
            print(f"    Sample cover numbers: {cover_numbers[:5]}")
        
        # Check for fiscal year 1404
        print("\n" + "="*50)
        print("Checking fiscal year 1404:")
        print("="*50)
        from convertdate import persian
        from datetime import date
        g_year_start, g_month_start, g_day_start = persian.to_gregorian(1404, 1, 1)
        try:
            g_year_end, g_month_end, g_day_end = persian.to_gregorian(1404, 12, 30)
        except:
            g_year_end, g_month_end, g_day_end = persian.to_gregorian(1404, 12, 29)
        
        start_date = date(g_year_start, g_month_start, g_day_start)
        end_date = date(g_year_end, g_month_end, g_day_end)
        
        fiscal_1404_query = query.filter(
            InvoiceSummary.invoice_date >= start_date,
            InvoiceSummary.invoice_date <= end_date
        )
        fiscal_1404_summaries = fiscal_1404_query.all()
        print(f"Summaries in fiscal year 1404: {len(fiscal_1404_summaries)}")
        
        fiscal_1404_statuses = {}
        for summary in fiscal_1404_summaries:
            status = summary.invoice_status
            if status:
                if status not in fiscal_1404_statuses:
                    fiscal_1404_statuses[status] = []
                fiscal_1404_statuses[status].append(summary.cover_number)
        
        print(f"Unique statuses in fiscal year 1404: {len(fiscal_1404_statuses)}")
        for status, cover_numbers in fiscal_1404_statuses.items():
            print(f"  - {status}: {len(cover_numbers)} invoices")
    else:
        print("User has no contractor")

