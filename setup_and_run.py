"""
Setup verification and execution script
"""
import os
import sys

def check_api_key():
    """Check if API key is configured"""
    try:
        from baseline import API_KEY
        if API_KEY == "YOUR API KEY":
            print("=" * 60)
            print("ERROR: API Key Not Configured!")
            print("=" * 60)
            print("\nPlease follow these steps:")
            print("1. Open baseline.py in your editor")
            print("2. Find line 17: API_KEY = \"YOUR API KEY\"")
            print("3. Replace 'YOUR API KEY' with your actual Saltlux API key")
            print("4. Save the file")
            print("5. Run this script again")
            print("\nExample:")
            print('   API_KEY = "sk-1234567890abcdef..."')
            print("=" * 60)
            return False
        else:
            print(f"[OK] API Key configured: {API_KEY[:10]}...{API_KEY[-4:]}")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to check API key: {e}")
        return False

def check_files():
    """Check if required files exist"""
    print("\n[CHECK] Verifying required files...")

    required_files = [
        ("test.csv", "Test data CSV file"),
        ("test/", "Test images directory")
    ]

    all_ok = True
    for file_path, description in required_files:
        if os.path.exists(file_path):
            if file_path.endswith('/'):
                count = len([f for f in os.listdir(file_path) if f.endswith('.png')])
                print(f"[OK] {description}: {count} images found")
            else:
                print(f"[OK] {description}")
        else:
            print(f"[ERROR] Missing: {description} ({file_path})")
            all_ok = False

    return all_ok

def run_classification():
    """Run the classification"""
    print("\n" + "=" * 60)
    print("Starting Automated Classification")
    print("=" * 60)

    try:
        from baseline import main
        main()
        return True
    except Exception as e:
        print(f"\n[ERROR] Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("AI Agent Semiconductor Classification System")
    print("Setup Verification & Execution")
    print("=" * 60)

    # Check API key
    if not check_api_key():
        sys.exit(1)

    # Check files
    if not check_files():
        print("\n[ERROR] Missing required files!")
        sys.exit(1)

    # Ask user confirmation
    print("\n" + "=" * 60)
    response = input("Ready to classify 100 test images? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("Classification cancelled.")
        sys.exit(0)

    # Run classification
    if run_classification():
        print("\n" + "=" * 60)
        print("[SUCCESS] Classification completed!")
        print("Check output/output.csv for results")
        print("=" * 60)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
