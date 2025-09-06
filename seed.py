#!/usr/bin/env python3
"""
Seed script to populate the database with sample loads for testing
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import engine, Base, get_db_context
from app.models.load import Load

def create_sample_loads():
    """Create sample loads for testing"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    with get_db_context() as db:
        # Check if loads already exist
        existing_loads = db.query(Load).count()
        if existing_loads > 0:
            return
        
        # Sample loads data
        sample_loads = [
            {
                "origin": "Chicago, IL",
                "destination": "Dallas, TX",
                "pickup_datetime": datetime.now() + timedelta(days=1, hours=10),
                "delivery_datetime": datetime.now() + timedelta(days=3, hours=18),
                "equipment_type": "Dry Van",
                "loadboard_rate": 2.50,
                "notes": "No hazmat, residential delivery",
                "weight": 20000,
                "commodity_type": "Electronics",
                "num_of_pieces": 150,
                "miles": 800,
                "dimensions": "53' x 8.5' x 8.5'",
                "status": "available"
            },
            {
                "origin": "Los Angeles, CA",
                "destination": "Phoenix, AZ",
                "pickup_datetime": datetime.now() + timedelta(days=1, hours=8),
                "delivery_datetime": datetime.now() + timedelta(days=1, hours=20),
                "equipment_type": "Flatbed",
                "loadboard_rate": 3.25,
                "notes": "Tarps required, oversized load",
                "weight": 30000,
                "commodity_type": "Steel",
                "num_of_pieces": 25,
                "miles": 400,
                "dimensions": "48' x 8.5' x 12'",
                "status": "available"
            },
            {
                "origin": "Atlanta, GA",
                "destination": "Miami, FL",
                "pickup_datetime": datetime.now() + timedelta(days=2, hours=9),
                "delivery_datetime": datetime.now() + timedelta(days=3, hours=15),
                "equipment_type": "Reefer",
                "loadboard_rate": 2.75,
                "notes": "Temperature controlled, food grade",
                "weight": 25000,
                "commodity_type": "Frozen Foods",
                "num_of_pieces": 200,
                "miles": 650,
                "dimensions": "53' x 8.5' x 8.5'",
                "status": "available"
            },
            {
                "origin": "Seattle, WA",
                "destination": "Portland, OR",
                "pickup_datetime": datetime.now() + timedelta(days=1, hours=14),
                "delivery_datetime": datetime.now() + timedelta(days=1, hours=22),
                "equipment_type": "Dry Van",
                "loadboard_rate": 2.00,
                "notes": "Express delivery, no stops",
                "weight": 15000,
                "commodity_type": "Apparel",
                "num_of_pieces": 300,
                "miles": 175,
                "dimensions": "53' x 8.5' x 8.5'",
                "status": "available"
            },
            {
                "origin": "Denver, CO",
                "destination": "Kansas City, MO",
                "pickup_datetime": datetime.now() + timedelta(days=2, hours=7),
                "delivery_datetime": datetime.now() + timedelta(days=3, hours=12),
                "equipment_type": "Power Only",
                "loadboard_rate": 1.75,
                "notes": "Trailer provided, driver assist loading",
                "weight": 18000,
                "commodity_type": "Machinery",
                "num_of_pieces": 5,
                "miles": 600,
                "dimensions": "53' x 8.5' x 8.5'",
                "status": "available"
            },
            {
                "origin": "Los Angeles, CA",
                "destination": "Phoenix, AZ",
                "pickup_datetime": datetime.now() + timedelta(days=1, hours=12),
                "delivery_datetime": datetime.now() + timedelta(days=2, hours=8),
                "equipment_type": "Dry Van",
                "loadboard_rate": 2.80,
                "notes": "Fragile electronics, white glove delivery",
                "weight": 12000,
                "commodity_type": "TVs",
                "num_of_pieces": 50,
                "miles": 400,
                "dimensions": "53' x 8.5' x 8.5'",
                "status": "available"
            }
        ]
        
        # Create and add loads
        for load_data in sample_loads:
            load = Load(**load_data)
            db.add(load)
        
        # Commit all loads
        db.commit()
        
        print(f"✅ Successfully created {len(sample_loads)} sample loads:")
        for load in sample_loads:
            print(f"   - {load['origin']} → {load['destination']} ({load['equipment_type']}) - ${load['loadboard_rate']}/mile")
        
        print("\n🚀 Database is now ready for testing!")

def main():
    """Main function"""
    
    try:
        create_sample_loads()
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    main()
