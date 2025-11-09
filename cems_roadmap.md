# 🗺️ CEMS Complete Development Roadmap
## خريطة الطريق الكاملة مع Prompts جاهزة للتنفيذ

---

## 📋 Project Overview - نظرة عامة

```
Total Phases: 8
Total Components: 24
Estimated Total Time: 30-35 days
Development Approach: Incremental, Test-Driven
```

---

## 🏗️ PHASE 1: Project Foundation & Setup
**المدة:** 2-3 أيام | **الأولوية:** CRITICAL | **Dependencies:** None

### Component 1.1: Project Structure & Configuration
**المدة:** 4-6 ساعات

```markdown
=== PROMPT FOR CHAT 1.1 ===

أنا أبدأ مشروع CEMS (Currency Exchange Management System) وأحتاج إلى إعداد البنية الأساسية.

**Context:**
- نظام إدارة صرافة متعدد الفروع
- Tech Stack: FastAPI + PostgreSQL + SQLAlchemy + Docker
- يحتاج: مصادقة JWT، صلاحيات متعددة، معاملات مالية

**المطلوب في هذه الجلسة:**

1. **Project Structure الكامل:**
```
CEMS_2025/
├── app/
│   ├── api/v1/endpoints/
│   ├── core/
│   ├── db/models/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   ├── middleware/
│   └── utils/
├── tests/
├── alembic/
├── docker/
└── docs/
```

2. **Core Configuration Files:**
   - `app/core/config.py` - Pydantic Settings
   - `app/core/constants.py` - Enums & Constants
   - `app/core/exceptions.py` - Custom Exceptions
   - `app/main.py` - FastAPI Application

3. **Environment & Dependencies:**
   - `requirements.txt` - Production dependencies
   - `requirements-dev.txt` - Development dependencies
   - `.env.example` - Environment variables template
   - `.gitignore` - Git ignore rules

4. **Docker Setup:**
   - `Dockerfile` - Application container
   - `docker-compose.yml` - Production setup
   - `docker-compose.dev.yml` - Development setup

5. **Database Configuration:**
   - `app/db/base.py` - SQLAlchemy base & session
   - `app/db/__init__.py` - Database utilities
   - `alembic.ini` - Alembic configuration
   - `alembic/env.py` - Migration environment

**Output Requirements:**
- ✅ كود كامل في Artifacts لكل ملف
- ✅ تعليمات setup خطوة بخطوة
- ✅ أوامر test للتحقق من التشغيل
- ✅ شرح مختصر لكل مكون

**Success Criteria:**
- FastAPI app يعمل على http://localhost:8000
- Database connection ناجحة
- `/docs` endpoint يفتح Swagger UI
- Docker containers تعمل بدون أخطاء
```

---

### Component 1.2: Database Base Models & Mixins
**المدة:** 3-4 ساعات

```markdown
=== PROMPT FOR CHAT 1.2 ===

**Context من الجلسة السابقة:**
تم إعداد Project Structure و FastAPI application. الآن نحتاج Database Models الأساسية.

**المطلوب في هذه الجلسة:**

1. **Base Model Class:**
   - `app/db/base_class.py`
   - Common fields: id, created_at, updated_at, is_active
   - UUID primary keys
   - Soft delete functionality

2. **Mixins للاستخدام المتكرر:**
   - `TimestampMixin` - created_at, updated_at
   - `SoftDeleteMixin` - is_deleted, deleted_at
   - `UserTrackingMixin` - created_by, updated_by

3. **Alembic Initial Migration:**
   - Setup alembic للمشروع
   - أول migration (revision) فارغة
   - Testing migration up/down

4. **Database Utilities:**
   - `app/db/session.py` - Session management
   - `app/db/init_db.py` - Database initialization
   - Connection pooling settings

**Technical Requirements:**
- استخدام UUID بدلاً من Integer IDs
- Timezone-aware timestamps (UTC)
- PostgreSQL-specific features (JSONB)
- Proper indexes on common queries

**Output Requirements:**
- ✅ كود كامل للـ Base Models
- ✅ Alembic migration script
- ✅ Database testing utilities
- ✅ SQL schema visualization

**Test Command:**
```bash
alembic upgrade head
alembic downgrade base
```
```

---

## 🔐 PHASE 2: Authentication & Authorization System
**المدة:** 3-4 أيام | **الأولوية:** CRITICAL | **Dependencies:** Phase 1

### Component 2.1: User & Role Models
**المدة:** 4-5 ساعات

```markdown
=== PROMPT FOR CHAT 2.1 ===

**Context:**
Project structure جاهز. نبدأ بنظام المصادقة والصلاحيات.

**المطلوب:**

1. **User Model** (`app/db/models/user.py`):
```python
Fields:
- id (UUID)
- username (unique, indexed)
- email (unique, indexed)
- hashed_password
- full_name
- phone_number (optional)
- is_active (default: True)
- is_superuser (default: False)
- last_login
- failed_login_attempts
- locked_until (for security)
- branches (relationship) - many-to-many
- roles (relationship) - many-to-many
```

2. **Role Model** (`app/db/models/role.py`):
```python
Fields:
- id (UUID)
- name (unique: admin, manager, teller)
- display_name_ar (Arabic name)
- description
- permissions (JSONB) - flexible permissions
- is_active
```

3. **User-Branch Assignment:**
```python
Table: user_branches
- user_id
- branch_id
- assigned_at
- assigned_by
- is_primary (boolean)
```

4. **Schemas** (`app/schemas/user.py`):
   - UserBase, UserCreate, UserUpdate, UserInDB, UserResponse
   - RoleBase, RoleCreate, RoleResponse
   - Validation rules (email format, password strength)

5. **Alembic Migration:**
   - Migration لإنشاء user و role tables
   - Default roles seed data (admin, manager, teller)
   - Default superuser account

**Security Requirements:**
- Password hashing (bcrypt)
- No sensitive data in responses
- Proper indexes for queries
- Audit trail preparation

**Output Requirements:**
- ✅ Models with relationships
- ✅ Pydantic schemas
- ✅ Migration script
- ✅ Seed data script
- ✅ Test cases للـ models
```

