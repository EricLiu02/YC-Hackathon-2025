from datetime import date, datetime
from typing import List
from .models import (
    Hotel, HotelLocation, HotelReview, HotelAmenity, RoomType,
    HotelSearchResponse, HotelPricingResponse, PricingDetails, CancellationPolicy
)


DEMO_HOTELS = [
    Hotel(
        hotel_id="grand_plaza_nyc_001",
        name="Grand Plaza Hotel NYC",
        location=HotelLocation(
            address="768 5th Avenue, New York, NY 10019",
            latitude=40.7614,
            longitude=-73.9776,
            distance_to_center="0.2 miles from Times Square"
        ),
        star_rating=4,
        review=HotelReview(
            rating=4.2,
            total_reviews=2847,
            source="Google Reviews"
        ),
        amenities=[
            HotelAmenity(name="Free WiFi"),
            HotelAmenity(name="Fitness Center"),
            HotelAmenity(name="Business Center"),
            HotelAmenity(name="24/7 Room Service"),
            HotelAmenity(name="Concierge")
        ],
        images=[
            "https://example.com/hotel1_lobby.jpg",
            "https://example.com/hotel1_room.jpg",
            "https://example.com/hotel1_exterior.jpg"
        ],
        description="Luxury hotel in the heart of Manhattan with stunning city views and world-class amenities.",
        rooms=[
            RoomType(
                room_id="std_king_001",
                room_name="Standard King Room",
                description="Spacious king room with city views",
                max_occupancy=2,
                bed_info="1 King Bed",
                price_per_night=299.00,
                total_price=598.00,
                currency="USD",
                cancellation_policy="Free cancellation until 24 hours before check-in",
                breakfast_included=False
            ),
            RoomType(
                room_id="deluxe_suite_001",
                room_name="Deluxe Suite",
                description="Luxury suite with separate living area",
                max_occupancy=4,
                bed_info="1 King Bed + Sofa Bed",
                price_per_night=499.00,
                total_price=998.00,
                currency="USD",
                cancellation_policy="Free cancellation until 48 hours before check-in",
                breakfast_included=True
            )
        ],
        price_range="$299 - $499 per night"
    ),
    Hotel(
        hotel_id="boutique_central_nyc_002",
        name="Boutique Central Hotel",
        location=HotelLocation(
            address="129 W 46th St, New York, NY 10036",
            latitude=40.7580,
            longitude=-73.9855,
            distance_to_center="0.1 miles from Times Square"
        ),
        star_rating=3,
        review=HotelReview(
            rating=4.0,
            total_reviews=1923,
            source="Google Reviews"
        ),
        amenities=[
            HotelAmenity(name="Free WiFi"),
            HotelAmenity(name="Pet Friendly"),
            HotelAmenity(name="Luggage Storage"),
            HotelAmenity(name="24-hour Front Desk")
        ],
        images=[
            "https://example.com/hotel2_lobby.jpg",
            "https://example.com/hotel2_room.jpg"
        ],
        description="Charming boutique hotel with modern amenities and personalized service.",
        rooms=[
            RoomType(
                room_id="cozy_queen_002",
                room_name="Cozy Queen Room",
                description="Comfortable queen room with modern decor",
                max_occupancy=2,
                bed_info="1 Queen Bed",
                price_per_night=189.00,
                total_price=378.00,
                currency="USD",
                cancellation_policy="Free cancellation until 24 hours before check-in",
                breakfast_included=True
            )
        ],
        price_range="$189 per night"
    ),
    Hotel(
        hotel_id="luxury_manhattan_003",
        name="Luxury Manhattan Resort",
        location=HotelLocation(
            address="2 E 55th St, New York, NY 10022",
            latitude=40.7614,
            longitude=-73.9776,
            distance_to_center="0.5 miles from Central Park"
        ),
        star_rating=5,
        review=HotelReview(
            rating=4.6,
            total_reviews=3241,
            source="Google Reviews"
        ),
        amenities=[
            HotelAmenity(name="Free WiFi"),
            HotelAmenity(name="Spa & Wellness Center"),
            HotelAmenity(name="Indoor Pool"),
            HotelAmenity(name="Fine Dining Restaurant"),
            HotelAmenity(name="Valet Parking"),
            HotelAmenity(name="Butler Service")
        ],
        images=[
            "https://example.com/hotel3_lobby.jpg",
            "https://example.com/hotel3_pool.jpg",
            "https://example.com/hotel3_suite.jpg"
        ],
        description="Five-star luxury resort featuring world-class spa, fine dining, and premium accommodations.",
        rooms=[
            RoomType(
                room_id="exec_suite_003",
                room_name="Executive Suite",
                description="Luxurious suite with panoramic city views",
                max_occupancy=3,
                bed_info="1 King Bed + Day Bed",
                price_per_night=799.00,
                total_price=1598.00,
                currency="USD",
                cancellation_policy="Free cancellation until 72 hours before check-in",
                breakfast_included=True
            )
        ],
        price_range="$799 per night"
    )
]


