from fastapi import APIRouter, Request, Header, HTTPException
from app.database import get_db_context
from app.models.load import Load, CallLog
from dotenv import load_dotenv
from app.services.fmcsa_verification import verify_mc_number
import json
import os
import logging
from datetime import datetime

load_dotenv() 

WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY")
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

@router.post("/webhook/happyrobot/verify_mc")
async def verify_mc_endpoint(request: Request, x_api_key: str = Header(None)):
    """Dedicated endpoint for MC verification"""
    
    if x_api_key != WEBHOOK_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    payload = await request.json()
    logger.info(f"MC Verification request: {json.dumps(payload, indent=2)}")
    
    mc_number = payload.get("mc_number", "")
    
    if not mc_number:
        return {
            "verified": False,
            "message": "MC number is required",
            "say": "I need your MC number to verify your eligibility. What's your MC number?"
        }
    
    # Verify MC number
    is_verified, carrier_name = verify_mc_number(mc_number)
    
    logger.info(f"MC {mc_number} verification result: {is_verified}, Carrier: {carrier_name}")
    
    if is_verified:
        return {
            "verified": True,
            "message": "MC number verified successfully",
            "carrier_name": carrier_name,
            "say": f"Excellent! Your MC number {mc_number} has been verified. Welcome, {carrier_name}! You're eligible to work with us. Let me search for available loads that match your equipment.",

        }
    else:
        return {
            "verified": False,
            "message": "MC number verification failed",
            "say": "I'm sorry, but your MC number is not eligible to work with us at this time. Please contact our compliance department for more information.",

        }

