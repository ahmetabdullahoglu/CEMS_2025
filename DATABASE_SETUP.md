# إعداد قاعدة البيانات - CEMS

## 📋 نظرة عامة

تم إصلاح جميع مشاكل Vault Management Module بنجاح! الآن يجب عليك إعداد قاعدة البيانات لتشغيل النظام.

---

## 🚀 خطوات الإعداد (بالترتيب)

### 1️⃣ التأكد من ملف `.env`

تأكد من وجود ملف `.env` في جذر المشروع مع التكوينات التالية:

```bash
# Database Configuration
POSTGRES_SERVER=localhost
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=cems_db
DATABASE_URL=postgresql+asyncpg://your_db_user:your_db_password@localhost/cems_db

# Security
SECRET_KEY=your-super-secret-key-at-least-32-characters-long

# App Settings
APP_NAME=CEMS
DEBUG=True
```

**⚠️ مهم:** تأكد من إنشاء قاعدة البيانات أولاً:
```sql
CREATE DATABASE cems_db;
```

---

### 2️⃣ تطبيق Migrations

قم بتطبيق جميع migrations لإنشاء جداول قاعدة البيانات:

```bash
# في مجلد المشروع الرئيسي
alembic upgrade head
```

**المتوقع أن ترى:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_users_roles
INFO  [alembic.runtime.migration] Running upgrade 001_users_roles -> 002_currencies
INFO  [alembic.runtime.migration] Running upgrade 002_currencies -> 003_branch_tables
INFO  [alembic.runtime.migration] Running upgrade 003_branch_tables -> 005_create_customer_tables
INFO  [alembic.runtime.migration] Running upgrade 005_create_customer_tables -> 006_add_transactions
INFO  [alembic.runtime.migration] Running upgrade 006_add_transactions -> 007_vault_tables
INFO  [alembic.runtime.migration] Running upgrade 007_vault_tables -> ddc1f12b9caf
```

---

### 3️⃣ تشغيل Seeding Scripts (بالترتيب)

الآن قم بتشغيل scripts التعبئة بالترتيب الصحيح:

#### أ. البيانات الأساسية (Users & Roles)
```bash
python scripts/seed_data.py
```

#### ب. العملات (Currencies)
```bash
python scripts/seed_currencies.py
```

#### ج. الفروع (Branches)
```bash
python scripts/seed_branches.py
```

#### د. العملاء (Customers) - اختياري
```bash
python scripts/seed_customers.py
```

#### هـ. المعاملات (Transactions) - اختياري
```bash
python scripts/seed_transactions.py
```

#### و. الخزائن والتحويلات (Vaults & Transfers)
```bash
python scripts/seed_vaults.py
```

---

### 4️⃣ التحقق من النجاح

بعد تطبيق جميع migrations والـ seeding، تحقق من:

```bash
# التحقق من حالة migration
alembic current

# يجب أن ترى:
# ddc1f12b9caf (head)
```

---

## 🔍 استكشاف الأخطاء

### إذا واجهت: `relation "roles" does not exist`
✅ **الحل:** قم بتشغيل `alembic upgrade head` أولاً

### إذا واجهت: `column vault_balances.is_active does not exist`
✅ **الحل:** تأكد من تطبيق آخر migration:
```bash
alembic upgrade head
```

### إذا واجهت: `invalid input value for enum vault_type_enum: "MAIN"`
✅ **الحل:** تم إصلاح هذه المشكلة في آخر commit. قم بـ pull آخر التغييرات:
```bash
git pull origin claude/fix-vault-transfer-backref-011CUx1oLKncJGS1P59g9kxS
```

---

## 📊 الجداول التي سيتم إنشاؤها

بعد تطبيق جميع migrations، سيكون لديك:

### Phase 1-2: Core
- ✅ `users`
- ✅ `roles`
- ✅ `user_roles`

### Phase 3: Currency
- ✅ `currencies`
- ✅ `exchange_rates`
- ✅ `exchange_rate_history`

### Phase 4: Branches
- ✅ `branches`
- ✅ `branch_balances`
- ✅ `branch_balance_history`
- ✅ `branch_alerts`

### Phase 5: Customers
- ✅ `customers`
- ✅ `customer_documents`
- ✅ `customer_notes`

### Phase 6: Transactions
- ✅ `transactions` (with polymorphic types)

### Phase 7: Vaults ⭐ (الجديد)
- ✅ `vaults`
- ✅ `vault_balances`
- ✅ `vault_transfers`

---

## 🎯 النتيجة المتوقعة

بعد اتباع جميع الخطوات بنجاح:

```
✅ Database created
✅ All migrations applied (8 migrations)
✅ Default users and roles created
✅ Sample currencies loaded
✅ Sample branches created
✅ Main vault and branch vaults created
✅ Sample vault transfers created
```

---

## 📝 ملاحظات مهمة

1. **ترتيب التشغيل مهم جداً!** لا تقفز بين الخطوات
2. تأكد من وجود `.env` قبل أي شيء
3. جميع المشاكل السابقة تم إصلاحها في الكود
4. Migration 008 (ddc1f12b9caf) يضيف `is_active` لجدول `vault_balances`

---

## 🔗 المراجع

- **Branch:** `claude/fix-vault-transfer-backref-011CUx1oLKncJGS1P59g9kxS`
- **آخر Commit:** 812f8e8 - Add is_active column to vault_balances table

---

## ✨ جاهز للاختبار!

بعد إكمال جميع الخطوات، يمكنك تشغيل التطبيق:

```bash
uvicorn app.main:app --reload
```

ثم زيارة: http://localhost:8000/docs للوصول إلى API documentation
