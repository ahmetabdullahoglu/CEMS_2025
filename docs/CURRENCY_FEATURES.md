# Advanced Currency Features

## Overview

تم إضافة ميزات متقدمة جديدة لخدمة العملات (`CurrencyService`) تتيح:

1. **التحويل عبر عملة وسيطة (USD)** - Cross-rate conversion via USD intermediary
2. **تجميع الأرصدة بعملة مستهدفة** - Balance aggregation in target currency

---

## 1. التحويل عبر عملة وسيطة (Cross-Rate Conversion)

### المشكلة
عندما لا يتوفر سعر صرف مباشر بين عملتين، كان النظام يفشل في إجراء التحويل.

**مثال:**
- نريد تحويل AED → EGP
- لا يوجد سعر صرف مباشر AED/EGP
- لكن يوجد: AED/USD و USD/EGP

### الحل
النظام الآن يستخدم الدولار الأمريكي (USD) كعملة وسيطة تلقائياً:
```
AED → USD → EGP
```

### كيفية الاستخدام

#### الطريقة 1: استخدام `get_latest_rate()`

```python
from app.services.currency_service import CurrencyService

# إنشاء الخدمة
service = CurrencyService(db)

# الحصول على سعر الصرف مع دعم العملة الوسيطة
rate = await service.get_latest_rate(
    from_currency_code="AED",
    to_currency_code="EGP",
    use_intermediary=True  # تفعيل استخدام USD كوسيط (افتراضي)
)

print(f"Rate: {rate.rate}")
print(f"Notes: {rate.notes}")  # يوضح إذا تم الحساب عبر USD
```

**مثال النتيجة:**
```
Rate: 13.35
Notes: Calculated via USD: AED->USD (0.272) * USD->EGP (49.00)
```

#### الطريقة 2: استخدام `convert_amount()`

```python
# تحويل مبلغ محدد
result = await service.convert_amount(
    amount=Decimal("1000.00"),
    from_currency_code="AED",
    to_currency_code="EGP",
    use_intermediary=True,  # افتراضي
    use_buy_rate=False,
    use_sell_rate=False
)

print(f"From: {result['from_amount']} {result['from_currency']}")
print(f"To: {result['to_amount']} {result['to_currency']}")
print(f"Rate: {result['rate']}")
print(f"Via Intermediary: {result['via_intermediary']}")  # True إذا استخدم USD
```

**مثال النتيجة:**
```json
{
    "from_currency": "AED",
    "to_currency": "EGP",
    "from_amount": 1000.00,
    "rate": 13.35,
    "to_amount": 13350.00,
    "rate_type": "standard",
    "via_intermediary": true,
    "notes": "Calculated via USD: AED->USD (0.272) * USD->EGP (49.00)"
}
```

### أمثلة عملية

#### مثال 1: صرف عملات الخليج إلى الجنيه المصري
```python
# SAR → EGP
conversion = await service.convert_amount(
    amount=Decimal("1000.00"),
    from_currency_code="SAR",
    to_currency_code="EGP"
)
# النتيجة: 1000 SAR = 13,070 EGP (عبر USD)
```

#### مثال 2: الين الياباني إلى الريال السعودي
```python
# JPY → SAR
conversion = await service.convert_amount(
    amount=Decimal("10000.00"),
    from_currency_code="JPY",
    to_currency_code="SAR"
)
# النتيجة: 10,000 JPY = 250 SAR (عبر USD)
```

---

## 2. تجميع الأرصدة بعملة مستهدفة (Balance Aggregation)

### المشكلة
عندما يكون لديك أرصدة بعملات متعددة، تحتاج لمعرفة الإجمالي بعملة واحدة موحدة.

**مثال:**
- رصيد فرع: 500,000 TRY + 50,000 USD + 30,000 EUR + 100,000 EGP
- كم المجموع بالدولار؟

### الحل
دالة `aggregate_balances()` تقوم بـ:
1. تحويل كل رصيد إلى العملة المستهدفة
2. جمع جميع الأرصدة المحولة
3. توفير تفاصيل كل عملية تحويل

### كيفية الاستخدام

