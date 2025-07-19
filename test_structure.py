"""
Test script to verify the application structure.
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test if all modules can be imported correctly."""
    try:
        print("Testing imports...")
        
        # Test core modules
        from app.core.app import create_app
        print("✓ Core app module imported successfully")
        
        from app.core.database import get_supabase_client
        print("✓ Database module imported successfully")
        
        # Test API routes
        from app.api.routes import router
        print("✓ API routes imported successfully")
        
        # Test models
        from app.models.state_schema import SOPState
        print("✓ State schema imported successfully")
        
        # Test services
        from app.services.file_services.file_readers import read_file_by_extension
        print("✓ File readers imported successfully")
        
        from app.workflow import create_workflow
        print("✓ Workflow imported successfully")
        
        print("\n✅ All imports successful! The application structure is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_app_creation():
    """Test if the FastAPI app can be created."""
    try:
        print("\nTesting app creation...")
        from app.core.app import create_app
        app = create_app()
        print("✅ FastAPI app created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating app: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("ONVOKE AI APPLICATION STRUCTURE TEST")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_app_creation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! Your application is ready to run.")
        print("\nTo start the application, run:")
        print("  python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 50)
