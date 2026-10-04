"""
Decision Playground Entrypoint
"""
from app import app

def main():
    print("=" * 60)
    print("Starting Decision Playground...")
    print("Serving on: http://127.0.0.1:8050")
    print("=" * 60)
    app.run(host="127.0.0.1", port=8050, debug=True)

if __name__ == "__main__":
    main()
