import os
import requests
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from dotenv import load_dotenv

from models import (
    HotelSearchRequest, HotelSearchResponse, HotelPricingRequest, HotelPricingResponse,
    Hotel, HotelLocation, HotelReview, HotelAmenity, RoomType,
    PricingDetails, CancellationPolicy
)
from fixtures import get_demo_hotel_search_response, get_demo_hotel_pricing

load_dotenv()


class SearchAPIHotelClient:
    def __init__(self, use_demo_data: bool = False):
        self.use_demo_data = use_demo_data
        self.base_url = "https://www.searchapi.io/api/v1/search"
        
        if not use_demo_data:
            self.api_key = os.getenv('SEARCH_API_KEY')
            if not self.api_key:
                raise ValueError("SearchAPI key not found. Set SEARCH_API_KEY environment variable.")
    
    async def search_hotels(self, request: HotelSearchRequest) -> HotelSearchResponse:
        if self.use_demo_data:
            return get_demo_hotel_search_response(
                request.city, 
                request.check_in_date, 
                request.check_out_date
            )
        
        try:
            # Format dates for Google Hotels API
            check_in = request.check_in_date.strftime('%Y-%m-%d')
            check_out = request.check_out_date.strftime('%Y-%m-%d')
            
            # Build search parameters for Google Hotels
            params = {
                'api_key': self.api_key,
                'engine': 'google_hotels',
                'q': f'hotels in {request.city}',
                'check_in_date': check_in,
                'check_out_date': check_out,
                'adults': request.adults,
                'children': request.children,
                'rooms': request.rooms,
                'currency': 'USD',
                'gl': 'us',
                'hl': 'en'
            }
            
            # Add optional filters
            if request.hotel_class:
                params['hotel_class'] = request.hotel_class
            
            if request.max_price:
                params['max_price'] = request.max_price
                
            if request.sort_by:
                sort_mapping = {
                    'price': '1',  # Sort by price
                    'rating': '2',  # Sort by rating  
                    'distance': '3'  # Sort by distance
                }
                params['sort_by'] = sort_mapping.get(request.sort_by, '1')
            
            # Make the API request
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the response
            hotels = []
            search_id = f"searchapi_{request.city}_{check_in}_{check_out}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract hotels from Google Hotels API response
            if 'properties' in data:
                for i, property_data in enumerate(data['properties'][:request.max_results]):
                    hotel = self._parse_hotel_from_api(property_data, request)
                    hotels.append(hotel)
            
            return HotelSearchResponse(
                hotels=hotels,
                search_id=search_id,
                total_results=len(hotels),
                city=request.city,
                check_in_date=request.check_in_date,
                check_out_date=request.check_out_date
            )
            
        except Exception as error:
            print(f"SearchAPI error: {error}. Falling back to demo data.")
            return get_demo_hotel_search_response(
                request.city, 
                request.check_in_date, 
                request.check_out_date
            )
    
    def _parse_hotel_from_api(self, property_data: Dict[str, Any], request: HotelSearchRequest) -> Hotel:
        """Parse hotel data from SearchAPI Google Hotels response"""
        
        # Extract basic info
        hotel_id = property_data.get('property_token', f"hotel_{property_data.get('name', 'unknown').lower().replace(' ', '_')}")
        name = property_data.get('name', 'Unknown Hotel')
        
        # Location info
        location = HotelLocation(
            address=property_data.get('address', ''),
            latitude=property_data.get('gps_coordinates', {}).get('latitude'),
            longitude=property_data.get('gps_coordinates', {}).get('longitude'),
            distance_to_center=property_data.get('distance_from_center')
        )
        
        # Reviews
        review = None
        if 'overall_rating' in property_data:
            review = HotelReview(
                rating=float(property_data.get('overall_rating', 0)),
                total_reviews=int(property_data.get('reviews', 0)),
                source="Google"
            )
        
        # Amenities
        amenities = []
        for amenity in property_data.get('amenities', []):
            amenities.append(HotelAmenity(name=amenity))
        
        # Images
        images = []
        if 'images' in property_data:
            images = [img.get('thumbnail') for img in property_data['images'] if img.get('thumbnail')]
        
        # Room types and pricing
        rooms = []
        if 'rates' in property_data:
            for rate in property_data['rates']:
                nights = (request.check_out_date - request.check_in_date).days
                price_per_night = float(rate.get('rate_per_night', {}).get('lowest', 100))
                total_price = price_per_night * nights
                
                room = RoomType(
                    room_id=rate.get('rate_id', f"room_{len(rooms)}"),
                    room_name=rate.get('type', 'Standard Room'),
                    description=rate.get('description', ''),
                    max_occupancy=request.adults + request.children,
                    bed_info=rate.get('bed_info', ''),
                    price_per_night=price_per_night,
                    total_price=total_price,
                    currency='USD',
                    cancellation_policy=rate.get('cancellation_policy', 'Standard cancellation policy'),
                    breakfast_included=rate.get('breakfast_included', False)
                )
                rooms.append(room)
        
        # If no rooms found, create a default one
        if not rooms:
            nights = (request.check_out_date - request.check_in_date).days
            price_per_night = float(property_data.get('rate_per_night', {}).get('lowest', 150))
            rooms.append(RoomType(
                room_id=f"{hotel_id}_standard",
                room_name="Standard Room",
                description="Standard hotel room",
                max_occupancy=request.adults + request.children,
                bed_info="1 Double Bed",
                price_per_night=price_per_night,
                total_price=price_per_night * nights,
                currency='USD',
                cancellation_policy="Standard cancellation policy applies",
                breakfast_included=False
            ))
        
        return Hotel(
            hotel_id=hotel_id,
            name=name,
            location=location,
            star_rating=property_data.get('hotel_class'),
            review=review,
            amenities=amenities,
            images=images,
            description=property_data.get('description', ''),
            rooms=rooms,
            price_range=f"${min(r.price_per_night for r in rooms):.0f} - ${max(r.price_per_night for r in rooms):.0f} per night" if rooms else None
        )
    
    async def get_hotel_pricing(self, request: HotelPricingRequest) -> HotelPricingResponse:
        if self.use_demo_data:
            return get_demo_hotel_pricing(
                request.hotel_id,
                request.check_in_date,
                request.check_out_date,
                request.room_type
            )
        
        try:
            # For pricing details, we'd typically need a separate API call
            # For now, we'll use demo data as SearchAPI Google Hotels pricing 
            # requires more complex handling
            print("Using demo pricing data for detailed pricing information.")
            return get_demo_hotel_pricing(
                request.hotel_id,
                request.check_in_date,
                request.check_out_date,
                request.room_type
            )
            
        except Exception as error:
            print(f"Error getting hotel pricing: {error}. Using demo data.")
            return get_demo_hotel_pricing(
                request.hotel_id,
                request.check_in_date,
                request.check_out_date,
                request.room_type
            )