import os
import requests
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from dotenv import load_dotenv

# Try absolute imports first
try:
    from models import (
        HotelSearchRequest, HotelSearchResponse, HotelPricingRequest, HotelPricingResponse,
        Hotel, HotelLocation, HotelReview, HotelAmenity, RoomType,
        PricingDetails, CancellationPolicy
    )
    from location_enricher import PerplexityLocationEnricher, LocationInfo
except ImportError:
    # Fall back to relative imports
    from .models import (
        HotelSearchRequest, HotelSearchResponse, HotelPricingRequest, HotelPricingResponse,
        Hotel, HotelLocation, HotelReview, HotelAmenity, RoomType,
        PricingDetails, CancellationPolicy
    )
    from .location_enricher import PerplexityLocationEnricher, LocationInfo

load_dotenv()


class SearchAPIHotelClient:
    def __init__(self):
        self.base_url = "https://www.searchapi.io/api/v1/search"
        
        # Initialize location enricher
        try:
            self.location_enricher = PerplexityLocationEnricher()
            self.use_location_enrichment = True
        except ValueError:
            print("Warning: PERPLEXITY_API_KEY not found. Location enrichment disabled.")
            self.use_location_enrichment = False
        
        # Require API key for operation
        self.api_key = os.getenv('SEARCH_API_KEY') or os.getenv('SEARCHAPI_KEY')
        if not self.api_key:
            raise ValueError("SearchAPI key required. Set SEARCH_API_KEY or SEARCHAPI_KEY environment variable.")
    
    async def search_hotels(self, request: HotelSearchRequest) -> HotelSearchResponse:
        try:
            # Enrich location data using Perplexity if available
            location_info = None
            if self.use_location_enrichment:
                try:
                    user_query = f"hotels in {request.city}"
                    location_info = await self.location_enricher.enrich_location(user_query)
                    print(f"✨ Location enriched: {location_info.city}, {location_info.country}")
                except Exception as e:
                    print(f"Location enrichment failed: {e}. Using basic location data.")
            
            # Format dates for Google Hotels API
            check_in = request.check_in_date.strftime('%Y-%m-%d')
            check_out = request.check_out_date.strftime('%Y-%m-%d')
            
            # Build search parameters for Google Hotels with enriched data
            params = {
                'api_key': self.api_key,
                'engine': 'google_hotels',
                'q': f'hotels in {location_info.city if location_info else request.city}',
                'check_in_date': check_in,
                'check_out_date': check_out,
                'adults': request.adults,
                'children': request.children,
                'rooms': request.rooms,
                'currency': location_info.currency if location_info and location_info.currency else 'USD',
                'gl': location_info.country_code.lower() if location_info and location_info.country_code else 'us',
                'hl': 'en'
            }
            
            # Add bounding box if available for more precise location search
            if location_info and location_info.bounding_box:
                params['bounding_box'] = ','.join(map(str, location_info.bounding_box))
            
            # Add optional filters
            if request.hotel_class:
                params['hotel_class'] = request.hotel_class  # e.g., "4,5" for 4-5 star hotels
            
            if request.max_price:
                params['max_price'] = request.max_price
                
            # Add sort_by parameter using correct SearchAPI values
            if request.sort_by:
                sort_mapping = {
                    'price': 'lowest_price',
                    'rating': 'highest_rating', 
                    'distance': 'relevance',  # Closest approximation
                    'top': 'highest_rating'
                }
                if request.sort_by in sort_mapping:
                    params['sort_by'] = sort_mapping[request.sort_by]
            
            # Make the API request
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the response
            hotels = []
            final_city = location_info.city if location_info else request.city
            search_id = f"searchapi_{final_city}_{check_in}_{check_out}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract hotels from Google Hotels API response
            if 'properties' in data:
                for i, property_data in enumerate(data['properties'][:request.max_results]):
                    hotel = self._parse_hotel_from_api(property_data, request, location_info)
                    hotels.append(hotel)
            
            return HotelSearchResponse(
                hotels=hotels,
                search_id=search_id,
                total_results=len(hotels),
                city=final_city,
                check_in_date=request.check_in_date,
                check_out_date=request.check_out_date
            )
            
        except Exception as error:
            print(f"SearchAPI error: {error}")
            raise
    
    def _parse_hotel_from_api(self, property_data: Dict[str, Any], request: HotelSearchRequest, location_info: Optional[LocationInfo] = None) -> Hotel:
        """Parse hotel data from SearchAPI Google Hotels response"""
        
        # Extract basic info
        hotel_id = property_data.get('property_token', f"hotel_{property_data.get('name', 'unknown').lower().replace(' ', '_')}")
        name = property_data.get('name', 'Unknown Hotel')
        
        # Extract star rating - debug what we're getting
        star_rating = property_data.get('extracted_hotel_class')
        if star_rating is None:
            # Fallback: try to parse from hotel_class string 
            hotel_class_str = property_data.get('hotel_class', '')
            if 'star' in hotel_class_str:
                try:
                    star_rating = int(hotel_class_str.split('-')[0])
                except:
                    pass
        
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
        
        # Room types and pricing - SearchAPI returns pricing in property level
        rooms = []
        nights = (request.check_out_date - request.check_in_date).days
        currency = location_info.currency if location_info and location_info.currency else 'USD'
        
        # Get price per night from the property data
        price_per_night = 150  # Default fallback
        if 'price_per_night' in property_data and 'extracted_price' in property_data['price_per_night']:
            price_per_night = float(property_data['price_per_night']['extracted_price'])
        elif 'total_price' in property_data and 'extracted_price' in property_data['total_price']:
            price_per_night = float(property_data['total_price']['extracted_price'])
        
        total_price = price_per_night * nights
        
        # Create a default room since SearchAPI doesn't provide detailed room types
        rooms.append(RoomType(
            room_id=f"{hotel_id}_standard",
            room_name="Standard Room",
            description="Standard hotel room",
            max_occupancy=request.adults + request.children,
            bed_info="Standard bed configuration",
            price_per_night=price_per_night,
            total_price=total_price,
            currency=currency,
            cancellation_policy="Standard cancellation policy applies",
            breakfast_included=False
        ))
        
        return Hotel(
            hotel_id=hotel_id,
            name=name,
            location=location,
            star_rating=star_rating,  # Use parsed star rating
            review=review,
            amenities=amenities,
            images=images,
            description=property_data.get('description', ''),
            rooms=rooms,
            price_range=f"${min(r.price_per_night for r in rooms):.0f} - ${max(r.price_per_night for r in rooms):.0f} per night" if rooms else None
        )
    
    async def get_hotel_pricing(self, request: HotelPricingRequest) -> HotelPricingResponse:
        # SearchAPI Google Hotels doesn't provide separate pricing endpoint
        # Pricing is included in the search results
        raise NotImplementedError("Detailed pricing is included in hotel search results. Use search_hotels instead.")