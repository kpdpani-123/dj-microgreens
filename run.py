import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn

if __name__ == "__main__":
    print("==================================================================")
    print("Starting DJ Microgreens - Chennai E-commerce & Farm ERP Server")
    print("Farm Location: Guindy Industrial Micro-Farm, Chennai, TN")
    print("Storefront: http://127.0.0.1:8000")
    print("Admin Operations: http://127.0.0.1:8000/admin")
    print("Restaurant B2B Portal: http://127.0.0.1:8000/b2b")
    print("OpenAPI Swagger Docs: http://127.0.0.1:8000/docs")
    print("==================================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