---

### Component 2.2: JWT Authentication Service
**المدة:** 5-6 ساعات

```markdown
=== PROMPT FOR CHAT 2.2 ===

**Context:**
User & Role models جاهزة. نحتاج JWT authentication system.

**المطلوب:**

1. **Security Utils** (`app/core/security.py`):
```python
Functions:
- get_password_hash(password: str) -> str
- verify_password(plain: str, hashed: str) -> bool
- create_access_token(data: dict) -> str
- create_refresh_token(data: dict) -> str
- decode_token(token: str) -> dict
```

2. **Auth Service** (`app/services/auth_service.py`):
```python
Methods:
- authenticate_user(username, password)
- register_user(user_data)
- refresh_access_token(refresh_token)
- logout_user(token)
- verify_email(token)
- reset_password(token, new_password)
- check_user_permissions(user, required_permissions)
```

3. **Dependencies** (`app/api/deps.py`):
```python
- get_current_user() - من JWT token
- get_current_active_user()
- require_role(roles: List[str])
- require_permission(permissions: List[str])
```

4. **Auth Endpoints** (`app/api/v1/endpoints/auth.py`):
```python
POST /auth/login - تسجيل دخول
POST /auth/register - تسجيل مستخدم جديد (superuser only)
POST /auth/refresh - تحديث access token
POST /auth/logout - تسجيل خروج
GET /auth/me - بيانات المستخدم الحالي
POST /auth/change-password - تغيير كلمة المرور
```

5. **Token Blacklist** (Optional but recommended):
   - Redis للتخزين المؤقت
   - Token revocation mechanism

**Security Requirements:**
- Access Token: 15 minutes expiry
- Refresh Token: 7 days expiry
- Rate limiting على login endpoint
- Login attempt tracking
- IP logging للأمان

**Output Requirements:**
- ✅ كود كامل لكل ملف
- ✅ Postman collection / curl examples
- ✅ Test cases شاملة
- ✅ Security best practices documentation
```

---

### Component 2.3: RBAC Middleware & Permissions
**المدة:** 3-4 ساعات

```markdown
=== PROMPT FOR CHAT 2.3 ===

**Context:**
JWT authentication يعمل. نحتاج RBAC system متقدم.

**المطلوب:**

1. **Permission System** (`app/core/permissions.py`):
```python
Permissions Structure:
{
  "users": ["create", "read", "update", "delete"],
  "branches": ["create", "read", "update", "delete", "assign_users"],
  "currencies": ["create", "read", "update", "delete", "set_rates"],
  "transactions": ["create", "read", "approve", "cancel"],
  "vault": ["read", "transfer", "approve_transfer"],
  "reports": ["view_branch", "view_all", "export"]
}

Default Role Permissions:
- admin: ALL permissions
- manager: branch-level + reports
- teller: transactions (limited) + read
```

2. **Middleware** (`app/middleware/rbac.py`):
   - Check user permissions قبل endpoint execution
   - Branch-level access control
   - Audit logging لكل permission check

3. **Decorators للـ Endpoints:**
```python
@require_permissions(["transactions.create"])
@require_branch_access()
@require_any_role(["admin", "manager"])
```

4. **Branch-Level Access Control:**
   - User يقدر يوصل فقط للـ branches المربوطة بيه
   - Superuser يقدر يوصل لكل الـ branches

**Output Requirements:**
- ✅ Permission system كامل
- ✅ Middleware implementation
- ✅ Decorator utilities
- ✅ Test scenarios (positive + negative)
```

---

## 💰 PHASE 3: Currency Management Module
**المدة:** 2-3 أيام | **الأولوية:** HIGH | **Dependencies:** Phase 1, 2

### Component 3.1: Currency Models & Exchange Rates
**المدة:** 4-5 ساعات

```markdown
=== PROMPT FOR CHAT 3.1 ===

**Context:**
Authentication system جاهز. نبدأ بـ core business logic: العملات وأسعار الصرف.

**المطلوب:**

1. **Currency Model** (`app/db/models/currency.py`):
```python
Fields:
- id (UUID)
- code (unique: USD, EUR, TRY, etc.) - 3 chars
- name_en
- name_ar
- symbol (optional: $, €, ₺)
- is_base_currency (boolean) - واحدة فقط
- is_active
- decimal_places (default: 2)
- created_at, updated_at
```

2. **ExchangeRate Model:**
```python
Fields:
- id (UUID)
- from_currency_id (FK -> Currency)
- to_currency_id (FK -> Currency)
- rate (Decimal, precision 10, scale 6)
- buy_rate (optional)
- sell_rate (optional)
- effective_from (timestamp)
- effective_to (nullable) - للـ history
- set_by (FK -> User)
- is_active (latest rate)
```

3. **ExchangeRateHistory Model:**
   - Track all rate changes
   - Who, when, old value, new value

4. **Schemas** (`app/schemas/currency.py`):
   - CurrencyCreate, CurrencyUpdate, CurrencyResponse
   - ExchangeRateCreate, ExchangeRateUpdate, ExchangeRateResponse
   - Validation: positive rates, unique pairs

**Business Rules:**
- واحد base currency فقط في النظام
- Exchange rate دائماً positive
- من العملة للـ base currency تلقائي (1/rate)
- History يحفظ كل تغيير

**Output Requirements:**
- ✅ Models مع relationships
- ✅ Migration script
- ✅ Seed data (USD, EUR, TRY, GBP)
- ✅ Test cases
```