def get_demo_hotel_search_response(city: str, check_in: date, check_out: date) -> HotelSearchResponse:
    search_id = f"demo_search_{city.lower().replace(' ', '_')}_{check_in}_{check_out}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Update room prices based on number of nights
    nights = (check_out - check_in).days
    demo_hotels = []
    
    for hotel in DEMO_HOTELS:
        hotel_copy = hotel.model_copy(deep=True)
        for room in hotel_copy.rooms:
            room.total_price = room.price_per_night * nights
        demo_hotels.append(hotel_copy)
    
    return HotelSearchResponse(
        hotels=demo_hotels,
        search_id=search_id,
        total_results=len(demo_hotels),
        city=city,
        check_in_date=check_in,
        check_out_date=check_out
    )


def get_demo_hotel_pricing(hotel_id: str, check_in: date, check_out: date, room_type: str = None) -> HotelPricingResponse:
    # Find the hotel
    hotel = None
    for h in DEMO_HOTELS:
        if h.hotel_id == hotel_id:
            hotel = h
            break
    
    if not hotel:
        # Default pricing if hotel not found
        nights = (check_out - check_in).days
        base_price = 250.00 * nights
        return HotelPricingResponse(
            hotel_id=hotel_id,
            hotel_name="Unknown Hotel",
            room_type=room_type or "Standard Room",
            pricing=PricingDetails(
                base_price=base_price,
                taxes_and_fees=base_price * 0.18,
                total_price=base_price * 1.18,
                currency="USD",
                price_per_night=250.00,
                total_nights=nights
            ),
            cancellation_policy=CancellationPolicy(
                is_refundable=True,
                cancellation_deadline=check_in,
                penalty_amount=0.0,
                policy_description="Free cancellation until check-in date"
            )
        )
    
    # Find the specific room type or use the first one
    room = hotel.rooms[0]
    if room_type:
        for r in hotel.rooms:
            if room_type.lower() in r.room_name.lower():
                room = r
                break
    
    nights = (check_out - check_in).days
    base_price = room.price_per_night * nights
    taxes_and_fees = base_price * 0.18
    
    return HotelPricingResponse(
        hotel_id=hotel_id,
        hotel_name=hotel.name,
        room_type=room.room_name,
        pricing=PricingDetails(
            base_price=base_price,
            taxes_and_fees=taxes_and_fees,
            total_price=base_price + taxes_and_fees,
            currency="USD",
            price_per_night=room.price_per_night,
            total_nights=nights
        ),
        cancellation_policy=CancellationPolicy(
            is_refundable=True,
            cancellation_deadline=check_in,
            penalty_amount=0.0,
            policy_description=room.cancellation_policy or "Standard cancellation policy applies"
        ),
        booking_conditions=[
            "Valid credit card required at booking",
            "Photo ID required at check-in",
            "Minimum age requirement: 18 years"
        ],
        last_updated=datetime.now().isoformat()
    )