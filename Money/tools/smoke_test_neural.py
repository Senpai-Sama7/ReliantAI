# 🚀 HVAC NEURAL NODE: SMOKE TEST PROTOCOL (v1.4.0)
# Use this to verify Gemini connectivity and Neural Engine 'Warm-up' behavior.

import os
import json
import time
import sys
from pathlib import Path

# Ensure parent directory is in path so we can import core modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --- STUB TWILIO TO PREVENT COSTS ---
os.environ["STUB_TWILIO"] = "true"
os.environ["SKIP_TWILIO_VALIDATION"] = "true"

from hvac_dispatch_crew import warmup_node, run_hvac_crew
from database import init_db

def run_smoke_test():
    print("🛰️ [TEST CONFIG] STUB_TWILIO: ACTIVE (Zero Credit Burn)")
    init_db()
    
    # 1. TEST PRE-INITIALIZATION (WARM-UP)
    print("\n📦 STEP 1/2: Testing Neural Warm-up...")
    start_warm = time.time()
    warmup_node()
    elapsed_warm = time.time() - start_warm
    print(f"✅ Cold-start penalty mitigated in {elapsed_warm:.2f}s.")

    # 2. TEST LIVE CREW RUN (Requires real Gemini key)
    print("\n🧠 STEP 2/2: Testing Neural Inference with Real Scenario...")
    payload = "I smell gas in my laundry room. It's 102 degrees out."
    
    start_inf = time.time()
    try:
        result = run_hvac_crew(customer_message=payload, outdoor_temp_f=102.0)
        elapsed_inf = time.time() - start_inf
        
        print("\n🏆 NEURAL ENGINE OUTPUT OVERVIEW:")
        print(f"   Status: {result.get('status')}")
        print(f"   Inference Time: {elapsed_inf:.2f}s")
        # print("   Raw result:", str(result)[:500])
        print("\n✅ LIVE NEURAL SMOKE TEST PASSED.")
    except Exception as e:
        print(f"\n❌ LIVE NEURAL SMOKE TEST FAILED.")
        print(f"   Error: {e}")
        if "API key" in str(e):
            print("   ❗ REASON: No valid GEMINI_API_KEY detected in .env.")

if __name__ == "__main__":
    run_smoke_test()