---

### Component 3.2: Currency Service & API
**المدة:** 4-5 ساعات

```markdown
=== PROMPT FOR CHAT 3.2 ===

**Context:**
Currency models جاهزة. نحتاج Service layer و API endpoints.

**المطلوب:**

1. **Currency Repository** (`app/repositories/currency_repo.py`):
```python
Methods:
- get_all_currencies(include_inactive=False)
- get_currency_by_code(code)
- get_base_currency()
- create_currency(data)
- update_currency(id, data)
- activate/deactivate_currency(id)
```

2. **Currency Service** (`app/services/currency_service.py`):
```python
Methods:
- create_currency(data, current_user)
- update_currency(id, data, current_user)
- get_currency_with_rates(currency_id)
- set_exchange_rate(from, to, rate, user)
- get_latest_rate(from_currency, to_currency)
- calculate_exchange(amount, from, to) -> result
- get_rate_history(from, to, date_range)
```

3. **API Endpoints** (`app/api/v1/endpoints/currencies.py`):
```python
GET /currencies - List all (with filtering)
GET /currencies/{id} - Get single currency
POST /currencies - Create [admin only]
PUT /currencies/{id} - Update [admin only]
DELETE /currencies/{id} - Soft delete [admin only]

POST /currencies/rates - Set exchange rate [admin/manager]
GET /currencies/rates/{from}/{to} - Get current rate
GET /currencies/rates/history - Rate history
GET /currencies/calculate - Calculate exchange amount
```

**Validation Rules:**
- Currency code: 3 uppercase letters
- Rate: must be > 0
- واحد base currency فقط active
- Cannot delete currency with transactions

**Output Requirements:**
- ✅ Repository + Service layer
- ✅ Complete API endpoints
- ✅ OpenAPI documentation
- ✅ Integration tests
- ✅ Postman collection examples
```

---

## 🏢 PHASE 4: Branch Management Module
**المدة:** 3-4 أيام | **الأولوية:** HIGH | **Dependencies:** Phase 2, 3

### Component 4.1: Branch Models & Balance Tracking
**المدة:** 5-6 ساعات

```markdown
=== PROMPT FOR CHAT 4.1 ===

**Context:**
Currency system جاهز. نبدأ بإدارة الفروع والأرصدة.

**المطلوب:**

1. **Branch Model** (`app/db/models/branch.py`):
```python
Fields:
- id (UUID)
- code (unique: BR001, BR002, etc.)
- name_en
- name_ar
- region (enum: Istanbul_European, Istanbul_Asian, Ankara, etc.)
- address
- phone
- email
- manager_id (FK -> User) - nullable
- is_active
- is_main_branch (boolean) - واحد فقط
- opening_balance_date
- created_at, updated_at
```

2. **BranchBalance Model:**
```python
Fields:
- id (UUID)
- branch_id (FK -> Branch)
- currency_id (FK -> Currency)
- balance (Decimal 15,2)
- reserved_balance (Decimal) - للمعاملات المعلقة
- available_balance (computed: balance - reserved)
- minimum_threshold (alert trigger)
- maximum_threshold (alert trigger)
- last_updated
- last_reconciled_at

Constraints:
- Unique: (branch_id, currency_id)
- Check: balance >= 0
```

3. **BranchBalanceHistory Model:**
   - Track every balance change
   - transaction_type, amount, balance_before, balance_after
   - reference_id (FK to Transaction)

4. **BranchAlert Model:**
   - alert_type (low_balance, high_balance, suspicious_activity)
   - triggered_at, resolved_at
   - severity (info, warning, critical)

**Business Rules:**
- Branch balance لا يمكن يكون سالب
- Reserved balance عند pending transactions
- Minimum threshold alert للسيولة
- واحد main branch للخزينة الرئيسية

**Output Requirements:**
- ✅ Models مع constraints
- ✅ Trigger functions (PostgreSQL)
- ✅ Migration script
- ✅ Seed data (2-3 branches)
- ✅ Test cases للـ balance calculations
```

---

### Component 4.2: Branch Service & Balance Operations
**المدة:** 5-6 ساعات

```markdown
=== PROMPT FOR CHAT 4.2 ===

**Context:**
Branch models جاهزة. نحتاج Business logic للإدارة والتحويلات.

**المطلوب:**

1. **Branch Repository** (`app/repositories/branch_repo.py`):
```python
Methods:
- get_all_branches(region=None, is_active=True)
- get_branch_by_code(code)
- get_branch_with_balances(branch_id)
- get_user_branches(user_id)
- create_branch(data)
- update_branch(id, data)
```

2. **Branch Service** (`app/services/branch_service.py`):
```python
Methods:
- create_branch(data, current_user)
- update_branch(id, data, current_user)
- assign_manager(branch_id, user_id)
- assign_users_to_branch(branch_id, user_ids)
- get_branch_balance(branch_id, currency_id)
- get_all_balances(branch_id)
- check_balance_alerts(branch_id)
- set_balance_thresholds(branch, currency, min, max)
```

3. **Balance Service** (`app/services/balance_service.py`):
```python
CRITICAL Methods:
- update_balance(branch, currency, amount, transaction_ref)
- reserve_balance(branch, currency, amount, transaction_id)
- release_reserved_balance(transaction_id)
- reconcile_branch_balance(branch_id)
- get_balance_history(branch, currency, date_range)

