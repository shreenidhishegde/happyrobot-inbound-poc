from fastapi import APIRouter, Request, Header, HTTPException
from app.database import get_db_context
from app.models.load import Load, CallLog
from dotenv import load_dotenv
from app.services.fmcsa_verification import verify_mc_number
from sqlalchemy import func
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
    
    # Extract search criteria from carrier
    equipment_type = payload.get("equipment_type", "")
    origin_preference = payload.get("origin", "")
    destination_preference = payload.get("destination", "")
    weight_capacity = payload.get("weight_capacity", 0)  # Carrier's weight capacity
    available_dates = payload.get("available_dates", [])  # List of dates when carrier is available
    
    logger.info(f"Carrier capabilities - Equipment: {equipment_type}, Origin: {origin_preference}, Destination: {destination_preference}, Weight Capacity: {weight_capacity} lbs, Available Dates: {available_dates}")
    
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
            
            # STEP 2: Find loads matching carrier's criteria - check all available dates
            load = None
            best_total_rate = 0
            
            # Try each available date until we find a match
            for available_date in available_dates:
                logger.info(f"Checking loads for date: {available_date}")
                
                base_query = db.query(Load).filter(Load.status == "available")
                
                if equipment_type:
                    base_query = base_query.filter(Load.equipment_type.ilike(equipment_type))
                if origin_preference:
                    base_query = base_query.filter(Load.origin.ilike(f"%{origin_preference}%"))
                if destination_preference:
                    base_query = base_query.filter(Load.destination.ilike(f"%{destination_preference}%"))
                
                # Match pickup date - convert to datetime for proper comparison
                try:
                    target_date = datetime.strptime(available_date, "%Y-%m-%d").date()
                    base_query = base_query.filter(func.date(Load.pickup_datetime) == target_date)
                    logger.info(f"Filtering loads for pickup date: {target_date}")
                except ValueError:
                    logger.warning(f"Invalid date format: {available_date}, skipping date filter")
                    continue
                
                # Filter by weight capacity
                if weight_capacity > 0:
                    base_query = base_query.filter(Load.weight <= weight_capacity)
                
                # Find the load with the highest total rate for this date
                loads = base_query.all()
                if loads:
                    logger.info(f"Found {len(loads)} loads for date {available_date}")
                    
                    # Calculate total rate for each load and pick the best one
                    for candidate_load in loads:
                        base_rate = candidate_load.loadboard_rate
                        miles = getattr(candidate_load, 'miles', 0) or 0
                        total_rate = base_rate * miles if miles > 0 else base_rate
                        
                        if total_rate > best_total_rate:
                            best_total_rate = total_rate
                            load = candidate_load
                            logger.info(f"Found better load for {available_date} with total rate ${total_rate:,.2f}")
                    
                    # Stop at first date that has loads (we found the best one)
                    if load:
                        logger.info(f"Selected best load from date {available_date} with total rate ${best_total_rate:,.2f}")
                        break
                else:
                    logger.info(f"No loads found for date {available_date}")
            
            if not load:
                logger.info("No loads found for any of the available dates")
            
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
                if weight_capacity:
                    criteria_parts.append(f"weight capacity {weight_capacity} lbs")
                if available_dates:
                    criteria_parts.append(f"available {', '.join(available_dates)}")
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
                
                # Format the response message - tell carrier what they'll be carrying
                commodity_info = f"You'll be carrying {load.commodity_type}" if load.commodity_type else "You'll be carrying freight"
                pieces_info = f" ({load.num_of_pieces} pieces)" if getattr(load, 'num_of_pieces', None) else ""
                
                return {
                    "status": "success",
                    "message": "Load found",
                    "say": f"I found the best load for you! Load ID {load.load_id}, from {load.origin} to {load.destination}, pickup on {load.pickup_datetime.strftime('%Y-%m-%d %H:%M')}, delivery on {load.delivery_datetime.strftime('%Y-%m-%d %H:%M')}. {commodity_info}{pieces_info} weighing {load.weight:,} lbs. Your {equipment_type} can handle this perfectly! The total rate is ${total_rate:,.2f}{per_mile_rate}. Are you interested in this load?",
                    "load_found": True,
                    "load_id": load.load_id,
                    "base_rate": base_rate,
                    "total_rate": total_rate,
                    "per_mile_rate": per_mile_rate.strip(),
                    "origin": load.origin,
                    "destination": load.destination,
                    "weight": load.weight,
                    "commodity": load.commodity_type,
                    "num_of_pieces": getattr(load, 'num_of_pieces', None)
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