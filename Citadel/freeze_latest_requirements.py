

import os
import subprocess
from typing import Dict, List

# Define the desired versions for common packages
# This acts as a single source of truth for these dependencies.
COMMON_PACKAGES: Dict[str, str] = {
    "fastapi": "0.116.1",
    "uvicorn": "0.35.0",
    "pydantic": "2.11.7",
    "numpy": "2.3.2",
    "scikit-learn": "1.7.1",
    "pandas": "2.3.1",
    "httpx": "0.28.1",
}

# Define service-specific exceptions to the common packages
SERVICE_SPECIFIC_PACKAGES: Dict[str, Dict[str, str]] = {
    "causal_inference": {
        "scikit-learn": "1.6.0"
    }
}

def get_all_requirements_in_files() -> List[str]:
    """Finds all requirements.in files in the project."""
    requirements_files = []
    for root, _, files in os.walk('.'):
        if 'local_agent' in root:  # Exclude local_agent for now
            continue
        for file in files:
            if file == 'requirements.in':
                requirements_files.append(os.path.join(root, file))
    return requirements_files

def update_and_freeze_requirements(requirements_file: str):
    """
    Updates the common packages in a requirements.in file and then freezes it.
    """
    print(f"Processing {requirements_file}...")
    
    service_name = os.path.basename(os.path.dirname(requirements_file))

    with open(requirements_file, 'r') as f:
        lines = f.readlines()

    new_lines = []
    updated = False
    for line in lines:
        pkg = line.strip().split('==')[0]
        
        # Check for service-specific version
        if service_name in SERVICE_SPECIFIC_PACKAGES and pkg in SERVICE_SPECIFIC_PACKAGES[service_name]:
            new_version = f"{pkg}=={SERVICE_SPECIFIC_PACKAGES[service_name][pkg]}\n"
            if line.strip() != new_version.strip():
                print(f"  - Updating {pkg} to {SERVICE_SPECIFIC_PACKAGES[service_name][pkg]} (service specific)")
                new_lines.append(new_version)
                updated = True
            else:
                new_lines.append(line)
        elif pkg in COMMON_PACKAGES:
            new_version = f"{pkg}=={COMMON_PACKAGES[pkg]}\n"
            if line.strip() != new_version.strip():
                print(f"  - Updating {pkg} to {COMMON_PACKAGES[pkg]}")
                new_lines.append(new_version)
                updated = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if updated:
        with open(requirements_file, 'w') as f:
            f.writelines(new_lines)

    print(f"Freezing dependencies for {requirements_file}...")
    try:
        subprocess.run(
            ['pip-compile', '--upgrade', requirements_file],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Successfully froze dependencies for {requirements_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error freezing dependencies for {requirements_file}:")
        print(e.stdout)
        print(e.stderr)

if __name__ == '__main__':
    all_requirements_in = get_all_requirements_in_files()
    if not all_requirements_in:
        print("No requirements.in files found to process.")
    else:
        for req_file in all_requirements_in:
            update_and_freeze_requirements(req_file)

    print("\nDependency update process complete.")
    print("It is recommended to review the changes before committing.")
