"""
اسکریپت خودکار برای ساخت فایل .env از config.example.env
این اسکریپت فایل .env را می‌سازد و تنظیمات PostgreSQL را اعمال می‌کند.
"""

import shutil
from pathlib import Path

def setup_env():
    backend_dir = Path(__file__).parent.parent
    example_env = backend_dir / "config.example.env"
    env_file = backend_dir / ".env"
    
    if env_file.exists():
        print(f"⚠️  فایل .env از قبل وجود دارد: {env_file}")
        response = input("آیا می‌خواهید آن را بازنویسی کنید؟ (y/n): ").strip().lower()
        if response != 'y':
            print("❌ عملیات لغو شد.")
            return
    
    # کپی از config.example.env
    shutil.copy(example_env, env_file)
    print(f"✅ فایل .env ساخته شد: {env_file}")
    print("\n📝 لطفاً فایل .env را ویرایش کنید و اطلاعات اتصال PostgreSQL را تنظیم کنید:")
    print("   DATABASE_URL=postgresql+psycopg://username:password@host:port/database")
    print("\n💡 مثال:")
    print("   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/contractorchatbot")

if __name__ == "__main__":
    setup_env()

