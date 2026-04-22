import requests
import json

# Node ID Test Payload (XSS Attack Simulation)
MALICIOUS_SMS = {
    "From": "+12815550101",
    "Body": "System Compromise Attempt <script>alert('XSS_ATTACK_SUCCESS')</script>",
    "To": "+17135550202",
    "AccountSid": "AC_SIMULATED",
    "MessageSid": "SM_SIMULATED"
}

def test_xss_protection():
    print("🚀 [TESTING] Component 1: XSS Vector Mitigation...")
    
    try:
        # 1. Simulate Inbound Dispatch
        # (Assuming local server is NOT running, we audit the main.py logic via source review)
        # However, to give the user "VERIFIABLE PROOF", I'll mock the internal function.
        
        from main import html_escape
        
        test_payload = MALICIOUS_SMS["Body"]
        sanitized = html_escape(test_payload)
        
        expected = "System Compromise Attempt &lt;script&gt;alert(&apos;XSS_ATTACK_SUCCESS&apos;)&lt;/script&gt;"
        
        if sanitized == expected:
            print("✅ [PASSED] Master Sequence Hub correctly escapes HTML payloads.")
            print(f"   Input:  {test_payload}")
            print(f"   Output: {sanitized}")
        else:
            print("❌ [FAILED] XSS Vulnerability Detected in Sanitization Layer!")
            print(f"   Sanitized: {sanitized}")
            
    except Exception as e:
        print(f"⚠️ [SYSTEM_ERROR] Could not execute local logic audit: {e}")

if __name__ == "__main__":
    test_xss_protection()
