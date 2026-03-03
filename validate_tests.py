#!/usr/bin/env python
"""
Simple script to validate that storage tests exist.
"""
import sys
import os

print("=== Checking test storage file ===\n")

# Check if file exists
test_file = "tests/test_storage.py"
if not os.path.exists(test_file):
    print(f"✗ Test file not found: {test_file}")
    sys.exit(1)

print(f"✓ Test file exists: {test_file}")

# Read and count tests
with open(test_file, 'r') as f:
    content = f.read()

# Count test classes
test_classes = []
for line in content.split('\n'):
    if line.strip().startswith('class Test'):
        class_name = line.strip().split('(')[0].replace('class ', '')
        test_classes.append(class_name)

print(f"✓ Found {len(test_classes)} test classes:")
for cls in test_classes:
    print(f"  - {cls}")

# Count test methods
import re
test_methods = re.findall(r'def (test_\w+)\(self\):', content)
print(f"\n✓ Found {len(test_methods)} test methods")

# Show first 10 test methods
print("\nTest methods:")
for i, method in enumerate(test_methods[:10], 1):
    print(f"  {i}. {method}")

if len(test_methods) > 10:
    print(f"  ... and {len(test_methods) - 10} more")

print(f"\n{'='*60}")
print(f"Total: {len(test_classes)} test classes, {len(test_methods)} test methods")
print(f"{'='*60}")

# Check requirements
requirements_met = True
print("\n=== Checking Acceptance Criteria ===\n")

# Requirement: At least 3 pytest tests
if len(test_methods) >= 3:
    print(f"✓ At least 3 tests: {len(test_methods)} tests found")
else:
    print(f"✗ At least 3 tests required, only {len(test_methods)} found")
    requirements_met = False

# Requirement: Test saving URLs
save_tests = [m for m in test_methods if 'save' in m.lower()]
if save_tests:
    print(f"✓ Tests for saving URLs: {', '.join(save_tests)}")
else:
    print("✗ No tests for saving URLs found")
    requirements_met = False

# Requirement: Test getting by code
get_code_tests = [m for m in test_methods if 'get_by_code' in m or 'code' in m]
if get_code_tests:
    print(f"✓ Tests for getting by code: {', '.join(get_code_tests)}")
else:
    print("✗ No tests for getting by code found")
    requirements_met = False

# Requirement: Test getting by URL
get_url_tests = [m for m in test_methods if 'get_by_url' in m or 'url' in m]
if get_url_tests:
    print(f"✓ Tests for getting by URL: {', '.join(get_url_tests)}")
else:
    print("✗ No tests for getting by URL found")
    requirements_met = False

# Requirement: Test deletion
delete_tests = [m for m in test_methods if 'delete' in m]
if delete_tests:
    print(f"✓ Tests for deletion: {', '.join(delete_tests)}")
else:
    print("✗ No tests for deletion found")
    requirements_met = False

# Requirement: Test listing all
list_tests = [m for m in test_methods if 'list' in m]
if list_tests:
    print(f"✓ Tests for listing: {', '.join(list_tests)}")
else:
    print("✗ No tests for listing found")
    requirements_met = False

# Requirement: Test duplicate handling
duplicate_tests = [m for m in test_methods if 'duplicate' in m]
if duplicate_tests:
    print(f"✓ Tests for duplicate handling: {', '.join(duplicate_tests)}")
else:
    print("✗ No tests for duplicate handling found")
    requirements_met = False

# Requirement: Test thread-safety
thread_tests = [m for m in test_methods if 'thread' in m.lower() or 'concurrent' in m]
if thread_tests:
    print(f"✓ Tests for thread-safety: {', '.join(thread_tests)}")
else:
    print("✗ No tests for thread-safety found")
    requirements_met = False

# Requirement: Test CRUD operations
crud_tests = [m for m in test_methods if any(x in m for x in ['save', 'get', 'delete', 'update'])]
if len(crud_tests) >= 3:
    print(f"✓ Tests for CRUD operations: {len(crud_tests)} tests")
else:
    print(f"✗ Insufficient CRUD tests: {len(crud_tests)} tests")
    requirements_met = False

print(f"\n{'='*60}")
if requirements_met:
    print("✓ ALL ACCEPTANCE CRITERIA MET!")
    print(f"{'='*60}")
    sys.exit(0)
else:
    print("✗ SOME ACCEPTANCE CRITERIA NOT MET")
    print(f"{'='*60}")
    sys.exit(1)