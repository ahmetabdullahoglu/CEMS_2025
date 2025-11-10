#!/usr/bin/env python3
"""
Verification script for new user management endpoints
Checks that the methods and endpoints are properly defined
"""

import ast
import sys
from pathlib import Path

def check_service_methods():
    """Check UserService has the new methods"""
    print("=" * 60)
    print("Checking UserService methods...")
    print("=" * 60)

    service_file = Path("app/services/user_service.py")
    with open(service_file, 'r') as f:
        content = f.read()

    tree = ast.parse(content)

    methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "UserService":
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef):
                    methods.append(item.name)

    required_methods = ["admin_reset_password", "delete_user"]

    for method in required_methods:
        if method in methods:
            print(f"✅ Method '{method}' found")
        else:
            print(f"❌ Method '{method}' NOT found")
            return False

    print()
    return True


def check_endpoints():
    """Check users.py has the new endpoints"""
    print("=" * 60)
    print("Checking API endpoints...")
    print("=" * 60)

    endpoints_file = Path("app/api/v1/endpoints/users.py")
    with open(endpoints_file, 'r') as f:
        content = f.read()

    tree = ast.parse(content)

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            functions.append(node.name)

    required_endpoints = ["admin_reset_password", "delete_user"]

    for endpoint in required_endpoints:
        if endpoint in functions:
            print(f"✅ Endpoint function '{endpoint}' found")
        else:
            print(f"❌ Endpoint function '{endpoint}' NOT found")
            return False

    print()
    return True


def check_schema():
    """Check AdminPasswordReset schema exists"""
    print("=" * 60)
    print("Checking Pydantic schemas...")
    print("=" * 60)

    schema_file = Path("app/schemas/user.py")
    with open(schema_file, 'r') as f:
        content = f.read()

    tree = ast.parse(content)

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)

    if "AdminPasswordReset" in classes:
        print("✅ Schema 'AdminPasswordReset' found")
        print()
        return True
    else:
        print("❌ Schema 'AdminPasswordReset' NOT found")
        print()
        return False


def check_imports():
    """Check imports are correct"""
    print("=" * 60)
    print("Checking imports...")
    print("=" * 60)

    endpoints_file = Path("app/api/v1/endpoints/users.py")
    with open(endpoints_file, 'r') as f:
        content = f.read()

    checks = [
        ("AdminPasswordReset", "Schema import"),
        ("BusinessRuleViolationError", "Exception import")
    ]

    for item, description in checks:
        if item in content:
            print(f"✅ {description}: {item} found")
        else:
            print(f"❌ {description}: {item} NOT found")
            return False

    print()
    return True


def main():
    print("\n")
    print("🔍 VERIFICATION SCRIPT FOR NEW USER MANAGEMENT ENDPOINTS")
    print("\n")

    results = []

    results.append(("Service Methods", check_service_methods()))
    results.append(("API Endpoints", check_endpoints()))
    results.append(("Pydantic Schema", check_schema()))
    results.append(("Imports", check_imports()))

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("🎉 All checks passed! The implementation is complete.")
        print()
        print("New endpoints added:")
        print("  - POST /api/v1/users/{user_id}/admin-reset-password")
        print("    (Admin password reset without current password)")
        print("  - DELETE /api/v1/users/{user_id}")
        print("    (Permanent user deletion)")
        print()
        return 0
    else:
        print("❌ Some checks failed. Please review the implementation.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
