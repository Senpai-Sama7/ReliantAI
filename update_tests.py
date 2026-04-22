import re

files_to_update = [
    'B-A-P/tests/test_api.py',
    'B-A-P/tests/test_event_bus_integration.py'
]

for filepath in files_to_update:
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace async_client with authenticated_client globally
    content = content.replace('async_client', 'authenticated_client')
    
    # Revert the unauthenticated endpoints
    unauth_tests = [
        'test_health_endpoint',
        'test_root_endpoint',
        'test_metrics_endpoint',
        'test_openapi_docs'
    ]
    for test in unauth_tests:
        content = re.sub(f'def {test}\\(authenticated_client: AsyncClient\\)', f'def {test}(async_client: AsyncClient)', content)
    
    with open(filepath, 'w') as f:
        f.write(content)

print("Updated tests successfully.")