@router.post("/webhook/happyrobot/load_search")
async def search_load_endpoint(request: Request, x_api_key: str = Header(None)):
    """Dedicated endpoint for load search"""
    
    # Verify API key
    if x_api_key != WEBHOOK_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    payload = await request.json()
    logger.info(f"Load search request: {json.dumps(payload, indent=2)}")
    
    # Extract search criteria
    equipment_type = payload.get("equipment_type", "")
    origin_preference = payload.get("origin", "")
    destination_preference = payload.get("destination", "")
    commodity_type = payload.get("commodity_type", "")
    equipment_count = payload.get("equipment_count", 1)  # Default to 1 if not provided
    
    # Generate conversation ID if not provided
    conversation_id = (
        payload.get("conversation_id") or 
        payload.get("conversationId") or 
        payload.get("call_id") or 
        payload.get("callId") or
        payload.get("session_id") or
        payload.get("sessionId") or
        f"conv_{int(datetime.now().timestamp())}"
    )

    
    # Find best matching load
    with get_db_context() as db:
        try:
            # STEP 1: Check if equipment type exists at all
            if equipment_type:
                equipment_exists = db.query(Load).filter(
                    Load.status == "available",
                    Load.equipment_type.ilike(equipment_type)
                ).first()
                
                if not equipment_exists:
                    logger.warning(f"Equipment type '{equipment_type}' does not exist in database")
                    return {
                        "load_found": False,
                        "message": "Equipment type not available",
                        "say": f"I'm sorry, but we don't have any {equipment_type} equipment available. Our available equipment types are: Dry Van, Flatbed, Reefer, and Power Only. Would you like to search for loads with any of these equipment types?",
                        "conversation_id": conversation_id
                    }
            
            # STEP 2: Equipment type exists, now search for exact match with all criteria
            exact_query = db.query(Load).filter(Load.status == "available")
            
            if equipment_type:
                exact_query = exact_query.filter(Load.equipment_type.ilike(equipment_type))
            if origin_preference:
                exact_query = exact_query.filter(Load.origin.ilike(f"%{origin_preference}%"))
            if destination_preference:
                exact_query = exact_query.filter(Load.destination.ilike(f"%{destination_preference}%"))
            if commodity_type:
                exact_query = exact_query.filter(Load.commodity_type.ilike(f"%{commodity_type}%"))
            
            load = exact_query.first()
            
            # STEP 3: If no exact match, try partial matches for location and commodity (equipment type already verified)
            if not load:
                logger.info("No exact match found, trying partial matches for location and commodity...")
                partial_query = db.query(Load).filter(
                    Load.status == "available",
                    Load.equipment_type.ilike(equipment_type) if equipment_type else True
                )
                
                # Try partial matches for origin/destination and commodity
                if origin_preference or destination_preference or commodity_type:
                    from sqlalchemy import or_
                    conditions = []
                    if origin_preference:
                        conditions.append(Load.origin.ilike(f"%{origin_preference}%"))
                    if destination_preference:
                        conditions.append(Load.destination.ilike(f"%{destination_preference}%"))
                    if commodity_type:
                        conditions.append(Load.commodity_type.ilike(f"%{commodity_type}%"))
                    
                    partial_query = partial_query.filter(or_(*conditions))
                    load = partial_query.first()
            
            # STEP 4: If still no match, return no loads found message
            if not load:
                logger.warning("No matching loads found for the criteria")
                criteria_parts = []
                if equipment_type:
                    criteria_parts.append(f"{equipment_type} equipment")
                if commodity_type:
                    criteria_parts.append(f"{commodity_type} commodity")
                if origin_preference:
                    criteria_parts.append(f"from {origin_preference}")
                if destination_preference:
                    criteria_parts.append(f"to {destination_preference}")
                
                criteria_text = ", ".join(criteria_parts) if criteria_parts else "your criteria"
                
                return {
                    "load_found": False,
                    "message": "No matching loads found",
                    "say": f"I'm sorry, but I couldn't find any loads matching {criteria_text}. Would you like me to search for other available loads?",
                    "conversation_id": conversation_id
                }
            
            # Check if requesting more equipment than we have loads for
            available_loads_count = db.query(Load).filter(
                Load.status == "available",
                Load.equipment_type.ilike(f"%{equipment_type}%") if equipment_type else True,
                Load.origin.ilike(f"%{origin_preference}%") if origin_preference else True,
                Load.destination.ilike(f"%{destination_preference}%") if destination_preference else True,
                Load.commodity_type.ilike(f"%{commodity_type}%") if commodity_type else True
            ).count()
            
            if equipment_count > available_loads_count:
                return {
                    "load_found": False,
                    "message": "Insufficient loads available",
                    "say": f"I found {available_loads_count} load(s) matching your criteria, but you're requesting {equipment_count} equipment. We only have {available_loads_count} load(s) available. Are you okay to proceed with {available_loads_count} load(s)?",
                    "conversation_id": conversation_id,
                    "available_count": available_loads_count,
                    "requested_count": equipment_count
                }
            
            if load:
                # Calculate pricing based on equipment count
                base_rate = load.loadboard_rate
                total_rate = base_rate * equipment_count
                
                # Calculate per-mile rate if miles are available
                per_mile_rate = ""
                if hasattr(load, 'miles') and load.miles and load.miles > 0:
                    per_mile = total_rate / load.miles
                    per_mile_rate = f" (${per_mile:.2f} per mile)"
                
                return {
                    "status": "success",
                    "message": "Load found",
                    "say": f"I found a great load for you! Here are the details: Load ID {load.load_id}, from {load.origin} to {load.destination}, pickup on {load.pickup_datetime}, delivery on {load.delivery_datetime}. For {equipment_count} {equipment_type}(s), the total rate is ${total_rate:,.2f}{per_mile_rate}. Weight: {load.weight:,} lbs, commodity: {load.commodity_type}. Are you interested in this load?",
                    "load_found": True,
                    "load_id": load.load_id,
                    "base_rate": base_rate,
                    "equipment_count": equipment_count,
                    "total_rate": total_rate,
                    "per_mile_rate": per_mile_rate.strip(),
                    "origin": load.origin,
                    "destination": load.destination,
                    "weight": load.weight,
                    "commodity": load.commodity_type,
                    "conversation_id": conversation_id
                }
            else:
                return {
                    "status": "no_loads",
                    "message": "No matching loads found",
                    "say": f"I don't have any loads that match your {equipment_count} {equipment_type}(s) and preferences right now. Would you like me to check for loads in different areas or with different equipment requirements?",
                    "load_found": False,
                    "conversation_id": conversation_id
                }
                
        except Exception as e:
            logger.error(f"Error searching loads: {e}")
            return {
                "status": "error",
                "message": f"Failed to search loads: {str(e)}",
                "say": "I'm sorry, there was an error searching for loads. Please try again.",
                "conversation_id": conversation_id
            }

@router.post("/webhook/happyrobot/summary")
async def summary_endpoint(request: Request, x_api_key: str = Header(None)):
    """Endpoint to save call summary, outcome, and sentiment"""
    
    # Verify API key
    if x_api_key != WEBHOOK_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    payload = await request.json()
    logger.info(f"Summary request: {json.dumps(payload, indent=2)}")
    
    # Extract summary data
    summary  = payload.get("summary","")
    session_id = payload.get("session_id")
    call_outcome = payload.get("outcome", "")
    sentiment = payload.get("sentiment", "")
    mc_number = payload.get("mc_number", "")
    carrier_name= payload.get("carrier_name","")
    duration = payload.get("duration", 0)
    
    with get_db_context() as db:
        try:
            # Create new CallLog entry
            call_log = CallLog(
                session_id=session_id,
                mc_number=mc_number,
                carrier_name=carrier_name,
                call_outcome=call_outcome,
                sentiment=sentiment,
                duration=duration,
                call_summary=summary
            )
            
            db.add(call_log)
            db.commit()
            
  
            return {
                "status": "success",
                "message": "Call summary saved successfully",
                "say": "Thank you for the call summary. The information has been recorded."
            }
            
        except Exception as e:
            logger.error(f"Error saving call summary: {e}")
            return {
                "status": "error",
                "message": f"Failed to save call summary: {str(e)}",
                "say": "There was an error saving the call summary."
            }