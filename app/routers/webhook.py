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
            "say": f"Excellent! Your MC number {mc_number} has been verified. Welcome, {carrier_name}! You're eligible to work with us. Let me search for available loads that match your equipment."
        }
    else:
        return {
            "verified": False,
            "message": "MC number verification failed",
            "say": "I'm sorry, but your MC number is not eligible to work with us at this time. Please contact our compliance department for more information."
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
    commodity_count = payload.get("commodity_count", "")
    
    logger.info(f"Search criteria - Equipment: {equipment_type}, Origin: {origin_preference}, Destination: {destination_preference}, Commodity: {commodity_type}, Count: {commodity_count}")
    
    # Convert commodity_count to integer for capacity checking
    requested_pieces = None
    if commodity_count:
        requested_pieces = int(commodity_count)
        logger.info(f"Carrier requesting to transport {requested_pieces} pieces")
    
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
                        "say": f"I'm sorry, but we don't have any {equipment_type} equipment available. Our available equipment types are: Dry Van, Flatbed, Reefer, and Power Only. Would you like to search for loads with any of these equipment types?"
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
            
            # STEP 2.5: Check capacity if carrier specified commodity_count
            if load and requested_pieces is not None:
                load_capacity = getattr(load, 'num_of_pieces', None)
                if load_capacity and requested_pieces > load_capacity:
                    logger.warning(f"Carrier requesting {requested_pieces} pieces but load only has capacity for {load_capacity} pieces")
                    return {
                        "load_found": False,
                        "message": "Insufficient capacity",
                        "say": f"I found a load, but it only has capacity for {load_capacity} pieces, and you're requesting to transport {requested_pieces} pieces. This equipment doesn't have enough capacity for that much load. Would you like me to search for other available loads?"
                    }
            
            # STEP 3: If no exact match, try partial matches for location only (equipment type already verified)
            if not load:
                logger.info("No exact match found, trying partial matches for location...")
                partial_query = db.query(Load).filter(
                    Load.status == "available",
                    Load.equipment_type.ilike(equipment_type) if equipment_type else True
                )
                
                # Try partial matches for origin/destination only
                if origin_preference or destination_preference:
                    from sqlalchemy import or_
                    conditions = []
                    if origin_preference:
                        conditions.append(Load.origin.ilike(f"%{origin_preference}%"))
                    if destination_preference:
                        conditions.append(Load.destination.ilike(f"%{destination_preference}%"))
                    
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
                if requested_pieces:
                    criteria_parts.append(f"{requested_pieces} pieces")
                if origin_preference:
                    criteria_parts.append(f"from {origin_preference}")
                if destination_preference:
                    criteria_parts.append(f"to {destination_preference}")
                
                criteria_text = ", ".join(criteria_parts) if criteria_parts else "your criteria"
                
                return {
                    "load_found": False,
                    "message": "No matching loads found",
                    "say": f"I'm sorry, but I couldn't find any loads matching {criteria_text}. Would you like me to search for other available loads?"
                }
            
            if load:
                logger.info(f"Load found: ID {load.load_id}, Equipment: {load.equipment_type}, Commodity: {load.commodity_type}, Origin: {load.origin}, Destination: {load.destination}")
                
                # Calculate pricing based on the load details
                base_rate = load.loadboard_rate
                miles = getattr(load, 'miles', 0) or 0
                
                # Calculate total rate based on miles and rate per mile
                if miles > 0:
                    total_rate = base_rate * miles
                    per_mile_rate = f" (${base_rate:.2f} per mile)"
                else:
                    total_rate = base_rate
                    per_mile_rate = ""
                
                # Format the response message
                commodity_info = f"commodity: {load.commodity_type}" if load.commodity_type else ""
                pieces_info = f", {load.num_of_pieces} pieces" if getattr(load, 'num_of_pieces', None) else ""
                
                return {
                    "status": "success",
                    "message": "Load found",
                    "say": f"I found a great load for you! Here are the details: Load ID {load.load_id}, from {load.origin} to {load.destination}, pickup on {load.pickup_datetime.strftime('%Y-%m-%d %H:%M')}, delivery on {load.delivery_datetime.strftime('%Y-%m-%d %H:%M')}. The total rate is ${total_rate:,.2f}{per_mile_rate}. Weight: {load.weight:,} lbs{pieces_info}, {commodity_info}. Are you interested in this load?",
                    "load_found": True,
                    "load_id": load.load_id,
                    "total_rate": total_rate,
                    "per_mile_rate": per_mile_rate.strip(),
                    "origin": load.origin,
                    "destination": load.destination,
                    "weight": load.weight,
                    "commodity": load.commodity_type
                }
            else:
                return {
                    "status": "no_loads",
                    "message": "No matching loads found",
                    "say": f"I don't have any loads that match your {equipment_type} equipment and preferences right now. Would you like me to check for loads in different areas or with different equipment requirements?",
                    "load_found": False
                }
                
        except Exception as e:
            logger.error(f"Error searching loads: {e}")
            return {
                "status": "error",
                "message": f"Failed to search loads: {str(e)}",
                "say": "I'm sorry, there was an error searching for loads. Please try again."
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
    summary = payload.get("summary", "")
    session_id = payload.get("session_id")
    call_outcome = payload.get("outcome", "")
    sentiment = payload.get("sentiment", "")
    mc_number = payload.get("mc_number", "")
    carrier_name = payload.get("carrier_name", "")
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