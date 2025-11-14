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

### 🌱 البيانات التجريبية (Seeding)

لتجربة النظام بشكل كامل مع بيانات واقعية، نوفر سكريبتات seed شاملة:

#### التشغيل السريع (موصى به)

```bash
# داخل حاوية Docker
docker exec -it cems_app_dev bash

# تشغيل السكريبتات بالترتيب
python scripts/seed_data.py          # الأدوار والمستخدمين الأساسيين
python scripts/seed_currencies.py   # العملات وأسعار الصرف
python scripts/seed_branches.py     # الفروع والأرصدة
python scripts/seed_comprehensive.py # بيانات شاملة (موصى به!)
```

#### ما الذي ستحصل عليه؟

بعد تشغيل `seed_comprehensive.py`:
- 👥 **30+ مستخدم** (2 admins, 10 managers, 18+ tellers)
- 👤 **150+ عميل** مع وثائق وملاحظات
- 🏦 **20+ خزنة** بأرصدة متعددة العملات
- 💸 **50+ تحويل خزنة** بحالات مختلفة
- 💳 **750+ معاملة**:
  - 60% صرافة (Exchange)
  - 20% تحويل (Transfer)
  - 10% إيرادات (Income)
  - 10% مصروفات (Expense)

#### الوضع المصغر (للاختبار السريع)

```bash
# بيانات أقل للاختبار السريع
python scripts/seed_comprehensive.py --small
# ينتج: 10 مستخدمين، 30 عميل، 60 معاملة
```

#### بيانات الدخول بعد التعبئة

**Admin:**
- Username: `admin` / Password: `Admin@123`

**Managers:**
- `manager01` إلى `manager10` / Password: `Password@123`

**Tellers:**
- `teller01` إلى `teller18` / Password: `Password@123`

📖 **المزيد من التفاصيل:** [دليل البيانات التجريبية الكامل](scripts/SEEDING_README.md)

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

### 🌱 Seed Data for Testing

To test the system with realistic data, we provide comprehensive seeding scripts:

#### Quick Setup (Recommended)

```bash
# Inside Docker container
docker exec -it cems_app_dev bash

# Run scripts in order
python scripts/seed_data.py          # Roles and base users
python scripts/seed_currencies.py   # Currencies and exchange rates
python scripts/seed_branches.py     # Branches and balances
python scripts/seed_comprehensive.py # Comprehensive data (Recommended!)
```

#### What You'll Get

After running `seed_comprehensive.py`:
- 👥 **30+ users** (2 admins, 10 managers, 18+ tellers)
- 👤 **150+ customers** with documents and notes
- 🏦 **20+ vaults** with multi-currency balances
- 💸 **50+ vault transfers** with various statuses
- 💳 **750+ transactions**:
  - 60% Exchange operations
  - 20% Transfers
  - 10% Income
  - 10% Expenses

#### Small Mode (Quick Testing)

```bash
# Less data for quick testing
python scripts/seed_comprehensive.py --small
# Generates: 10 users, 30 customers, 60 transactions
```

#### Login Credentials

**Admin:**
- Username: `admin` / Password: `Admin@123`

**Managers:**
- `manager01` to `manager10` / Password: `Password@123`

**Tellers:**
- `teller01` to `teller18` / Password: `Password@123`

📖 **More Details:** [Complete Seeding Guide](scripts/SEEDING_README.md)

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