# ⚠️ مهم جداً: إعداد ملف .env

## 🔴 المشكلة في ملفك الحالي

ملف `.env` الذي عرضته يحتوي على خطأ واحد **مهم جداً**:

```env
DATABASE_URL=
```

هذا السطر **فارغ**! يجب أن يحتوي على عنوان الاتصال بقاعدة البيانات.

---

## ✅ الحل السريع

في ملف `.env` الخاص بك، **غيّر هذا السطر**:

### ❌ الخطأ:
```env
DATABASE_URL=
```

### ✅ الصحيح:
```env
DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@localhost:5432/cems_db
```

---

## 📝 ملف .env الكامل المُحدّث

استخدم هذا المحتوى الكامل لملف `.env`:

```env
# ==================== Application Settings ====================
PROJECT_NAME=CEMS - Currency Exchange Management System
VERSION=1.0.0
DEBUG=True
API_V1_PREFIX=/api/v1

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# ==================== Database Settings ====================
POSTGRES_SERVER=localhost
POSTGRES_USER=cems_user
POSTGRES_PASSWORD=cems_password_2025
POSTGRES_DB=cems_db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@localhost:5432/cems_db

# ==================== Redis Settings ====================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ==================== JWT & Security ====================
SECRET_KEY=ThisIsAVerySecureSecretKeyForCEMS2025WithMinimum32Characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password & Security
PASSWORD_MIN_LENGTH=8
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_DURATION_MINUTES=30

# ==================== CORS Settings ====================
BACKEND_CORS_ORIGINS=http://localhost:3000

# ==================== Rate Limiting ====================
RATE_LIMIT_PER_MINUTE=60

# ==================== File Upload ====================
MAX_UPLOAD_SIZE=5242880
UPLOAD_DIR=uploads
ALLOWED_DOCUMENT_TYPES=application/pdf,image/jpeg,image/png

# ==================== Email Settings ====================
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=noreply@cems.co
EMAILS_ENABLED=False

# ==================== Logging ====================
LOG_LEVEL=INFO
LOG_FORMAT=json

# ==================== Business Settings ====================
TRANSACTION_NUMBER_PREFIX=TRX
VAULT_TRANSFER_PREFIX=VTR
CUSTOMER_NUMBER_PREFIX=CUS
BRANCH_CODE_PREFIX=BR

DEFAULT_BASE_CURRENCY=USD
COMMISSION_RATE=0.01
LARGE_TRANSFER_THRESHOLD=10000.0
```

---

## 🎯 شرح DATABASE_URL

`DATABASE_URL` يتكون من:

```
postgresql+asyncpg://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]
```

### في حالتك:
- **Driver:** `postgresql+asyncpg` (للاتصال async)
- **User:** `cems_user`
- **Password:** `cems_password_2025`
- **Host:** `localhost` (أو `db` في Docker)
- **Port:** `5432` (PostgreSQL default)
- **Database:** `cems_db`

### 🐳 إذا كنت تستخدم Docker:

في حالة Docker Compose، HOST يكون اسم الخدمة:

```env
DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@db:5432/cems_db
```

**ملاحظة:** في Docker Compose، `localhost` يتم استبداله بـ `db` (اسم service في docker-compose.yml)

---

## 🔍 التحقق من الإعدادات

بعد تحديث `.env`، تحقق من أن كل شيء يعمل:

```bash
# 1. التحقق من أن ملف .env موجود
ls -la .env

# 2. التحقق من DATABASE_URL
cat .env | grep DATABASE_URL

# يجب أن تشاهد:
# DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@localhost:5432/cems_db

# 3. اختبار الاتصال بقاعدة البيانات
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('DATABASE_URL:', os.getenv('DATABASE_URL'))
"
```

---

## ⚡ الخطوات الكاملة للإعداد

### 1. تحديث .env
```bash
# افتح الملف وأضف DATABASE_URL
nano .env
# أو
vim .env
```

### 2. إنشاء قاعدة البيانات (إذا لم تكن موجودة)
```bash
# اتصل بـ PostgreSQL
psql -U postgres

# في psql prompt:
CREATE USER cems_user WITH PASSWORD 'cems_password_2025';
CREATE DATABASE cems_db OWNER cems_user;
GRANT ALL PRIVILEGES ON DATABASE cems_db TO cems_user;
\q
```

### 3. تطبيق Migrations
```bash
alembic upgrade head
```

### 4. تشغيل Seeding
```bash
chmod +x scripts/SEED_USAGE_3.sh
./scripts/SEED_USAGE_3.sh
```

---

## 🐳 في Docker

إذا كنت تستخدم Docker Compose، استخدم:

```bash
docker compose down -v
docker compose up -d
sleep 5
docker compose exec app alembic upgrade head
sleep 5
docker compose exec app bash scripts/SEED_USAGE_3.sh
```

**⚠️ مهم:** في Docker، تأكد من أن `DATABASE_URL` في `.env` يستخدم `db` كـ host:

```env
DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@db:5432/cems_db
```

---

## ✨ الخلاصة

**التغيير الوحيد المطلوب:**

```diff
- DATABASE_URL=
+ DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@localhost:5432/cems_db
```

بعد هذا التغيير، كل شيء سيعمل بشكل مثالي! 🎉
