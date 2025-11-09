"""
CEMS Report Service Tests
=========================
Comprehensive tests for report generation and export
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any

from report_service import ReportService
from report_export_service import ReportExportService, get_export_filename


# ==================== FIXTURES ====================

@pytest.fixture
def sample_report_data() -> Dict[str, Any]:
    """Sample report data for testing"""
    return {
        'title': 'Daily Transaction Summary',
        'date': date.today().isoformat(),
        'branch_id': 'branch-001',
        'summary': {
            'total_transactions': 150,
            'total_revenue': 5000.00,
            'average_commission': 33.33,
            'total_volume': 150000.00
        },
        'date_range': {
            'start': '2025-01-01',
            'end': '2025-01-31'
        },
        'data': [
            {
                'date': '2025-01-15',
                'transaction_count': 25,
                'revenue': 850.00,
                'volume': 25000.00
            },
            {
                'date': '2025-01-16',
                'transaction_count': 30,
                'revenue': 1020.00,
                'volume': 30000.00
            },
            {
                'date': '2025-01-17',
                'transaction_count': 28,
                'revenue': 945.00,
                'volume': 28000.00
            }
        ]
    }


@pytest.fixture
def financial_report_data() -> Dict[str, Any]:
    """Financial report data for testing"""
    return {
        'title': 'Monthly Financial Report',
        'year': 2025,
        'month': 1,
        'branch_id': 'branch-001',
        'summary': {
            'total_revenue': 15000.00,
            'total_transactions': 450,
            'average_daily_revenue': 500.00,
            'max_daily_revenue': 1200.00,
            'min_daily_revenue': 150.00
        },
        'daily_breakdown': {
            1: {'revenue': 500.00, 'count': 15},
            2: {'revenue': 650.00, 'count': 20},
            3: {'revenue': 800.00, 'count': 25}
        }
    }


@pytest.fixture
def export_service():
    """Export service fixture"""
    return ReportExportService()


# ==================== JSON EXPORT TESTS ====================

def test_json_export_pretty(export_service, sample_report_data):
    """Test JSON export with pretty formatting"""
    result = export_service.export_to_json(sample_report_data, pretty=True)
    
    assert result is not None
    assert isinstance(result, str)
    assert 'Daily Transaction Summary' in result
    assert 'total_transactions' in result
    
    # Check formatting
    assert '\n' in result  # Pretty formatting includes newlines
    assert '  ' in result  # Pretty formatting includes indentation


def test_json_export_compact(export_service, sample_report_data):
    """Test JSON export without formatting"""
    result = export_service.export_to_json(sample_report_data, pretty=False)
    
    assert result is not None
    assert isinstance(result, str)
    
    # Compact format has fewer characters
    pretty = export_service.export_to_json(sample_report_data, pretty=True)
    assert len(result) < len(pretty)


def test_json_export_decimal_handling(export_service):
    """Test that Decimal values are properly converted"""
    data = {
        'amount': Decimal('1234.56'),
        'rate': Decimal('1.25')
    }
    
    result = export_service.export_to_json(data)
    assert '1234.56' in result
    assert '1.25' in result


# ==================== EXCEL EXPORT TESTS ====================

def test_excel_export_standard(export_service, sample_report_data):
    """Test Excel export with standard template"""
    result = export_service.export_to_excel(sample_report_data, template='standard')
    
    assert result is not None
    assert hasattr(result, 'read')  # BytesIO object
    assert result.tell() == 0  # Positioned at start
    
    # Check file size (should have content)
    content = result.read()
    assert len(content) > 1000  # Non-trivial file size


def test_excel_export_financial(export_service, financial_report_data):
    """Test Excel export with financial template"""
    result = export_service.export_to_excel(financial_report_data, template='financial')
    
    assert result is not None
    content = result.read()
    assert len(content) > 1000


def test_excel_export_summary(export_service, sample_report_data):
    """Test Excel export with summary template"""
    result = export_service.export_to_excel(sample_report_data, template='summary')
    
    assert result is not None
    content = result.read()
    assert len(content) > 1000


# ==================== PDF EXPORT TESTS ====================

def test_pdf_export_standard(export_service, sample_report_data):
    """Test PDF export with standard template"""
    result = export_service.export_to_pdf(sample_report_data, template='standard')
    
    assert result is not None
    assert hasattr(result, 'read')
    
    content = result.read()
    assert len(content) > 1000
    assert content.startswith(b'%PDF')  # PDF signature


def test_pdf_export_with_large_dataset(export_service, sample_report_data):
    """Test PDF export handles large datasets properly"""
    # Add many records
    large_data = sample_report_data.copy()
    large_data['data'] = [
        {
            'date': f'2025-01-{i:02d}',
            'count': i * 10,
            'revenue': i * 100.00
        }
        for i in range(1, 100)  # 99 records
    ]
    
    result = export_service.export_to_pdf(large_data)
    
    assert result is not None
    content = result.read()
    assert len(content) > 1000


# ==================== HTML TEMPLATE TESTS ====================

def test_html_template_rendering(export_service, sample_report_data):
    """Test HTML template rendering"""
    from report_export_service import STANDARD_HTML_TEMPLATE
    
    result = export_service.export_with_html_template(
        sample_report_data,
        STANDARD_HTML_TEMPLATE
    )
    
    assert result is not None
    assert isinstance(result, str)
    assert '<html>' in result
    assert 'Daily Transaction Summary' in result
    assert 'table' in result.lower()


def test_html_template_custom_helpers(export_service):
    """Test HTML template with custom helper functions"""
    from report_export_service import STANDARD_HTML_TEMPLATE
    
    data = {
        'title': 'Test Report',
        'summary': {
            'revenue': 1234.56,
            'count': 100
        }
    }
    
    result = export_service.export_with_html_template(data, STANDARD_HTML_TEMPLATE)
    
    # Check currency formatting
    assert '$1,234.56' in result or '1234.56' in result


# ==================== HELPER FUNCTION TESTS ====================

def test_get_export_filename_with_timestamp():
    """Test filename generation with timestamp"""
    filename = get_export_filename('daily_summary', 'pdf', timestamp=True)
    
    assert filename.startswith('CEMS_daily_summary_')
    assert filename.endswith('.pdf')
    assert len(filename) > 20  # Has timestamp


def test_get_export_filename_without_timestamp():
    """Test filename generation without timestamp"""
    filename = get_export_filename('monthly_report', 'xlsx', timestamp=False)
    
    assert filename == 'CEMS_monthly_report.xlsx'


# ==================== INTEGRATION TESTS ====================

def test_export_all_formats(export_service, sample_report_data):
    """Test exporting to all formats"""
    # JSON
    json_result = export_service.export_to_json(sample_report_data)
    assert json_result is not None
    
    # Excel
    excel_result = export_service.export_to_excel(sample_report_data)
    assert excel_result is not None
    
    # PDF
    pdf_result = export_service.export_to_pdf(sample_report_data)
    assert pdf_result is not None


def test_export_empty_data(export_service):
    """Test handling of empty data"""
    empty_data = {
        'title': 'Empty Report',
        'summary': {},
        'data': []
    }
    
    # Should not raise errors
    json_result = export_service.export_to_json(empty_data)
    assert json_result is not None
    
    excel_result = export_service.export_to_excel(empty_data)
    assert excel_result is not None
    
    pdf_result = export_service.export_to_pdf(empty_data)
    assert pdf_result is not None


# ==================== PERFORMANCE TESTS ====================

def test_large_json_export_performance(export_service):
    """Test JSON export performance with large dataset"""
    import time
    
    large_data = {
        'title': 'Large Dataset Test',
        'data': [
            {'id': i, 'value': i * 100, 'name': f'Item {i}'}
            for i in range(10000)
        ]
    }
    
    start = time.time()
    result = export_service.export_to_json(large_data)
    elapsed = time.time() - start
    
    assert result is not None
    assert elapsed < 5.0  # Should complete in under 5 seconds


def test_large_excel_export_performance(export_service):
    """Test Excel export performance"""
    import time
    
    large_data = {
        'title': 'Large Excel Test',
        'data': [
            {'date': f'2025-01-{i%28 + 1:02d}', 'amount': i * 100}
            for i in range(1000)
        ]
    }
    
    start = time.time()
    result = export_service.export_to_excel(large_data)
    elapsed = time.time() - start
    
    assert result is not None
    assert elapsed < 10.0  # Excel is slower, allow 10 seconds


# ==================== ERROR HANDLING TESTS ====================

def test_export_handles_none_values(export_service):
    """Test handling of None values in data"""
    data = {
        'title': 'Test Report',
        'summary': {
            'value1': None,
            'value2': 100,
            'value3': None
        }
    }
    
    # Should handle None gracefully
    json_result = export_service.export_to_json(data)
    assert 'null' in json_result or 'None' in json_result


def test_export_handles_special_characters(export_service):
    """Test handling of special characters"""
    data = {
        'title': 'Test Report with Special Chars: @#$%',
        'data': [
            {'name': 'Item with "quotes"', 'value': 100},
            {'name': "Item with 'apostrophe'", 'value': 200}
        ]
    }
    
    json_result = export_service.export_to_json(data)
    assert json_result is not None


# ==================== SAMPLE DATA GENERATION ====================

def generate_sample_daily_summary() -> Dict[str, Any]:
    """Generate sample daily summary report"""
    return {
        'title': 'Daily Transaction Summary',
        'date': date.today().isoformat(),
        'branch_id': 'BR-001',
        'total_transactions': 45,
        'total_revenue': 1500.00,
        'volume_by_currency': {
            'USD': 50000.00,
            'EUR': 30000.00,
            'GBP': 20000.00
        },
        'revenue_by_type': {
            'exchange': 1200.00,
            'income': 200.00,
            'expense': 100.00
        },
        'transaction_breakdown': {
            'exchange': 35,
            'income': 5,
            'expense': 5
        }
    }


def generate_sample_monthly_revenue() -> Dict[str, Any]:
    """Generate sample monthly revenue report"""
    return {
        'title': 'Monthly Revenue Report',
        'year': 2025,
        'month': 1,
        'branch_id': 'BR-001',
        'total_revenue': 45000.00,
        'total_transactions': 1350,
        'average_daily_revenue': 1500.00,
        'daily_breakdown': {
            day: {
                'revenue': 1000.00 + (day * 50),
                'count': 40 + day
            }
            for day in range(1, 32)
        }
    }


def generate_sample_branch_comparison() -> Dict[str, Any]:
    """Generate sample branch comparison report"""
    branches = [
        {'branch_code': 'BR-001', 'branch_name': 'Main Branch', 'revenue': 45000.00, 'transactions': 1350},
        {'branch_code': 'BR-002', 'branch_name': 'Downtown', 'revenue': 38000.00, 'transactions': 1140},
        {'branch_code': 'BR-003', 'branch_name': 'Airport', 'revenue': 52000.00, 'transactions': 1560},
    ]
    
    return {
        'title': 'Branch Performance Comparison',
        'date_range': {
            'start': '2025-01-01',
            'end': '2025-01-31'
        },
        'total_system_revenue': sum(b['revenue'] for b in branches),
        'branch_count': len(branches),
        'branches': branches
    }


# ==================== MANUAL TEST SCRIPT ====================

def run_manual_tests():
    """
    Manual test script to generate sample reports
    Run this to create actual files for visual inspection
    """
    print("🧪 Running Manual Report Export Tests\n")
    
    export_service = ReportExportService()
    
    # Test 1: Daily Summary
    print("1️⃣ Generating Daily Summary Report...")
    daily_data = generate_sample_daily_summary()
    
    json_file = export_service.export_to_json(daily_data)
    with open('/tmp/daily_summary.json', 'w') as f:
        f.write(json_file)
    print("   ✅ JSON: /tmp/daily_summary.json")
    
    excel_file = export_service.export_to_excel(daily_data, template='standard')
    with open('/tmp/daily_summary.xlsx', 'wb') as f:
        f.write(excel_file.getvalue())
    print("   ✅ Excel: /tmp/daily_summary.xlsx")
    
    pdf_file = export_service.export_to_pdf(daily_data)
    with open('/tmp/daily_summary.pdf', 'wb') as f:
        f.write(pdf_file.getvalue())
    print("   ✅ PDF: /tmp/daily_summary.pdf\n")
    
    # Test 2: Monthly Revenue
    print("2️⃣ Generating Monthly Revenue Report...")
    monthly_data = generate_sample_monthly_revenue()
    
    excel_file = export_service.export_to_excel(monthly_data, template='financial')
    with open('/tmp/monthly_revenue.xlsx', 'wb') as f:
        f.write(excel_file.getvalue())
    print("   ✅ Excel: /tmp/monthly_revenue.xlsx")
    
    pdf_file = export_service.export_to_pdf(monthly_data)
    with open('/tmp/monthly_revenue.pdf', 'wb') as f:
        f.write(pdf_file.getvalue())
    print("   ✅ PDF: /tmp/monthly_revenue.pdf\n")
    
    # Test 3: Branch Comparison
    print("3️⃣ Generating Branch Comparison Report...")
    comparison_data = generate_sample_branch_comparison()
    
    excel_file = export_service.export_to_excel(comparison_data, template='summary')
    with open('/tmp/branch_comparison.xlsx', 'wb') as f:
        f.write(excel_file.getvalue())
    print("   ✅ Excel: /tmp/branch_comparison.xlsx\n")
    
    print("✅ All manual tests completed!")
    print("📂 Check /tmp/ directory for generated files")


if __name__ == '__main__':
    # Run manual tests
    run_manual_tests()
    
    # Run pytest if available
    print("\n🧪 Running Automated Tests...")
    pytest.main([__file__, '-v'])
