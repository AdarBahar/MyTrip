"""
Database seeding script
"""
import asyncio
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models import Base
from app.models.user import User, UserStatus
from app.models.trip import Trip, TripMember, TripStatus, TripMemberRole, TripMemberStatus
from app.models.day import Day, DayStatus
from app.models.place import Place, OwnerType
from app.models.stop import Stop, StopKind
from app.models.pin import Pin
from app.services.routing import get_routing_provider, RoutePoint


def create_demo_data():
    """Create demo data for development"""

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if demo data already exists
        existing_user = db.query(User).filter(User.email == "demo@roadtrip.com").first()
        if existing_user:
            print("Demo data already exists, skipping...")
            return

        print("Creating demo data...")

        # Create demo user
        demo_user = User(
            email="demo@roadtrip.com",
            display_name="Demo User",
            status=UserStatus.ACTIVE
        )
        db.add(demo_user)
        db.flush()

        # Create demo trip
        demo_trip = Trip(
            slug="california-coast",
            title="California Coast Road Trip",
            destination="California, USA",
            start_date=date(2024, 6, 15),
            timezone="America/Los_Angeles",
            status=TripStatus.ACTIVE,
            is_published=True,
            created_by=demo_user.id
        )
        db.add(demo_trip)
        db.flush()

        # Create trip member (owner)
        trip_member = TripMember(
            trip_id=demo_trip.id,
            user_id=demo_user.id,
            role=TripMemberRole.OWNER,
            status=TripMemberStatus.ACTIVE
        )
        db.add(trip_member)

        # Create places
        places_data = [
            {
                "name": "San Francisco",
                "address": "San Francisco, CA, USA",
                "lat": 37.7749,
                "lon": -122.4194
            },
            {
                "name": "Monterey",
                "address": "Monterey, CA, USA",
                "lat": 36.6002,
                "lon": -121.8947
            },
            {
                "name": "Big Sur",
                "address": "Big Sur, CA, USA",
                "lat": 36.2704,
                "lon": -121.8081
            },
            {
                "name": "San Luis Obispo",
                "address": "San Luis Obispo, CA, USA",
                "lat": 35.2828,
                "lon": -120.6596
            },
            {
                "name": "Santa Barbara",
                "address": "Santa Barbara, CA, USA",
                "lat": 34.4208,
                "lon": -119.6982
            },
            {
                "name": "Los Angeles",
                "address": "Los Angeles, CA, USA",
                "lat": 34.0522,
                "lon": -118.2437
            }
        ]

        places = []
        for place_data in places_data:
            place = Place(
                owner_type=OwnerType.TRIP,
                owner_id=demo_trip.id,
                name=place_data["name"],
                address=place_data["address"],
                lat=place_data["lat"],
                lon=place_data["lon"]
            )
            places.append(place)
            db.add(place)

        db.flush()

        # Create days
        day1 = Day(
            trip_id=demo_trip.id,
            seq=1,
            date=date(2024, 6, 15),
            status=DayStatus.ACTIVE,
            rest_day=False,
            notes={"description": "San Francisco to Monterey via scenic Highway 1"}
        )

        day2 = Day(
            trip_id=demo_trip.id,
            seq=2,
            date=date(2024, 6, 16),
            status=DayStatus.ACTIVE,
            rest_day=False,
            notes={"description": "Monterey to Santa Barbara via Big Sur"}
        )

        db.add_all([day1, day2])
        db.flush()

        # Create stops for day 1
        stops_day1 = [
            Stop(
                day_id=day1.id,
                trip_id=demo_trip.id,
                place_id=places[0].id,  # San Francisco
                seq=1,
                kind=StopKind.START,
                fixed=True,
                notes="Starting point - Golden Gate Bridge area"
            ),
            Stop(
                day_id=day1.id,
                trip_id=demo_trip.id,
                place_id=places[1].id,  # Monterey
                seq=2,
                kind=StopKind.END,
                fixed=True,
                notes="End point - Monterey Bay"
            )
        ]

        # Create stops for day 2
        stops_day2 = [
            Stop(
                day_id=day2.id,
                trip_id=demo_trip.id,
                place_id=places[1].id,  # Monterey
                seq=1,
                kind=StopKind.START,
                fixed=True,
                notes="Starting from Monterey"
            ),
            Stop(
                day_id=day2.id,
                trip_id=demo_trip.id,
                place_id=places[2].id,  # Big Sur
                seq=2,
                kind=StopKind.VIA,
                fixed=False,
                notes="Scenic stop at Big Sur"
            ),
            Stop(
                day_id=day2.id,
                trip_id=demo_trip.id,
                place_id=places[4].id,  # Santa Barbara
                seq=3,
                kind=StopKind.END,
                fixed=True,
                notes="End point - Santa Barbara"
            )
        ]

        db.add_all(stops_day1 + stops_day2)

        # Create some pins
        pins = [
            Pin(
                trip_id=demo_trip.id,
                place_id=places[3].id,  # San Luis Obispo
                name="San Luis Obispo - Optional Stop",
                lat=places[3].lat,
                lon=places[3].lon,
                order_index=1,
                meta={"type": "optional_stop", "category": "city"}
            ),
            Pin(
                trip_id=demo_trip.id,
                place_id=places[5].id,  # Los Angeles
                name="Los Angeles - Future Extension",
                lat=places[5].lat,
                lon=places[5].lon,
                order_index=2,
                meta={"type": "future_destination", "category": "city"}
            )
        ]

        db.add_all(pins)

        db.commit()
        print("Demo data created successfully!")

        # Print summary
        print(f"Created:")
        print(f"  - 1 demo user: {demo_user.email}")
        print(f"  - 1 demo trip: {demo_trip.title}")
        print(f"  - {len(places)} places")
        print(f"  - 2 days with stops")
        print(f"  - {len(pins)} pins")

    except Exception as e:
        db.rollback()
        print(f"Error creating demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_demo_data()