
import requests
import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv() 

FMCSA_API_KEY = os.getenv("FMCSA_API_KEY")
print(FMCSA_API_KEY)

def verify_mc_number(mc_number: str) -> tuple[bool, str]:
    """
    Check if carrier with MC number is eligible to work with using FMCSA API.
    Returns (is_verified, carrier_name) tuple.
    """
    # Clean the MC number (remove MC prefix if present)
    clean_mc = mc_number.replace("MC", "").replace("mc", "").strip()
    
    # Use real FMCSA API for verification
    return verify_with_fmcsa_api(clean_mc)

def verify_with_fmcsa_api(clean_mc: str) -> tuple[bool, str]:
    """
    Verify MC number using the official FMCSA API.
    Returns (is_verified, carrier_name) tuple.
    """
    # FMCSA API endpoint
    url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{clean_mc}?format=json"
    
    # Add webKey 
    if FMCSA_API_KEY:
        url += f"&webKey={FMCSA_API_KEY}"

    print("url",url)
    
    try:

        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        print(f"FMCSA API Response: {json.dumps(data, indent=2)}")
        
        # Check if carrier exists and is allowed to operate
        if "content" in data and len(data["content"]) > 0:
            carrier_info = data["content"][0]["carrier"]
            print("carrier info", carrier_info)
            allowed_to_operate = carrier_info.get("allowedToOperate", "N")
            carrier_name = carrier_info.get("legalName", "Unknown")
            
            print(f"allowedToOperate: {allowed_to_operate}")
            print(f"carrier_name: {carrier_name}")
            
            if allowed_to_operate == "Y":
                print("✅ VERIFIED - returning True")
                return True, carrier_name
            else:
                print("❌ NOT VERIFIED - returning False")
                print(f"   Carrier: {carrier_name}")
                return False, carrier_name
        else:

            return False, "Unknown"
            
    except Exception as e:

        return False, "Unknown"

