# 🔄 دليل البدء من جديد - Fresh Start Guide

## 📋 الخطوات الكاملة لتنظيف كل شيء والبدء من الصفر

---

## 🧹 الخطوة 1: تنظيف كامل (Clean Slate)

```bash
# 1. إيقاف وحذف جميع الـ containers والـ volumes
docker compose down -v

# 2. حذف الـ images القديمة (اختياري لكن موصى به)
docker image rm $(docker images 'cems*' -q) 2>/dev/null || true

# 3. تنظيف ملفات Python cache
make clean

# 4. حذف ملفات uploads و logs
rm -rf uploads/* logs/*

# 5. حذف قاعدة البيانات المحلية (إن وجدت)
# إذا كنت تستخدم PostgreSQL محلياً:
# psql -U postgres -c "DROP DATABASE IF EXISTS cems_db;"
# psql -U postgres -c "DROP USER IF EXISTS cems_user;"
```

**أو استخدم أمر واحد:**
```bash
make reset-all
docker image rm $(docker images 'cems*' -q) 2>/dev/null || true
```

---

## 🔄 الخطوة 2: سحب آخر تحديثات الكود

```bash
# سحب آخر التحديثات من GitHub
git pull origin claude/fix-vault-transfer-backref-011CUx1oLKncJGS1P59g9kxS

# أو إذا كنت على branch آخر:
git checkout claude/fix-vault-transfer-backref-011CUx1oLKncJGS1P59g9kxS
git pull
```

---

## 🐳 الخطوة 3: إعادة بناء Docker (بدون cache)

```bash
# إعادة بناء الـ images من الصفر
docker compose build --no-cache

# انتظر حتى ينتهي البناء (قد يستغرق 2-5 دقائق)
```

---

## 🚀 الخطوة 4: البدء من جديد

### الطريقة الأولى: استخدام `make setup` (موصى به)

```bash
make setup
```

هذا الأمر سيقوم بـ:
1. ✅ تثبيت dependencies
2. ✅ إنشاء ملف `.env` من `.env.example`
3. ✅ بدء Docker containers
4. ✅ الانتظار 5 ثوانٍ حتى يصبح PostgreSQL جاهزاً
5. ✅ تطبيق migrations **داخل Docker**
6. ✅ زراعة البيانات **داخل Docker**

### الطريقة الثانية: استخدام `make docker-reset`

```bash
make docker-reset
```

هذا الأمر سيقوم بـ:
1. ✅ إيقاف وحذف containers والـ volumes
2. ✅ بدء containers جديدة
3. ✅ الانتظار حتى تصبح الخدمات جاهزة
4. ✅ تطبيق migrations
5. ✅ تنظيف Python cache
6. ✅ زراعة جميع البيانات

---

## ✅ الخطوة 5: التحقق من النجاح

### 1. التحقق من Docker containers

```bash
docker compose ps
```

يجب أن ترى:
```
NAME                IMAGE           STATUS
cems_app_dev        cems-app        Up
cems_postgres_dev   postgres:15     Up
cems_redis_dev      redis:7         Up
```

### 2. التحقق من logs

```bash
make docker-logs
```

يجب أن ترى:
```
INFO:     Application startup complete.
```

### 3. اختبار قاعدة البيانات

```bash
docker compose exec app python scripts/debug_auth.py
```

يجب أن ترى:
```
✅ Admin user found!
✅ Account is ACTIVE
✅ Password verification SUCCESSFUL!
```

### 4. اختبار تسجيل الدخول

```bash
docker compose exec app python scripts/test_login.py
```

يجب أن ترى:
```
✅ LOGIN SUCCESSFUL!
```

### 5. اختبار من المتصفح

افتح: http://localhost:8000/docs

1. اضغط على "Authorize" (أعلى اليمين)
2. أدخل:
   - **Username**: `admin`
   - **Password**: `Admin@123`
3. اضغط "Authorize"
4. يجب أن يتم تسجيل الدخول بنجاح! ✅

---

## 🎯 الخطوة 6: اختبار API

### من Swagger UI (المتصفح)

1. افتح: http://localhost:8000/docs
2. جرب endpoint `/api/v1/vault` (GET)
3. يجب أن ترى قائمة بالخزائن

### من Terminal (curl)

```bash
# 1. تسجيل الدخول والحصول على token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123"}' | \
  jq -r '.access_token')

# 2. اختبار API
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/vault" | jq

# 3. الحصول على vault summary
docker compose exec app python scripts/seed_vaults.py --show
```

---

## 🔍 استكشاف الأخطاء

### مشكلة: Docker containers لا تبدأ

```bash
# تحقق من أن Docker Desktop يعمل
docker ps

# تحقق من logs
docker compose logs

# أعد المحاولة
docker compose down -v
docker compose up -d
```

### مشكلة: Migrations تفشل

