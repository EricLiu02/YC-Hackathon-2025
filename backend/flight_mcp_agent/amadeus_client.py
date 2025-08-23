import os
from typing import List, Optional
from datetime import date
from amadeus import Client, ResponseError
from dotenv import load_dotenv

from .models import FlightSearchRequest, FlightSearchResponse, FlightOption, FlightPricingRequest, FlightPricingResponse, PriceBreakdown
from .fixtures import get_demo_flight_search_response, get_demo_flight_pricing

load_dotenv()


class AmadeusFlightClient:
    def __init__(self, use_demo_data: bool = False):
        self.use_demo_data = use_demo_data
        
        if not use_demo_data:
            api_key = os.getenv('AMADEUS_API_KEY')
            api_secret = os.getenv('AMADEUS_API_SECRET')
            
            if not api_key or not api_secret:
                raise ValueError("Amadeus API credentials not found. Set AMADEUS_API_KEY and AMADEUS_API_SECRET environment variables.")
            
            self.amadeus = Client(
                client_id=api_key,
                client_secret=api_secret
            )
    
    async def search_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        if self.use_demo_data:
            return get_demo_flight_search_response(request.origin, request.destination)
        
        try:
            # Build the search parameters
            params = {
                'originLocationCode': request.origin,
                'destinationLocationCode': request.destination,
                'departureDate': request.departure_date.isoformat(),
                'adults': request.adults,
                'max': request.max_results
            }
            
            if request.return_date:
                params['returnDate'] = request.return_date.isoformat()
            
            if request.children > 0:
                params['children'] = request.children
                
            if request.infants > 0:
                params['infants'] = request.infants
                
            if request.travel_class:
                params['travelClass'] = request.travel_class

            # Make the API call
            response = self.amadeus.shopping.flight_offers_search.get(**params)
            
            # Parse the response
            flights = []
            search_id = f"amadeus_search_{request.origin}_{request.destination}_{request.departure_date}"
            
            for offer in response.data:
                for itinerary in offer['itineraries']:
                    for segment in itinerary['segments']:
                        flight = FlightOption(
                            flight_id=f"{segment['carrierCode']}{segment['number']}_{segment['departure']['at'][:10]}",
                            airline_code=segment['carrierCode'],
                            airline_name=segment.get('operating', {}).get('carrierCode', segment['carrierCode']),
                            departure_time=segment['departure']['at'],
                            arrival_time=segment['arrival']['at'],
                            duration=itinerary['duration'],
                            stops=len(itinerary['segments']) - 1,
                            price=float(offer['price']['total']),
                            currency=offer['price']['currency'],
                            fare_class=offer['travelerPricings'][0]['fareDetailsBySegment'][0]['cabin'],
                            departure_airport=segment['departure']['iataCode'],
                            arrival_airport=segment['arrival']['iataCode'],
                            aircraft_type=segment.get('aircraft', {}).get('code'),
                            booking_class=offer['travelerPricings'][0]['fareDetailsBySegment'][0]['class']
                        )
                        flights.append(flight)
            
            return FlightSearchResponse(
                flights=flights[:request.max_results],
                search_id=search_id,
                total_results=len(flights)
            )
            
        except ResponseError as error:
            # Fallback to demo data on API error
            print(f"Amadeus API error: {error}. Falling back to demo data.")
            return get_demo_flight_search_response(request.origin, request.destination)
        except Exception as error:
            print(f"Unexpected error: {error}. Falling back to demo data.")
            return get_demo_flight_search_response(request.origin, request.destination)
    
    async def get_flight_pricing(self, request: FlightPricingRequest) -> List[FlightPricingResponse]:
        if self.use_demo_data:
            return [get_demo_flight_pricing(flight_id) for flight_id in request.flight_ids]
        
        pricing_results = []
        
        for flight_id in request.flight_ids:
            try:
                # For now, fallback to demo pricing as flight pricing requires offer confirmation
                # In a production implementation, you would use flight-offers-pricing API
                pricing_results.append(get_demo_flight_pricing(flight_id))
            except Exception as error:
                print(f"Error getting pricing for flight {flight_id}: {error}")
                pricing_results.append(get_demo_flight_pricing(flight_id))
        
        return pricing_results