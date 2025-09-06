
import requests
import os
import json
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv() 

FMCSA_API_KEY = os.getenv("FMCSA_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)

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

    logger.info(f"FMCSA API URL: {url}")
    
    try:

        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        logger.debug(f"FMCSA API Response: {json.dumps(data, indent=2)}")
        
        # Check if carrier exists and is allowed to operate
        if "content" in data and len(data["content"]) > 0:
            carrier_info = data["content"][0]["carrier"]
            logger.debug(f"Carrier info: {carrier_info}")
            allowed_to_operate = carrier_info.get("allowedToOperate", "N")
            carrier_name = carrier_info.get("legalName", "Unknown")
            
            logger.info(f"MC {clean_mc} - allowedToOperate: {allowed_to_operate}, carrier_name: {carrier_name}")
            
            if allowed_to_operate == "Y":
                logger.info(f"✅ MC {clean_mc} VERIFIED - {carrier_name}")
                return True, carrier_name
            else:
                logger.warning(f"❌ MC {clean_mc} NOT VERIFIED - {carrier_name}")
                return False, carrier_name
        else:
            logger.warning(f"❌ MC {clean_mc} not found in FMCSA database")
            return False, "Unknown"
            
    except Exception as e:
        logger.error(f"❌ FMCSA API error for MC {clean_mc}: {e}")
        return False, "Unknown"

