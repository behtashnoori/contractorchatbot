"""Script to check database row counts"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app import create_app
from backend.app.models import Contractor, InvoiceSummary, InvoiceDetail, ImportBatch, ImportError, User

def main():
    app = create_app()
    with app.app_context():
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
        print("=" * 60)
        print("بررسی تعداد ردیف‌های آپلود شده در دیتابیس")
        print("=" * 60)
        print()
        
        # Count contractors
        contractor_count = Contractor.query.count()
        print(f"📊 تعداد پیمانکاران (Contractors): {contractor_count:,}")
        
        # Count invoice summaries
        invoice_summary_count = InvoiceSummary.query.count()
        print(f"📊 تعداد خلاصه فاکتورها (Invoice Summaries): {invoice_summary_count:,}")
        
        # Count invoice details
        invoice_detail_count = InvoiceDetail.query.count()
        print(f"📊 تعداد جزئیات فاکتورها (Invoice Details): {invoice_detail_count:,}")
        
        # Count import batches
        batch_count = ImportBatch.query.count()
        print(f"📊 تعداد Batch های آپلود (Import Batches): {batch_count:,}")
        
        # Count import errors
        error_count = ImportError.query.count()
        print(f"📊 تعداد خطاهای آپلود (Import Errors): {error_count:,}")
        
        # Count users
        user_count = User.query.count()
        print(f"📊 تعداد کاربران (Users): {user_count:,}")
        
        print()
        print("=" * 60)
        print("جزئیات آخرین Batch های آپلود:")
        print("=" * 60)
        
        # Get last 5 batches
        last_batches = ImportBatch.query.order_by(ImportBatch.created_at.desc()).limit(5).all()
        for batch in last_batches:
            print(f"\n📦 Batch: {batch.name}")
            print(f"   Source: {batch.source}")
            print(f"   Status: {batch.status}")
            print(f"   Uploaded by: {batch.uploaded_by}")
            print(f"   Created: {batch.created_at}")
            if batch.total_rows:
                print(f"   Progress: {batch.rows_processed}/{batch.total_rows} ({batch.progress_percentage:.1f}%)")
            if batch.inserted_count or batch.updated_count or batch.errors_count:
                print(f"   Metrics: {batch.inserted_count} جدید، {batch.updated_count} به‌روزرسانی، {batch.errors_count} خطا")
            
            # Count records for this batch
            if batch.source == "contractors-1":
                batch_summaries = InvoiceSummary.query.filter_by(last_update_batch_id=batch.id).count()
                print(f"   Invoice Summaries: {batch_summaries}")
            elif batch.source == "contractors-2":
                batch_details = InvoiceDetail.query.filter_by(last_update_batch_id=batch.id).count()
                print(f"   Invoice Details: {batch_details}")
            elif batch.source == "codtafsiltamin":
                print(f"   (Contractors imported)")
            
            batch_errors = ImportError.query.filter_by(batch_id=batch.id).count()
            if batch_errors > 0:
                print(f"   ⚠️  Errors: {batch_errors}")

if __name__ == "__main__":
    main()

