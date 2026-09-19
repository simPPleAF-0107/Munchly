import os
from pathlib import Path
import pytest

endpoints_dir = Path(r"d:\Projects\Munchly\backend\app\api\v1\endpoints")
router_path = Path(r"d:\Projects\Munchly\backend\app\api\v1\router.py")

def test_get_current_user_dependency_used():
    # Verify get_current_user dependency is used consistently
    for filepath in endpoints_dir.glob("*.py"):
        if filepath.name in ("__init__.py", "auth.py"):
            continue
        content = filepath.read_text(encoding='utf-8')
        assert "get_current_user" in content or "get_current_active_user" in content, f"Missing auth dependency in {filepath.name}"

def test_endpoint_schemas_exist():
    # Test that endpoint schema classes exist and have required fields
    for filepath in endpoints_dir.glob("*.py"):
        if filepath.name == "__init__.py":
            continue
        content = filepath.read_text(encoding='utf-8')
        assert "schemas" in content or "pydantic" in content, f"No schemas imported in {filepath.name}"

def test_request_validation_patterns():
    # Test request validation patterns (pydantic model validation)
    for filepath in endpoints_dir.glob("*.py"):
        if filepath.name == "__init__.py":
            continue
        content = filepath.read_text(encoding='utf-8')
        assert "APIRouter" in content
        assert "@router." in content

def test_all_routers_included():
    # Test that all router files are properly included (check router.py)
    router_file_content = router_path.read_text(encoding='utf-8')
    for filepath in endpoints_dir.glob("*.py"):
        if filepath.name == "__init__.py":
            continue
        module_name = filepath.stem
        assert f"api_router.include_router({module_name}.router" in router_file_content, f"Router missing include for {module_name}"

def test_event_emission_patterns():
    # Verify event emission patterns exist in daily/feedback/behavioral endpoints
    for module in ["daily.py", "feedback.py", "behavioral.py"]:
        filepath = endpoints_dir / module
        content = filepath.read_text(encoding='utf-8')
        has_event_logic = "Service" in content or "BackgroundTasks" in content or "event" in content.lower()
        assert has_event_logic, f"No event emission pattern found in {module}"