```bash
# تحقق من اتصال قاعدة البيانات
docker compose exec app python -c "from app.db.base import engine; print('DB OK')"

# أعد تطبيق migrations
docker compose exec app alembic downgrade base
docker compose exec app alembic upgrade head
```

### مشكلة: Seeding يفشل

```bash
# احذف البيانات الموجودة وأعد الزراعة
docker compose exec postgres psql -U cems_user -d cems_db -c "TRUNCATE users CASCADE;"
docker compose exec app python scripts/seed_data.py
```

### مشكلة: تسجيل الدخول يفشل

```bash
# شغّل أداة التشخيص
docker compose exec app python scripts/debug_auth.py

# إذا كان الباسوورد خاطئ، السكريبت سيصلحه تلقائياً
# ثم جرب تسجيل الدخول مرة أخرى
```

---

## 📊 معلومات مهمة

### بيانات الاعتماد الافتراضية

```
Username: admin
Password: Admin@123
Email:    admin@cems.co
```

### روابط مهمة

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Application**: http://localhost:8000

### قواعد البيانات

**Docker (الإعداد الموصى به):**
- Host: `postgres` (داخل Docker network)
- Port: `5432`
- User: `cems_user`
- Password: `cems_password_2025`
- Database: `cems_db`

**Local (إذا كنت تستخدم PostgreSQL محلياً):**
- Host: `localhost`
- Port: `5432`
- User: `cems_user`
- Password: `cems_password_2025`
- Database: `cems_db`

---

## 🚨 مشاكل شائعة وحلولها

### 1. "Invalid username or password" بعد `make setup`

**السبب**: كان Makefile القديم يشغل migrations و seeding محلياً بدلاً من داخل Docker

**الحل**:
```bash
git pull  # سحب Makefile المحدث
make reset-all
docker compose build --no-cache
make setup
```

### 2. قاعدتا بيانات مختلفتان

**الأعراض**:
- السكريبت المحلي يجد admin user
- لكن التطبيق في Docker يقول "Invalid credentials"

**الحل**:
استخدم **فقط** أوامر Docker:
```bash
# ✅ صحيح
docker compose exec app python scripts/debug_auth.py

# ❌ خطأ (هذا يتصل بقاعدة بيانات محلية)
python scripts/debug_auth.py
```

### 3. Migration 008 يشتكي من "column already exists"

**الحل**: Migration 008 ذكي ويتحقق من وجود الأعمدة أولاً
```bash
docker compose exec app alembic upgrade head
# سيطبع: "ℹ️ Column already exists, skipping..."
```

### 4. Docker image قديم

**الأعراض**: الكود محدث لكن المشكلة مستمرة

**الحل**:
```bash
docker compose down -v
docker image rm $(docker images 'cems*' -q)
docker compose build --no-cache
make docker-reset
```

---

## ✅ قائمة التحقق النهائية

بعد اتباع جميع الخطوات، تحقق من:

- [ ] Docker containers تعمل (`docker compose ps`)
- [ ] Application logs لا تحتوي على أخطاء (`make docker-logs`)
- [ ] Admin user موجود (`docker compose exec app python scripts/debug_auth.py`)
- [ ] Password صحيح (✅ Password verification SUCCESSFUL!)
- [ ] Login من API docs يعمل (http://localhost:8000/docs)
- [ ] Login من curl يعمل (يرجع access_token)
- [ ] Vaults موجودة (`make vault-summary` من داخل Docker)

---

## 🎉 الخطوات النهائية

إذا نجحت جميع الخطوات:

```bash
# 1. اعرض vault summary
docker compose exec app python scripts/seed_vaults.py --show

# 2. افتح API docs
open http://localhost:8000/docs
# أو:
# xdg-open http://localhost:8000/docs  # Linux
# start http://localhost:8000/docs     # Windows

# 3. استمتع بالعمل! 🎉
```

---

## 📚 ملفات مساعدة

- `CREDENTIALS.md` - معلومات بيانات الاعتماد
- `TROUBLESHOOTING_AUTH.md` - دليل حل مشاكل المصادقة
- `MAKEFILE_GUIDE.md` - دليل أوامر Makefile
- `DATABASE_SETUP.md` - دليل إعداد قاعدة البيانات
- `ENV_SETUP_NOTES.md` - ملاحظات إعداد البيئة

---

## 🆘 إذا استمرت المشكلة

1. راجع `TROUBLESHOOTING_AUTH.md`
2. شغّل جميع أدوات التشخيص:
   ```bash
   docker compose exec app python scripts/debug_auth.py > debug.txt
   docker compose exec app python scripts/test_login.py > test.txt
   docker compose logs app > logs.txt
   ```
3. راجع الملفات الناتجة للبحث عن أخطاء

---

**آخر تحديث**: 2025-11-09
**النسخة**: 2.0
**الحالة**: ✅ جميع المشاكل المعروفة تم حلها
