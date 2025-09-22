#!/bin/bash
set -e

echo "🌍 Starting Earthquake Monitor API..."

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
while ! pg_isready -h db -p 5432 -U postgres; do
    echo "   PostgreSQL is unavailable - sleeping for 2 seconds"
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Database migrations completed!"

# Create default admin user
echo "👤 Creating default admin user..."
python -c "
import sys
sys.path.append('/app')

from src.infrastructure.database.config import SessionLocal
from src.presentation.auth.repository import UserRepository
from src.presentation.auth.models import UserCreate

session = SessionLocal()
try:
    user_repo = UserRepository(session)

    # Check if admin user already exists
    existing_user = user_repo.get_user_by_email('admin@earthquake-monitor.com')
    if existing_user:
        print('✅ Admin user already exists')
    else:
        # Create admin user
        admin_user = UserCreate(
            email='admin@earthquake-monitor.com',
            username='admin',
            password='admin123',
            full_name='System Administrator',
            is_active=True
        )
        user_repo.create_user(admin_user)
        print('✅ Admin user created successfully')
except Exception as e:
    print(f'❌ Error with admin user: {e}')
finally:
    session.close()
" || true

# Start the application
echo "🚀 Starting FastAPI application..."
exec uvicorn src.presentation.main:app --host 0.0.0.0 --port 8000