```python
from decimal import Decimal

# تحديد الأرصدة
balances = [
    {'currency_code': 'TRY', 'amount': Decimal('500000.00')},
    {'currency_code': 'USD', 'amount': Decimal('50000.00')},
    {'currency_code': 'EUR', 'amount': Decimal('30000.00')},
    {'currency_code': 'EGP', 'amount': Decimal('100000.00')},
    {'currency_code': 'SAR', 'amount': Decimal('25000.00')},
    {'currency_code': 'GBP', 'amount': Decimal('5000.00')},
]

# تجميع الأرصدة بالدولار
result = await service.aggregate_balances(
    balances=balances,
    target_currency_code="USD",  # العملة المستهدفة (افتراضي: USD)
    use_buy_rate=False,
    use_sell_rate=False
)

print(f"Total: {result['total_amount']:,.2f} {result['target_currency']}")
print(f"\nBreakdown:")
for item in result['breakdown']:
    print(f"  {item['currency']}: {item['original_amount']:,.2f} "
          f"→ {item['converted_amount']:,.2f} USD "
          f"(rate: {item['rate_used']})")
```

**مثال النتيجة:**
```
Total: 118,676.47 USD

Breakdown:
  TRY: 500,000.00 → 15,384.62 USD (rate: 0.0308)
  USD: 50,000.00 → 50,000.00 USD (rate: 1.0)
  EUR: 30,000.00 → 32,610.00 USD (rate: 1.087)
  EGP: 100,000.00 → 2,040.00 USD (rate: 0.0204) (via USD)
  SAR: 25,000.00 → 6,675.00 USD (rate: 0.267)
  GBP: 5,000.00 → 6,330.00 USD (rate: 1.266)
```

### أمثلة متقدمة

#### مثال 1: تجميع بعملات مختلفة

```python
# التجميع باليورو
result_eur = await service.aggregate_balances(balances, "EUR")

# التجميع بالليرة التركية
result_try = await service.aggregate_balances(balances, "TRY")

# التجميع بالجنيه المصري
result_egp = await service.aggregate_balances(balances, "EGP")
```

#### مثال 2: استخدام أسعار الشراء/البيع

```python
# استخدام سعر الشراء
result_buy = await service.aggregate_balances(
    balances=balances,
    target_currency_code="USD",
    use_buy_rate=True
)

# استخدام سعر البيع
result_sell = await service.aggregate_balances(
    balances=balances,
    target_currency_code="USD",
    use_sell_rate=True
)
```

#### مثال 3: تجميع أرصدة الفروع

```python
from app.repositories.branch_repo import BranchRepository

# الحصول على جميع أرصدة الفرع
branch_repo = BranchRepository(db)
branch_balances = await branch_repo.get_branch_balances(branch_id)

# تحويل إلى الصيغة المطلوبة
balances = [
    {
        'currency_code': balance.currency.code,
        'amount': balance.balance
    }
    for balance in branch_balances
]

# تجميع الأرصدة
total = await service.aggregate_balances(balances, "USD")

print(f"Total branch balance: {total['total_amount']:,.2f} USD")
```

---

## 3. استخدام الميزات في API Endpoints

### مثال: Endpoint لتجميع أرصدة فرع

```python
from fastapi import APIRouter, Depends
from app.services.currency_service import CurrencyService

router = APIRouter()

@router.get("/branches/{branch_id}/total-balance")
async def get_branch_total_balance(
    branch_id: UUID,
    target_currency: str = "USD",
    db: AsyncSession = Depends(get_db)
):
    """Get total branch balance in specified currency"""

    # Get branch balances
    branch_repo = BranchRepository(db)
    balances_data = await branch_repo.get_branch_balances(branch_id)

    # Convert to format for aggregation
    balances = [
        {
            'currency_code': b.currency.code,
            'amount': b.balance
        }
        for b in balances_data
    ]

    # Aggregate
    currency_service = CurrencyService(db)
    result = await currency_service.aggregate_balances(
        balances=balances,
        target_currency_code=target_currency
    )

    return {
        "branch_id": branch_id,
        "target_currency": target_currency,
        "total_balance": result['total_amount'],
        "breakdown": result['breakdown']
    }
```

### مثال: Endpoint لتحويل عملات

```python
@router.post("/currency/convert")
async def convert_currency(
    from_currency: str,
    to_currency: str,
    amount: Decimal,
    db: AsyncSession = Depends(get_db)
):
    """Convert amount between currencies"""

    service = CurrencyService(db)

    result = await service.convert_amount(
        amount=amount,
        from_currency_code=from_currency,
        to_currency_code=to_currency,
        use_intermediary=True
    )

    return {
        "from": {
            "currency": result['from_currency'],
            "amount": result['from_amount']
        },
        "to": {
            "currency": result['to_currency'],
            "amount": result['to_amount']
        },
        "rate": result['rate'],
        "via_intermediary": result.get('via_intermediary', False)
    }
```

---

## 4. آلية العمل التفصيلية

