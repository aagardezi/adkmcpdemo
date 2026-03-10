import sys
import os

try:
    import google.adk
    print(os.path.dirname(google.adk.__file__))
except ImportError:
    print("google.adk not found", file=sys.stderr)
    sys.exit(1)