Atomic Operations:
- كل عملية في database transaction
- Optimistic locking للـ concurrency
- Balance validation قبل أي تحديث
```

4. **API Endpoints** (`app/api/v1/endpoints/branches.py`):
```python
GET /branches - List branches
GET /branches/{id} - Branch details
POST /branches - Create [admin only]
PUT /branches/{id} - Update [admin/manager]
DELETE /branches/{id} - Soft delete [admin]

GET /branches/{id}/balances - All currency balances
GET /branches/{id}/balances/{currency} - Specific currency
PUT /branches/{id}/thresholds - Set alert thresholds

GET /branches/{id}/users - Assigned users
POST /branches/{id}/users - Assign users [manager]
DELETE /branches/{id}/users/{user_id} - Remove user

GET /branches/{id}/alerts - Active alerts
```

**Critical Requirements:**
- Thread-safe balance updates
- Audit trail لكل عملية
- Alert system للـ thresholds
- Branch-level access control

**Output Requirements:**
- ✅ Repository + Service layers
- ✅ Complete API endpoints
- ✅ Concurrent update handling
- ✅ Integration tests
- ✅ Alert mechanism
```

---

## 👥 PHASE 5: Customer Management Module
**المدة:** 2 أيام | **الأولوية:** MEDIUM | **Dependencies:** Phase 2, 4

### Component 5.1: Customer Model & KYC
**المدة:** 4-5 ساعات

```markdown
=== PROMPT FOR CHAT 5.1 ===

**Context:**
Branch system جاهز. نحتاج Customer management للمعاملات.

**المطلوب:**

1. **Customer Model** (`app/db/models/customer.py`):
```python
Fields:
- id (UUID)
- customer_number (unique, auto-generated: CUS-00001)
- first_name
- last_name
- name_ar (optional)
- national_id (unique, indexed) - هوية
- passport_number (optional)
- phone_number (required)
- email (optional)
- date_of_birth
- nationality
- address
- city, country
- customer_type (individual, corporate)
- risk_level (low, medium, high)
- is_active
- registered_at
- registered_by (FK -> User)
- branch_id (FK -> Branch) - primary branch
```

2. **CustomerDocument Model:**
```python
Fields:
- id (UUID)
- customer_id (FK -> Customer)
- document_type (national_id, passport, utility_bill, etc.)
- document_number
- document_url (file path or S3 key)
- issue_date
- expiry_date
- verified_by (FK -> User)
- verified_at
- is_verified
```

3. **CustomerNote Model:**
   - Internal notes by staff
   - note_text, created_by, is_alert

**Validation Rules:**
- National ID format validation (country-specific)
- Phone number format (international)
- Age validation (must be 18+)
- Duplicate customer check

**Output Requirements:**
- ✅ Models with validation
- ✅ Migration script
- ✅ Schemas (CustomerCreate, CustomerUpdate, CustomerResponse)
- ✅ Test cases
```

---

### Component 5.2: Customer Service & API
**المدة:** 3-4 ساعات

```markdown
=== PROMPT FOR CHAT 5.2 ===

**Context:**
Customer models جاهزة. نحتاج Service layer و API.

**المطلوب:**

1. **Customer Repository & Service:**
```python
Service Methods:
- create_customer(data, current_user, branch_id)
- update_customer(id, data, current_user)
- search_customers(query, branch_id, filters)
- get_customer_by_national_id(national_id)
- get_customer_transactions(customer_id, date_range)
- calculate_customer_stats(customer_id)
- add_customer_note(customer_id, note, user)
```

2. **API Endpoints** (`app/api/v1/endpoints/customers.py`):
```python
GET /customers - Search/List customers
GET /customers/{id} - Customer details
POST /customers - Register new customer
PUT /customers/{id} - Update customer
DELETE /customers/{id} - Deactivate [admin only]

GET /customers/{id}/transactions - Transaction history
GET /customers/{id}/stats - Statistics
POST /customers/{id}/notes - Add note
GET /customers/{id}/notes - Get notes

POST /customers/{id}/documents - Upload document
GET /customers/{id}/documents - List documents
PUT /customers/documents/{doc_id}/verify - Verify document
```

**Business Rules:**
- Duplicate check على national_id
- Customer مربوط بـ branch
- Transaction history tracking
- Risk assessment based on activity

**Output Requirements:**
- ✅ Complete service layer
- ✅ API endpoints
- ✅ Search functionality (name, phone, national_id)
- ✅ Integration tests
```

---

## 💳 PHASE 6: Transaction Management Module
**المدة:** 5-6 أيام | **الأولوية:** CRITICAL | **Dependencies:** Phase 2, 3, 4, 5

### Component 6.1: Transaction Base Models
**المدة:** 6-8 ساعات

