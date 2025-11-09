#!/usr/bin/env python3
"""
CEMS Reporting System - Quick Test Script
==========================================
Fast verification of reporting functionality
"""

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def test_imports():
    """Test 1: Import all modules"""
    print_header("TEST 1: Module Imports")
    
    try:
        from report_service import ReportService
        print_success("Imported ReportService")
        
        from report_export_service import ReportExportService
        print_success("Imported ReportExportService")
        
        import openpyxl
        print_success("Imported openpyxl (Excel support)")
        
        import reportlab
        print_success("Imported reportlab (PDF support)")
        
        from jinja2 import Template
        print_success("Imported Jinja2 (Template engine)")
        
        return True
        
    except ImportError as e:
        print_error(f"Import failed: {str(e)}")
        print_info("Run: pip install -r requirements-reports.txt")
        return False


def test_json_export():
    """Test 2: JSON Export"""
    print_header("TEST 2: JSON Export")
    
    try:
        from report_export_service import ReportExportService
        
        export_service = ReportExportService()
        
        # Sample data
        sample_data = {
            'title': 'Test Report',
            'date': date.today().isoformat(),
            'summary': {
                'total_revenue': 5000.00,
                'total_transactions': 150
            },
            'data': [
                {'date': '2025-01-15', 'count': 25, 'amount': 850.00},
                {'date': '2025-01-16', 'count': 30, 'amount': 1020.00}
            ]
        }
        
        # Export to JSON
        json_output = export_service.export_to_json(sample_data, pretty=True)
        
        # Verify
        assert json_output is not None
        assert 'Test Report' in json_output
        assert 'total_revenue' in json_output
        
        # Save to file
        output_file = '/tmp/cems_test_report.json'
        with open(output_file, 'w') as f:
            f.write(json_output)
        
        print_success(f"JSON export successful: {output_file}")
        print_info(f"File size: {len(json_output)} bytes")
        
        return True
        
    except Exception as e:
        print_error(f"JSON export failed: {str(e)}")
        return False


def test_excel_export():
    """Test 3: Excel Export"""
    print_header("TEST 3: Excel Export")
    
    try:
        from report_export_service import ReportExportService
        
        export_service = ReportExportService()
        
        # Sample data with more structure
        sample_data = {
            'title': 'Monthly Financial Report',
            'date_range': {
                'start': '2025-01-01',
                'end': '2025-01-31'
            },
            'summary': {
                'total_revenue': 15000.00,
                'total_transactions': 450,
                'average_daily_revenue': 500.00
            },
            'data': [
                {'date': f'2025-01-{i:02d}', 'transactions': 10+i, 'revenue': 300.00+i*10}
                for i in range(1, 11)
            ]
        }
        
        # Export to Excel with different templates
        templates = ['standard', 'financial', 'summary']
        
        for template in templates:
            excel_file = export_service.export_to_excel(sample_data, template=template)
            
            # Verify
            assert excel_file is not None
            content = excel_file.read()
            assert len(content) > 1000
            
            # Save to file
            output_file = f'/tmp/cems_test_{template}.xlsx'
            with open(output_file, 'wb') as f:
                f.write(content)
            
            print_success(f"Excel export ({template}): {output_file}")
            print_info(f"File size: {len(content)} bytes")
        
        return True
        
    except Exception as e:
        print_error(f"Excel export failed: {str(e)}")
        return False


def test_pdf_export():
    """Test 4: PDF Export"""
    print_header("TEST 4: PDF Export")
    
    try:
        from report_export_service import ReportExportService
        
        export_service = ReportExportService()
        
        # Sample data
        sample_data = {
            'title': 'Branch Performance Report',
            'date_range': {
                'start': '2025-01-01',
                'end': '2025-01-31'
            },
            'summary': {
                'total_branches': 5,
                'total_revenue': 45000.00,
                'top_branch': 'Airport Branch'
            },
            'branches': [
                {'code': 'BR-001', 'name': 'Main Branch', 'revenue': 15000.00},
                {'code': 'BR-002', 'name': 'Downtown', 'revenue': 12000.00},
                {'code': 'BR-003', 'name': 'Airport', 'revenue': 18000.00}
            ]
        }
        
        # Export to PDF
        pdf_file = export_service.export_to_pdf(sample_data)
        
        # Verify
        assert pdf_file is not None
        content = pdf_file.read()
        assert content.startswith(b'%PDF')  # PDF signature
        assert len(content) > 1000
        
        # Save to file
        output_file = '/tmp/cems_test_report.pdf'
        with open(output_file, 'wb') as f:
            f.write(content)
        
        print_success(f"PDF export successful: {output_file}")
        print_info(f"File size: {len(content)} bytes")
        
        return True
        
    except Exception as e:
        print_error(f"PDF export failed: {str(e)}")
        return False


