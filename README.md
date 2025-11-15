# 💱 CEMS - Currency Exchange Management System

<div align="center">

![CEMS Logo](https://via.placeholder.com/200x200?text=CEMS)

**نظام متكامل لإدارة عمليات الصرافة متعدد الفروع**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](#english) | [العربية](#arabic)

</div>

---

<a name="arabic"></a>
## 🇸🇦 النسخة العربية

### 📖 نظرة عامة

**CEMS** هو نظام شامل ومتكامل لإدارة شركات الصرافة وعملياتها، مع دعم كامل للفروع المتعددة، الخزائن، العملاء، والمستخدمين. تم تصميمه لتحقيق:

- ✅ **الكفاءة التشغيلية** في إدارة المعاملات المالية
- ✅ **دقة المتابعة المالية** لجميع العمليات
- ✅ **الأمان العالي** في حماية البيانات والصلاحيات
- ✅ **سهولة الاستخدام** للموظفين والإدارة

### ⚡ الميزات الرئيسية

#### 🏦 إدارة العملات
- إنشاء وتحديث العملات المختلفة
- إدارة أسعار الصرف بين العملات
- تتبع تاريخ الأسعار والتغيرات
- تحليل اتجاهات الصرف

#### 🏢 إدارة الفروع
- إدارة متعددة الفروع (CRUD كامل)
- تتبع رصيد كل عملة في كل فرع
- التحويلات بين الفروع مع سجل تدقيق
- تنبيهات ذكية عند انخفاض الأرصدة
- ربط الموظفين بالفروع مع صلاحيات مخصصة

#### 👥 إدارة العملاء
- تسجيل بيانات العملاء (KYC)
- ملفات تفصيلية لكل عميل
- تتبع سجل المعاملات الكامل
- تحليل سلوك العملاء

#### 🔐 المصادقة والصلاحيات
- نظام صلاحيات هرمي (RBAC)
- ثلاثة أدوار رئيسية: Admin, Manager, Teller
- مصادقة آمنة باستخدام JWT
- تتبع نشاط المستخدمين وسجل الأحداث

#### 💰 المعاملات المالية
- **الإيرادات (Income):** تسجيل الإيرادات ومصادر الدخل
- **المصروفات (Expense):** تتبع المصروفات وتصنيفها
- **الصرف (Exchange):** عمليات تحويل العملات
- **التحويلات (Transfer):** بين الفروع أو الخزينة
- رقم مرجعي فريد لكل معاملة
- حالات المعاملات (معلقة / مكتملة / ملغاة)

#### 🏛️ إدارة الخزينة
- إدارة الخزينة المركزية
- تحويلات من/إلى الفروع
- تتبع حركة الأموال في الوقت الفعلي
- نظام الموافقات للمبالغ الكبيرة

#### 📊 التقارير والتحليلات
- تقارير الأداء للشركة والفروع
- تقارير اتجاهات الصرف والسيولة
- تحليل الإيرادات والمصروفات
- لوحات مراقبة تفاعلية
- تصدير بصيغ: PDF, Excel, JSON

### 🛠️ التقنيات المستخدمة

| المكون | التقنية |
|--------|---------|
| **Backend** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL 15 + SQLAlchemy ORM |
| **Cache** | Redis |
| **Authentication** | JWT (JSON Web Tokens) |
| **API Docs** | Swagger/OpenAPI (تلقائي) |
| **Testing** | Pytest + Coverage |
| **Deployment** | Docker + Docker Compose |
| **Web Server** | Nginx (Reverse Proxy) |

### 🚀 البدء السريع

#### المتطلبات الأساسية

- Python 3.11 أو أحدث
- Docker و Docker Compose
- Git

#### التثبيت

```bash
# 1. استنساخ المشروع
git clone https://github.com/your-username/CEMS_2025.git
cd CEMS_2025

# 2. إنشاء ملف البيئة
cp .env.example .env

# 3. توليد مفتاح سري
python -c "import secrets; print(secrets.token_urlsafe(32))"
# انسخ الناتج وضعه في .env كـ SECRET_KEY

# 4. تشغيل الإعداد الكامل
make setup

# 5. الوصول للتطبيق
# API: http://localhost:8000
# Documentation: http://localhost:8000/docs
```

### 🌱 البيانات التجريبية (Seeding) - نسخة 10X

لتجربة النظام بشكل كامل مع بيانات واقعية، نوفر سكريبتات seed محسّنة بحجم بيانات 10 أضعاف:

#### التشغيل السريع (موصى به)

```bash
# داخل حاوية Docker
docker exec -it cems_app_dev bash

# تشغيل جميع السكريبتات
bash scripts/SEED_USAGE_3.sh
```

أو يدويًا:

```bash
python scripts/seed_data.py          # الأدوار والمستخدمين
python scripts/seed_currencies.py   # العملات وأسعار الصرف
python scripts/seed_branches.py     # الفروع والأرصدة
python scripts/seed_customers.py    # 110+ عميل (10X!)
python scripts/seed_transactions.py # 470+ معاملة (10X!)
python scripts/seed_vaults.py       # 40+ تحويل خزنة (10X!)
```

#### ما الذي ستحصل عليه؟

**بيانات شاملة (10X):**
- 👥 **1 مستخدم admin** (يمكن إضافة المزيد حسب الحاجة)
- 👤 **110 عميل** (85% أفراد، 15% شركات)
  - 200+ وثيقة (هويات، جوازات سفر، رخص قيادة)
  - 110+ ملاحظة
- 💳 **470 معاملة** موزعة على آخر 6 أشهر:
  - 130 معاملة إيرادات (عمولات ورسوم)
  - 100 معاملة مصروفات (إيجار، رواتب، خدمات)
  - 150 معاملة صرافة (تحويلات عملات)
  - 90 معاملة تحويل (بين الفروع)
- 🏦 **خزن متعددة** بأرصدة متنوعة العملات
- 💸 **40 تحويل خزنة** (70% مكتمل، 15% قيد النقل، 10% معلق، 5% ملغى)

#### بيانات الدخول

**Admin:**
- Username: `admin` / Password: `Admin@123`

⚠️ **مهم:** غيّر كلمة المرور بعد أول تسجيل دخول!

### 📚 التوثيق

- [📖 دليل الإعداد الكامل](PROJECT_SETUP.md)
- [🏗️ البنية المعمارية](docs/architecture.md)
- [🔐 نظام الصلاحيات](docs/permissions.md)
- [📊 مخطط قاعدة البيانات](docs/database_schema.md)
- [🚀 دليل النشر](docs/deployment_guide.md)

### 📦 هيكل المشروع

```
CEMS_2025/
├── 📁 app/                    # التطبيق الرئيسي
│   ├── api/v1/endpoints/     # نقاط النهاية
│   ├── core/                 # الإعدادات الأساسية
│   ├── db/models/            # نماذج قاعدة البيانات
│   ├── services/             # منطق الأعمال
│   ├── repositories/         # طبقة الوصول للبيانات
│   └── schemas/              # مخططات Pydantic
├── 📁 tests/                 # الاختبارات
├── 📁 alembic/               # Database migrations
├── 📁 docker/                # إعدادات Docker
└── 📁 docs/                  # التوثيق
```

### 🧪 الاختبار

```bash
# تشغيل جميع الاختبارات
make test

# اختبارات الوحدة فقط
make test-unit

# اختبارات التكامل فقط
make test-integration

# مع تقرير التغطية
pytest --cov=app --cov-report=html
```

### 🔒 الأمان

- ✅ مصادقة JWT آمنة
- ✅ نظام صلاحيات متقدم (RBAC)
- ✅ تشفير كلمات المرور (bcrypt)
- ✅ سجل تدقيق شامل
- ✅ حماية من CSRF و XSS
- ✅ Rate limiting على API

### 🤝 المساهمة

نرحب بمساهماتكم! يرجى:

1. Fork المشروع
2. إنشاء branch للميزة (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push للـ branch (`git push origin feature/amazing-feature`)
5. فتح Pull Request

### 📄 الترخيص

هذا المشروع مرخص تحت [MIT License](LICENSE)

### 📧 التواصل

- 🌐 الموقع: [your-website.com](https://your-website.com)
- 📧 البريد: info@your-domain.com
- 💬 Telegram: [@your_channel](https://t.me/your_channel)

---

<a name="english"></a>
## 🇬🇧 English Version

### 📖 Overview

**CEMS (Currency Exchange Management System)** is a comprehensive multi-branch solution designed to manage all aspects of currency exchange operations efficiently and securely.

### ⚡ Key Features

- 🏦 **Currency Management** - Manage currencies and exchange rates
- 🏢 **Branch Management** - Multi-branch support with balances
- 👥 **Customer Management** - Complete KYC and transaction history
- 🔐 **RBAC System** - Role-based access control
- 💰 **Financial Transactions** - Income, Expense, Exchange, Transfer
- 🏛️ **Vault Management** - Central vault with transfers
- 📊 **Reports & Analytics** - Comprehensive reporting system

### 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/your-username/CEMS_2025.git
cd CEMS_2025
make setup

# Access
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 🌱 Seed Data for Testing - 10X Version

To test the system with realistic data, we provide enhanced seeding scripts with 10x data volume:

#### Quick Setup (Recommended)

```bash
# Inside Docker container
docker exec -it cems_app_dev bash

# Run all seeding scripts
bash scripts/SEED_USAGE_3.sh
```

Or manually:

```bash
python scripts/seed_data.py          # Roles and users
python scripts/seed_currencies.py   # Currencies and exchange rates
python scripts/seed_branches.py     # Branches and balances
python scripts/seed_customers.py    # 110+ customers (10X!)
python scripts/seed_transactions.py # 470+ transactions (10X!)
python scripts/seed_vaults.py       # 40+ vault transfers (10X!)
```

#### What You'll Get

**Comprehensive Data (10X):**
- 👥 **1 admin user** (more can be added as needed)
- 👤 **110 customers** (85% individual, 15% corporate)
  - 200+ documents (IDs, passports, driving licenses)
  - 110+ notes
- 💳 **470 transactions** distributed over last 6 months:
  - 130 Income transactions (commissions & fees)
  - 100 Expense transactions (rent, salaries, utilities)
  - 150 Exchange transactions (currency conversions)
  - 90 Transfer transactions (branch-to-branch)
- Every seeded transaction now includes a `description` summary that's surfaced by the API responses
- 🏦 **Multiple vaults** with multi-currency balances
- 💸 **40 vault transfers** (70% completed, 15% in-transit, 10% pending, 5% cancelled)

#### Login Credentials

**Admin:**
- Username: `admin` / Password: `Admin@123`

⚠️ **Important:** Change password after first login!

### 📚 Documentation

- [📖 Setup Guide](PROJECT_SETUP.md)
- [🏗️ Architecture](docs/architecture.md)
- [📊 Database Schema](docs/database_schema.md)
- [🚀 Deployment Guide](docs/deployment_guide.md)

### 📄 License

This project is licensed under the [MIT License](LICENSE)

---

<div align="center">

**Made with ❤️ for the Currency Exchange Industry**

</div>