```markdown
=== PROMPT FOR CHAT 6.1 ===

**Context:**
Branch و Customer systems جاهزة. نبدأ بـ core التطبيق: المعاملات المالية.

**المطلوب:**

1. **Transaction Base Model** (`app/db/models/transaction.py`):
```python
Base Transaction (Single Table Inheritance):
- id (UUID)
- transaction_number (unique: TRX-20250109-00001)
- transaction_type (enum: income, expense, exchange, transfer)
- branch_id (FK -> Branch)
- user_id (FK -> User) - who executed
- customer_id (FK -> Customer) - nullable
- status (pending, completed, cancelled, failed)
- amount (Decimal 15,2)
- currency_id (FK -> Currency)
- reference_number (optional, external)
- notes (text)
- transaction_date
- completed_at
- cancelled_at
- cancelled_by (FK -> User)
- cancellation_reason
```

2. **Income Transaction:**
```python
Additional Fields:
- income_category (service_fee, commission, other)
- income_source (optional description)
```

3. **Expense Transaction:**
```python
Additional Fields:
- expense_category (rent, salary, utilities, other)
- expense_to (payee name)
- approval_required (boolean)
- approved_by (FK -> User)
- approved_at
```

4. **Exchange Transaction (التحويل بين العملات):**
```python
Additional Fields:
- from_currency_id (FK -> Currency)
- to_currency_id (FK -> Currency)
- from_amount (Decimal)
- to_amount (Decimal)
- exchange_rate_used (Decimal) - snapshot
- commission_amount (Decimal)
- commission_percentage (Decimal)
```

5. **Transfer Transaction (بين الفروع أو الخزينة):**
```python
Additional Fields:
- from_branch_id (FK -> Branch)
- to_branch_id (FK -> Branch)
- transfer_type (branch_to_branch, vault_to_branch, branch_to_vault)
- received_by (FK -> User) - at destination
- received_at
```

**Critical Requirements:**
- Unique transaction_number generation
- State machine للـ status transitions
- Audit trail لكل تغيير
- Cannot modify completed transactions

**Output Requirements:**
- ✅ All transaction models
- ✅ Status state machine
- ✅ Migration script
- ✅ Schemas for each type
- ✅ Test cases
```

---

### Component 6.2: Transaction Service - Core Logic
**المدة:** 8-10 ساعات

```markdown
=== PROMPT FOR CHAT 6.2 ===

**Context:**
Transaction models جاهزة. نحتاج Business logic للمعاملات (أهم جزء في النظام).

**المطلوب:**

1. **Transaction Service** (`app/services/transaction_service.py`):
```python
CRITICAL - All operations MUST be atomic:

create_income(branch_id, amount, currency, category, user):
  1. Validate inputs
  2. Generate transaction_number
  3. Start DB transaction
  4. Create income record
  5. Update branch_balance (+amount)
  6. Create balance_history entry
  7. Commit or rollback
  
create_expense(branch_id, amount, currency, category, payee, user):
  1. Check branch balance (sufficient funds)
  2. Generate transaction_number
  3. Start DB transaction
  4. Create expense record
  5. Update branch_balance (-amount)
  6. Create balance_history
  7. Handle approval workflow if required
  8. Commit or rollback

create_exchange(branch_id, customer_id, from_currency, to_currency, 
                from_amount, user):
  1. Get latest exchange rate
  2. Calculate to_amount and commission
  3. Check branch has from_currency balance
  4. Generate transaction_number
  5. Start DB transaction
  6. Create exchange record
  7. Update branch balance (-from_amount in from_currency)
  8. Update branch balance (+to_amount in to_currency)
  9. Create commission income (if applicable)
  10. Create balance_history entries
  11. Commit or rollback

create_transfer(from_branch, to_branch, amount, currency, user):
  1. Check from_branch balance
  2. Generate transaction_number
  3. Start DB transaction
  4. Create transfer record (status: pending)
  5. Reserve balance in from_branch
  6. Notify to_branch for reception
  7. Commit
  
  # Separate endpoint to complete transfer
  complete_transfer(transfer_id, received_by_user):
  8. Start DB transaction
  9. Update from_branch balance (-amount)
  10. Update to_branch balance (+amount)
  11. Update transfer status (completed)
  12. Release reserved balance
  13. Commit or rollback

cancel_transaction(transaction_id, reason, user):
  - Only pending transactions
  - Reverse all balance changes
  - Mark as cancelled with audit trail
```

2. **Transaction Repository:**
   - Complex queries (filtering, pagination)
   - Transaction history
   - Statistics aggregation

3. **Validation Service:**
```python
- validate_sufficient_balance()
- validate_exchange_rate()
- validate_transaction_limits(branch, amount)
- check_duplicate_transaction(reference_number)
```

**Critical Error Handling:**
- Rollback على أي خطأ
- Detailed error messages
- Balance consistency checks
- Retry mechanism للـ deadlocks

**Output Requirements:**
- ✅ Complete service layer
- ✅ Atomic operations
- ✅ Error handling
- ✅ Extensive unit tests
- ✅ Integration tests (concurrent scenarios)
```

---

### Component 6.3: Transaction API Endpoints
**المدة:** 4-5 ساعات

```markdown
=== PROMPT FOR CHAT 6.3 ===

**Context:**
Transaction service جاهز. نحتاج API endpoints.

**المطلوب:**

**API Endpoints** (`app/api/v1/endpoints/transactions.py`):

```python
# Income
POST /transactions/income
GET /transactions/income
GET /transactions/income/{id}

# Expense
POST /transactions/expense - Create expense
PUT /transactions/expense/{id}/approve - Approve [manager+]
GET /transactions/expense

# Exchange
POST /transactions/exchange - Execute exchange
GET /transactions/exchange
GET /transactions/exchange/{id}
GET /transactions/exchange/rate-preview - Preview before execution

