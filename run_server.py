#!/usr/bin/env python3
"""
Direct Flask app runner without batch file complications
"""
import sys
import os

# Add the workspace root to Python path
workspace_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, workspace_root)

print(f"[DIR] Working directory: {os.getcwd()}")
print(f"[DIR] Workspace root: {workspace_root}")

# Import the app
try:
    from Scripts.app import app
    print("[OK] Flask app imported successfully")
except Exception as e:
    print(f"[ERROR] Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    print("[START] Starting College Chatbot Server...")
    try:
        # Run Flask with minimal settings
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n[BYE] Server stopped by user")
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