### 4.1 البحث عن سعر الصرف

النظام يتبع الخطوات التالية للحصول على سعر الصرف:

1. **البحث عن سعر مباشر**: `FROM → TO`
2. **البحث عن السعر المعكوس**: `TO → FROM` (ثم حساب المقلوب)
3. **البحث عن سعر عبر USD** (إذا كان مفعلاً):
   - `FROM → USD`
   - `USD → TO`
   - حساب: `rate = (FROM→USD) × (USD→TO)`

### 4.2 حساب أسعار الشراء والبيع

عند استخدام عملة وسيطة:
- **Buy Rate**: `buy_rate = from_to_usd_buy × usd_to_to_buy`
- **Sell Rate**: `sell_rate = from_to_usd_sell × usd_to_to_sell`

### 4.3 معالجة الأخطاء

```python
try:
    result = await service.convert_amount(
        amount=amount,
        from_currency_code="UNKNOWN",
        to_currency_code="USD"
    )
except ResourceNotFoundError as e:
    # العملة غير موجودة
    print(f"Currency not found: {e}")
except ValidationError as e:
    # بيانات غير صحيحة (مثل مبلغ سالب)
    print(f"Invalid data: {e}")
```

---

## 5. ملاحظات مهمة

### ⚠️ نقاط يجب مراعاتها

1. **الدقة في الحسابات**:
   - الحساب عبر عملة وسيطة قد يقدم نتيجة مختلفة قليلاً عن السعر المباشر
   - الفرق عادة ضئيل جداً ومقبول

2. **الأداء**:
   - البحث عن سعر مباشر أسرع من الحساب عبر وسيط
   - يُفضل إضافة أسعار صرف مباشرة للأزواج الأكثر استخداماً

3. **توفر USD**:
   - يجب أن تكون عملة USD موجودة في النظام
   - يجب توفر أسعار صرف USD مع جميع العملات الأخرى

4. **التحديث التلقائي**:
   - النظام يستخدم أحدث أسعار الصرف المتاحة
   - يُنصح بتحديث أسعار الصرف بانتظام

---

## 6. أمثلة كاملة

### مثال شامل: تقرير أرصدة جميع الفروع

```python
async def generate_branches_balance_report(
    db: AsyncSession,
    target_currency: str = "USD"
):
    """إنشاء تقرير شامل لأرصدة جميع الفروع"""

    branch_repo = BranchRepository(db)
    currency_service = CurrencyService(db)

    # الحصول على جميع الفروع
    branches = await branch_repo.get_all_branches()

    report = {
        'target_currency': target_currency,
        'branches': [],
        'grand_total': Decimal('0')
    }

    for branch in branches:
        # الحصول على أرصدة الفرع
        balances_data = await branch_repo.get_branch_balances(branch.id)

        balances = [
            {
                'currency_code': b.currency.code,
                'amount': b.balance
            }
            for b in balances_data
        ]

        # تجميع الأرصدة
        aggregated = await currency_service.aggregate_balances(
            balances=balances,
            target_currency_code=target_currency
        )

        report['branches'].append({
            'branch_code': branch.code,
            'branch_name': branch.name_en,
            'total': aggregated['total_amount'],
            'breakdown': aggregated['breakdown']
        })

        report['grand_total'] += aggregated['total_amount']

    return report
```

**الاستخدام:**
```python
report = await generate_branches_balance_report(db, "USD")

print(f"Total Company Balance: {report['grand_total']:,.2f} USD")
print("\nBranches:")
for branch in report['branches']:
    print(f"  {branch['branch_code']}: {branch['total']:,.2f} USD")
```

---

## 7. الاختبار

لاختبار الميزات الجديدة، استخدم السكريبت المرفق:

```bash
python scripts/test_currency_features.py
```

السكريبت يختبر:
- ✅ التحويل المباشر بين العملات
- ✅ التحويل عبر USD الوسيط
- ✅ تجميع الأرصدة بعملات مختلفة
- ✅ سيناريوهات محددة للتحويل المتقاطع

---

## 8. الخلاصة

الميزات الجديدة توفر:

✅ **مرونة أكبر** في التعامل مع أزواج العملات غير المتوفرة
✅ **تقارير شاملة** لمجموع الأرصدة بأي عملة
✅ **شفافية** في العمليات الحسابية (توضيح إذا تم استخدام وسيط)
✅ **دعم تلقائي** للعملات الجديدة بدون الحاجة لإضافة جميع الأزواج

هذه الميزات تجعل نظام CEMS أكثر قوة ومرونة في التعامل مع العملات المتعددة!