# Transfer
POST /transactions/transfer - Initiate transfer
PUT /transactions/transfer/{id}/receive - Complete transfer
GET /transactions/transfer
GET /transactions/transfer/{id}

# General
GET /transactions - List all (with filters)
GET /transactions/{id} - Get details
PUT /transactions/{id}/cancel - Cancel transaction
GET /transactions/stats - Statistics

# Filters:
- transaction_type
- branch_id
- customer_id
- status
- date_range
- amount_range
- currency_id
```

**Response Format:**
```json
{
  "transaction_id": "uuid",
  "transaction_number": "TRX-20250109-00001",
  "type": "exchange",
  "status": "completed",
  "branch": {...},
  "customer": {...},
  "details": {
    "from_currency": "USD",
    "to_currency": "TRY",
    "from_amount": 100.00,
    "to_amount": 3250.00,
    "rate": 32.50,
    "commission": 5.00
  },
  "executed_by": {...},
  "executed_at": "2025-01-09T10:30:00Z"
}
```

**Output Requirements:**
- ✅ All endpoints implemented
- ✅ Comprehensive request/response examples
- ✅ OpenAPI documentation
- ✅ Postman collection
- ✅ Error response examples
```

---

## 🏛️ PHASE 7: Vault Management Module
**المدة:** 2-3 أيام | **الأولوية:** MEDIUM | **Dependencies:** Phase 4, 6

### Component 7.1: Vault Models & Operations
**المدة:** 6-7 ساعات

```markdown
=== PROMPT FOR CHAT 7.1 ===

**Context:**
Branch و Transaction systems جاهزة. نحتاج Central Vault management.

**المطلوب:**

1. **Vault Model** (`app/db/models/vault.py`):
```python
Fields:
- id (UUID)
- vault_type (main, branch) - main vault واحد فقط
- branch_id (FK -> Branch) - nullable for main vault
- is_active
```

2. **VaultBalance Model:**
```python
Fields:
- id (UUID)
- vault_id (FK -> Vault)
- currency_id (FK -> Currency)
- balance (Decimal 15,2)
- last_updated
```

3. **VaultTransfer Model:**
```python
Fields:
- id (UUID)
- transfer_number (unique: VTR-20250109-00001)
- from_vault_id (FK -> Vault)
- to_vault_id (FK -> Vault) - nullable for branch
- to_branch_id (FK -> Branch) - nullable
- currency_id
- amount
- transfer_type (vault_to_vault, vault_to_branch, branch_to_vault)
- status (pending, in_transit, completed, cancelled)
- initiated_by (FK -> User)
- approved_by (FK -> User) - for large amounts
- received_by (FK -> User)
- initiated_at
- approved_at
- completed_at
- notes
```

**Business Rules:**
- Main vault balance tracking
- Transfer approval workflow (amount thresholds)
- Security logging لكل عملية
- Balance reconciliation

**Output Requirements:**
- ✅ Models complete
- ✅ Migration script
- ✅ Approval workflow logic
- ✅ Test cases
```

---

### Component 7.2: Vault Service & API
**المدة:** 4-5 ساعات

```markdown
=== PROMPT FOR CHAT 7.2 ===

**Context:**
Vault models جاهزة. نحتاج Service و API.

**المطلوب:**

1. **Vault Service:**
```python
Methods:
- get_vault_balance(vault_id, currency_id)
- transfer_to_branch(vault, branch, currency, amount, user)
- transfer_from_branch(branch, vault, currency, amount, user)
- approve_transfer(transfer_id, user)
- complete_transfer(transfer_id, user)
- reconcile_vault_balance(vault_id)
- get_transfer_history(vault_id, date_range)
```

2. **API Endpoints** (`app/api/v1/endpoints/vault.py`):
```python
GET /vault - Main vault details
GET /vault/balances - All currency balances
GET /vault/balances/{currency} - Specific currency

POST /vault/transfer/to-branch - Send to branch
POST /vault/transfer/from-branch - Receive from branch
PUT /vault/transfer/{id}/approve - Approve transfer [manager+]
PUT /vault/transfer/{id}/complete - Complete transfer
GET /vault/transfers - Transfer history

GET /vault/reconciliation - Reconciliation report
POST /vault/reconciliation - Perform reconciliation
```

**Output Requirements:**
- ✅ Service layer complete
- ✅ API endpoints
- ✅ Approval workflow
- ✅ Integration tests
```

---

## 📊 PHASE 8: Reporting & Analytics Module
**المدة:** 4-5 أيام | **الأولوية:** MEDIUM | **Dependencies:** All previous phases

### Component 8.1: Report Models & Data Aggregation
**المدة:** 6-8 ساعات

```markdown
=== PROMPT FOR CHAT 8.1 ===

**Context:**
كل الأنظمة الأساسية جاهزة. نحتاج Reporting system شامل.

**المطلوب:**

1. **Report Service** (`app/services/report_service.py`):
```python
Financial Reports:
- daily_transaction_summary(branch_id, date)
- monthly_revenue_report(branch_id, year, month)
- branch_performance_comparison(date_range)
- currency_exchange_trends(currency_pair, date_range)
- customer_transaction_analysis(customer_id, date_range)

Balance Reports:
- branch_balance_snapshot(branch_id, date)
- vault_balance_summary(date)
- low_balance_alert_report()
- balance_movement_report(branch_id, currency, date_range)

User Activity Reports:
- user_activity_log(user_id, date_range)
- transaction_by_user(user_id, date_range)
- audit_trail_report(entity_type, entity_id, date_range)