def test_html_template():
    """Test 5: HTML Template Export"""
    print_header("TEST 5: HTML Template Export")
    
    try:
        from report_export_service import ReportExportService, STANDARD_HTML_TEMPLATE
        
        export_service = ReportExportService()
        
        # Sample data
        sample_data = {
            'title': 'Daily Summary Report',
            'summary': {
                'total_transactions': 150,
                'total_revenue': 5000.00,
                'average_commission': 33.33
            },
            'data': [
                {'currency': 'USD', 'count': 100, 'volume': 100000.00},
                {'currency': 'EUR', 'count': 30, 'volume': 30000.00},
                {'currency': 'GBP', 'count': 20, 'volume': 20000.00}
            ]
        }
        
        # Render HTML
        html_output = export_service.export_with_html_template(
            sample_data,
            STANDARD_HTML_TEMPLATE
        )
        
        # Verify
        assert html_output is not None
        assert '<html>' in html_output
        assert 'Daily Summary Report' in html_output
        assert 'table' in html_output.lower()
        
        # Save to file
        output_file = '/tmp/cems_test_report.html'
        with open(output_file, 'w') as f:
            f.write(html_output)
        
        print_success(f"HTML export successful: {output_file}")
        print_info(f"File size: {len(html_output)} bytes")
        
        return True
        
    except Exception as e:
        print_error(f"HTML export failed: {str(e)}")
        return False


def test_performance():
    """Test 6: Performance with Large Dataset"""
    print_header("TEST 6: Performance Test")
    
    try:
        import time
        from report_export_service import ReportExportService
        
        export_service = ReportExportService()
        
        # Generate large dataset
        large_data = {
            'title': 'Large Dataset Performance Test',
            'data': [
                {
                    'id': i,
                    'date': f'2025-01-{(i%28)+1:02d}',
                    'amount': i * 100.00,
                    'description': f'Transaction {i}'
                }
                for i in range(1, 5001)  # 5000 records
            ]
        }
        
        print_info(f"Testing with {len(large_data['data'])} records...")
        
        # Test JSON
        start = time.time()
        json_output = export_service.export_to_json(large_data, pretty=False)
        json_time = time.time() - start
        print_success(f"JSON: {json_time:.3f}s ({len(json_output)} bytes)")
        
        # Test Excel (limited rows)
        limited_data = large_data.copy()
        limited_data['data'] = large_data['data'][:1000]  # Limit for Excel
        
        start = time.time()
        excel_output = export_service.export_to_excel(limited_data)
        excel_time = time.time() - start
        print_success(f"Excel: {excel_time:.3f}s (1000 records)")
        
        # Test PDF (limited rows)
        start = time.time()
        pdf_output = export_service.export_to_pdf(limited_data)
        pdf_time = time.time() - start
        print_success(f"PDF: {pdf_time:.3f}s (1000 records)")
        
        print_info("Performance test completed")
        
        return True
        
    except Exception as e:
        print_error(f"Performance test failed: {str(e)}")
        return False


def test_filename_generation():
    """Test 7: Filename Generation"""
    print_header("TEST 7: Filename Generation")
    
    try:
        from report_export_service import get_export_filename
        
        # Test with timestamp
        filename1 = get_export_filename('daily_summary', 'pdf', timestamp=True)
        assert filename1.startswith('CEMS_daily_summary_')
        assert filename1.endswith('.pdf')
        print_success(f"With timestamp: {filename1}")
        
        # Test without timestamp
        filename2 = get_export_filename('monthly_report', 'xlsx', timestamp=False)
        assert filename2 == 'CEMS_monthly_report.xlsx'
        print_success(f"Without timestamp: {filename2}")
        
        return True
        
    except Exception as e:
        print_error(f"Filename generation failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'CEMS REPORTING SYSTEM - QUICK TEST':^60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    
    # Track results
    results = []
    
    # Run tests
    tests = [
        ("Module Imports", test_imports),
        ("JSON Export", test_json_export),
        ("Excel Export", test_excel_export),
        ("PDF Export", test_pdf_export),
        ("HTML Template", test_html_template),
        ("Performance", test_performance),
        ("Filename Generation", test_filename_generation)
    ]
    
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}")
        print_info("Generated test files in /tmp/:")
        print("  - cems_test_report.json")
        print("  - cems_test_standard.xlsx")
        print("  - cems_test_financial.xlsx")
        print("  - cems_test_summary.xlsx")
        print("  - cems_test_report.pdf")
        print("  - cems_test_report.html")
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  SOME TESTS FAILED{Colors.ENDC}")
        print_info("Check error messages above for details")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
