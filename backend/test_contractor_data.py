"""
Test script to investigate contractor data and filter issues
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from app.models import InvoiceSummary, InvoiceDetail, User, Contractor
from app.extensions import db
from convertdate import persian
from datetime import date

app = create_app()
with app.app_context():
    # Find user by username (from the image, it shows "دیزباد (70358)")
    # Let's try to find contractor with detail_code 70358
    contractor = Contractor.query.filter_by(detail_code='70358').first()
    
    if not contractor:
        print("Contractor not found with detail_code 70358")
        # Try to find any contractor
        contractors = Contractor.query.limit(5).all()
        print(f"\nFound {len(contractors)} contractors:")
        for c in contractors:
            print(f"  - detail_code: {c.detail_code}, supplier_code: {c.supplier_code}")
        contractor = contractors[0] if contractors else None
    
    if not contractor:
        print("No contractor found!")
        exit(1)
    
    print(f"\n{'='*60}")
    print(f"Testing Contractor:")
    print(f"  detail_code: {contractor.detail_code}")
    print(f"  supplier_code: {contractor.supplier_code}")
    print(f"{'='*60}\n")
    
    # Test 1: Check summaries with detail_code match
    print("Test 1: Summaries with detail_code match")
    print("-" * 60)
    query1 = InvoiceSummary.query.filter_by(detail_code=contractor.detail_code)
    if contractor.supplier_code:
        query1 = query1.filter(
            (InvoiceSummary.supplier_code == contractor.supplier_code) |
            (InvoiceSummary.supplier_code.is_(None))
        )
    summaries1 = query1.all()
    print(f"Found {len(summaries1)} summaries with detail_code match")
    
    statuses1 = {}
    for s in summaries1:
        status = s.invoice_status or "None"
        if status not in statuses1:
            statuses1[status] = []
        statuses1[status].append(s.cover_number)
    
    print(f"Statuses: {len(statuses1)}")
    for status, covers in statuses1.items():
        print(f"  - {status}: {len(covers)} invoices")
        print(f"    Sample: {covers[:3]}")
    
    # Test 2: Check InvoiceDetail for this contractor
    print(f"\nTest 2: InvoiceDetail records")
    print("-" * 60)
    details_query = InvoiceDetail.query
    if contractor.supplier_code:
        details_query = details_query.filter(
            (InvoiceDetail.supplier_code == contractor.supplier_code) |
            (InvoiceDetail.supplier_code.is_(None))
        )
    details = details_query.all()
    print(f"Found {len(details)} InvoiceDetail records")
    
    # Get unique cover_numbers from InvoiceDetail
    from sqlalchemy import distinct
    matching_details = InvoiceDetail.query.filter(
        (InvoiceDetail.supplier_code == contractor.supplier_code) |
        (InvoiceDetail.supplier_code.is_(None))
    ).with_entities(distinct(InvoiceDetail.cover_number)).all()
    
    matching_cover_numbers = [d[0] for d in matching_details if d[0]]
    print(f"Found {len(matching_cover_numbers)} unique cover_numbers from InvoiceDetail")
    print(f"Sample cover_numbers: {matching_cover_numbers[:5]}")
    
    # Test 3: Check summaries with fallback logic
    print(f"\nTest 3: Summaries with fallback logic (detail_code OR cover_number from InvoiceDetail)")
    print("-" * 60)
    from sqlalchemy import or_
    
    conditions = []
    detail_code_condition = InvoiceSummary.detail_code == contractor.detail_code
    conditions.append(detail_code_condition)
    
    if contractor.supplier_code and matching_cover_numbers:
        fallback_condition = InvoiceSummary.cover_number.in_(matching_cover_numbers)
        conditions.append(fallback_condition)
    
    if len(conditions) > 1:
        query3 = InvoiceSummary.query.filter(or_(*conditions))
    else:
        query3 = InvoiceSummary.query.filter(conditions[0])
    
    if contractor.supplier_code:
        query3 = query3.filter(
            (InvoiceSummary.supplier_code == contractor.supplier_code) |
            (InvoiceSummary.supplier_code.is_(None))
        )
    
    summaries3 = query3.all()
    print(f"Found {len(summaries3)} summaries with fallback logic")
    
    statuses3 = {}
    for s in summaries3:
        status = s.invoice_status or "None"
        if status not in statuses3:
            statuses3[status] = []
        statuses3[status].append(s.cover_number)
    
    print(f"Statuses: {len(statuses3)}")
    for status, covers in statuses3.items():
        print(f"  - {status}: {len(covers)} invoices")
        print(f"    Sample: {covers[:3]}")
    
    # Test 4: Check fiscal year 1404
    print(f"\nTest 4: Summaries in fiscal year 1404")
    print("-" * 60)
    g_year_start, g_month_start, g_day_start = persian.to_gregorian(1404, 1, 1)
    try:
        g_year_end, g_month_end, g_day_end = persian.to_gregorian(1404, 12, 30)
    except:
        g_year_end, g_month_end, g_day_end = persian.to_gregorian(1404, 12, 29)
    
    start_date = date(g_year_start, g_month_start, g_day_start)
    end_date = date(g_year_end, g_month_end, g_day_end)
    
    query4 = query3.filter(
        InvoiceSummary.invoice_date >= start_date,
        InvoiceSummary.invoice_date <= end_date
    )
    summaries4 = query4.all()
    print(f"Found {len(summaries4)} summaries in fiscal year 1404")
    
    statuses4 = {}
    for s in summaries4:
        status = s.invoice_status or "None"
        if status not in statuses4:
            statuses4[status] = []
        statuses4[status].append(s.cover_number)
    
    print(f"Statuses in fiscal year 1404: {len(statuses4)}")
    for status, covers in statuses4.items():
        print(f"  - {status}: {len(covers)} invoices")
        print(f"    Sample: {covers[:3]}")
    
    # Test 5: Check what the API endpoint returns
    print(f"\nTest 5: Simulating filters/options endpoint")
    print("-" * 60)
    # This is the same logic as in get_filter_options
    base_query = query3  # Use the fallback query
    
    # Apply fiscal year filter
    fiscal_year_query = base_query.filter(
        InvoiceSummary.invoice_date >= start_date,
        InvoiceSummary.invoice_date <= end_date
    )
    
    summaries_with_date = fiscal_year_query.filter(InvoiceSummary.invoice_date.isnot(None)).all()
    print(f"Summaries with date in fiscal year 1404: {len(summaries_with_date)}")
    
    # Extract statuses (this is what the endpoint does)
    all_summaries = fiscal_year_query.all()
    print(f"All summaries for status extraction: {len(all_summaries)}")
    
    statuses_extracted = set()
    status_counts = {}
    for summary in all_summaries:
        if summary.invoice_status:
            statuses_extracted.add(summary.invoice_status)
            status_counts[summary.invoice_status] = status_counts.get(summary.invoice_status, 0) + 1
    
    print(f"Extracted statuses: {len(statuses_extracted)}")
    for status in statuses_extracted:
        print(f"  - {status}: {status_counts.get(status, 0)} invoices")