Analytics:
- calculate_commission_earned(branch_id, date_range)
- identify_high_value_customers(branch_id)
- transaction_volume_trends(branch_id, period)
- exchange_rate_volatility_analysis(currency_pair, period)
```

2. **Report Export Service:**
```python
Export Formats:
- export_to_json(report_data)
- export_to_excel(report_data, template)
- export_to_pdf(report_data, template)

Libraries:
- openpyxl (Excel)
- reportlab (PDF)
- jinja2 (Templates)
```

3. **Scheduled Reports:**
   - Daily EOD (End of Day) reports
   - Weekly summaries
   - Monthly financial statements

**Output Requirements:**
- ✅ Report service with all calculations
- ✅ Export functionality (all formats)
- ✅ Test reports with sample data
```

---

### Component 8.2: Report API & Dashboard Data
**المدة:** 5-6 ساعات

```markdown
=== PROMPT FOR CHAT 8.2 ===

**Context:**
Report service جاهز. نحتاج API endpoints و Dashboard data.

**المطلوب:**

1. **Report Endpoints** (`app/api/v1/endpoints/reports.py`):
```python
# Financial Reports
GET /reports/daily-summary
GET /reports/monthly-revenue
GET /reports/branch-performance
GET /reports/exchange-trends

# Balance Reports
GET /reports/balance-snapshot
GET /reports/balance-movement
GET /reports/low-balance-alerts

# User Reports
GET /reports/user-activity
GET /reports/audit-trail

# Export
POST /reports/export
  Body: {
    "report_type": "daily_summary",
    "format": "pdf",
    "filters": {...}
  }
```

2. **Dashboard API** (`app/api/v1/endpoints/dashboard.py`):
```python
GET /dashboard/overview
  Response: {
    "total_transactions_today": 150,
    "total_revenue_today": 5000,
    "active_branches": 5,
    "low_balance_alerts": 2,
    "pending_approvals": 3,
    "top_currencies": [...]
  }

GET /dashboard/charts
  - Transaction volume chart (daily/weekly/monthly)
  - Revenue trend chart
  - Currency distribution pie chart
  - Branch comparison bar chart
```

**Output Requirements:**
- ✅ All report endpoints
- ✅ Dashboard data APIs
- ✅ Export functionality working
- ✅ Sample reports (PDF, Excel)
- ✅ Postman collection
```

---

## 🧪 PHASE 9: Testing & Quality Assurance
**المدة:** 3-4 أيام | **الأولوية:** HIGH | **Dependencies:** All phases

### Component 9.1: Comprehensive Test Suite
**المدة:** Full phase

```markdown
=== PROMPT FOR CHAT 9.1 ===

**Context:**
كل الـ features مبنية. نحتاج Comprehensive testing.

**المطلوب:**

1. **Unit Tests** (`tests/unit/`):
```python
Test Coverage:
- Models: validation, relationships, constraints
- Services: business logic, edge cases
- Utilities: helpers, validators, generators
- Schemas: Pydantic validation

Target: 80%+ code coverage
```

2. **Integration Tests** (`tests/integration/`):
```python
Critical Flows:
- User authentication & authorization
- Currency exchange end-to-end
- Branch transfer workflow
- Transaction lifecycle
- Report generation

Focus: API endpoints + database interactions
```

3. **Performance Tests** (`tests/performance/`):
```python
Load Testing:
- Concurrent transactions (100+ simultaneous)
- Database query performance
- API response times
- Report generation speed

Tools: locust or pytest-benchmark
```

4. **Security Tests:**
```python
Security Checks:
- JWT token validation
- Permission bypass attempts
- SQL injection attempts
- Rate limiting
- Password strength enforcement
```

**Test Data:**
- Faker library for realistic data
- Fixtures for common scenarios
- Database seeding scripts

**Output Requirements:**
- ✅ Test suite > 80% coverage
- ✅ CI/CD integration (GitHub Actions)
- ✅ Performance benchmarks
- ✅ Security test report
```

---

## 🚀 PHASE 10: Deployment & DevOps
**المدة:** 2-3 أيام | **الأولوية:** HIGH | **Dependencies:** Phase 9

### Component 10.1: Production Deployment Setup
**المدة:** Full phase

```markdown
=== PROMPT FOR CHAT 10.1 ===

**Context:**
Application جاهز و tested. نحتاج Production deployment.

**المطلوب:**

1. **Docker Production Setup:**
```yaml
docker-compose.yml:
  - FastAPI app (gunicorn)
  - PostgreSQL with persistence
  - Redis for caching
  - Nginx reverse proxy
  - Monitoring (Prometheus + Grafana)
```

2. **Environment Configuration:**
```bash
Production .env:
- Database credentials (secure)
- JWT secret keys (strong)
- API rate limits
- CORS settings
- Logging level
```

3. **Database Optimization:**
```sql
- Indexes on frequently queried columns
- Partitioning for large tables
- Connection pooling settings
- Backup strategy
```

4. **Security Hardening:**
```python
- HTTPS enforcement
- Security headers
- Rate limiting
- IP whitelisting (admin endpoints)
- Database encryption at rest
```

5. **Monitoring & Logging:**
```yaml
Setup:
- Application logs (structured JSON)
- Error tracking (Sentry)
- Performance monitoring (Prometheus)
- Dashboards (Grafana)
- Alerting (critical errors, downtime)
```

6. **Backup & Recovery:**
```bash
Scripts:
- Daily database backups
- Transaction logs backup
- Disaster recovery plan
- Database restore procedures
```

7. **CI/CD Pipeline:**
```yaml
GitHub Actions:
  - Run tests on PR
  - Build Docker image
  - Push to registry
  - Deploy to staging
  - Deploy to production (manual approval)
```

**Output Requirements:**
- ✅ Production-ready docker-compose
- ✅ Deployment scripts
- ✅ Monitoring dashboards
- ✅ Backup automation
- ✅ CI/CD pipeline
- ✅ Documentation (deployment guide)
```

---

## 📚 PHASE 11: Documentation & Handover
**المدة:** 2 أيام | **الأولوية:** MEDIUM | **Dependencies:** All phases

### Component 11.1: Complete Documentation
**المدة:** Full phase

```markdown
=== PROMPT FOR CHAT 11.1 ===

**Context:**
System كامل و deployed. نحتاج Documentation شامل.

**المطلوب:**

1. **Technical Documentation:**
```markdown
docs/technical/:
- Architecture overview
- Database schema diagrams
- API documentation (enhanced Swagger)
- Service layer documentation
- Security implementation details
- Performance optimization notes
```

2. **User Manuals:**
```markdown
docs/user-manuals/:
- Admin guide (system management)
- Manager guide (branch operations)
- Teller guide (daily operations)
- Report generation guide
```

3. **Developer Guide:**
```markdown
docs/developer/:
- Setup instructions (development)
- Code structure explanation
- Adding new features guide
- Testing guidelines
- Deployment procedures
```

4. **API Documentation:**
```markdown
Enhanced Swagger:
- Request/response examples
- Error codes reference
- Rate limiting info
- Authentication guide
- Postman collection
```

5. **Operational Runbooks:**
```markdown
docs/operations/:
- Daily operations checklist
- Troubleshooting guide
- Common errors & solutions
- Database maintenance
- Backup & restore procedures
```

**Output Requirements:**
- ✅ Complete technical docs
- ✅ User manuals (3 roles)
- ✅ Developer onboarding guide
- ✅ API reference
- ✅ Operational runbooks
- ✅ Video tutorials (optional)
```

---

## 📋 SUMMARY: Quick Reference

```markdown
=== PHASES AT A GLANCE ===

Phase 1: Foundation (2-3 days)
  ├── 1.1: Project structure & config
  └── 1.2: Database base models

Phase 2: Authentication (3-4 days)
  ├── 2.1: User & Role models
  ├── 2.2: JWT authentication
  └── 2.3: RBAC & permissions

Phase 3: Currency (2-3 days)
  ├── 3.1: Currency models
  └── 3.2: Currency service & API

Phase 4: Branches (3-4 days)
  ├── 4.1: Branch models & balances
  └── 4.2: Branch service & operations

Phase 5: Customers (2 days)
  ├── 5.1: Customer model & KYC
  └── 5.2: Customer service & API

Phase 6: Transactions (5-6 days) ⚠️ CRITICAL
  ├── 6.1: Transaction models
  ├── 6.2: Transaction service (core logic)
  └── 6.3: Transaction API

Phase 7: Vault (2-3 days)
  ├── 7.1: Vault models & operations
  └── 7.2: Vault service & API

Phase 8: Reports (4-5 days)
  ├── 8.1: Report models & aggregation
  └── 8.2: Report API & dashboard

Phase 9: Testing (3-4 days)
  └── 9.1: Comprehensive test suite

Phase 10: Deployment (2-3 days)
  └── 10.1: Production setup

Phase 11: Documentation (2 days)
  └── 11.1: Complete documentation

Total Estimated Time: 30-35 days
Critical Path: Phases 1 → 2 → 6 → 9 → 10
```

---

## 🎯 USAGE INSTRUCTIONS

**كيفية استخدام هذا الدليل:**

1. **ابدأ بـ Phase 1, Component 1.1**
2. **افتح محادثة جديدة مع Claude**
3. **انسخ الـ PROMPT المحدد**
4. **الصق في Claude وأضف:**
   ```
   المشروع: CEMS (Currency Exchange Management System)
   GitHub: https://github.com/[your-repo]
   
   [الـ PROMPT من الأعلى]
   
   أريد:
   - كود كامل في Artifacts
   - تعليمات واضحة
   - أمثلة للاختبار
   ```
5. **احفظ المخرجات في GitHub**
6. **انتقل للـ Component التالي**

**نصائح:**
- ✅ اختبر كل component قبل الانتقال للتالي
- ✅ احتفظ بـ context من المراحل السابقة
- ✅ وثق أي تغييرات عن الخطة الأصلية
- ✅ استخدم Git branches لكل component

---

## 🔗 DEPENDENCIES MAP

```
Phase 1 (Foundation)
  ↓
Phase 2 (Auth) ←─────────────┐
  ↓                          │
Phase 3 (Currency)           │
  ↓                          │
Phase 4 (Branches) ←─────────┤
  ↓                          │
Phase 5 (Customers)          │
  ↓                          │
Phase 6 (Transactions) ←─────┤ (uses all previous)
  ↓                          │
Phase 7 (Vault) ←────────────┤
  ↓                          │
Phase 8 (Reports) ←──────────┘ (uses all)
  ↓
Phase 9 (Testing) ← (tests everything)
  ↓
Phase 10 (Deployment)
  ↓
Phase 11 (Documentation)
```

**يمكنك العمل بالتوازي على:**
- Phase 3 & Phase 5 (بعد Phase 2)
- Phase 7 & Phase 8 (بعد Phase 6)

---

END OF ROADMAP
Version: 1.0
Last Updated: 2025-01-09
