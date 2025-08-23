import os
import logging
from typing import List, Optional
from datetime import date, datetime
from amadeus import Client, ResponseError
from dotenv import load_dotenv

from .models import FlightSearchRequest, FlightSearchResponse, FlightOption, FlightPricingRequest, FlightPricingResponse, PriceBreakdown

load_dotenv()


class AmadeusFlightClient:
    def __init__(self):
        api_key = os.getenv('AMADEUS_API_KEY')
        api_secret = os.getenv('AMADEUS_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("Amadeus API credentials not found. Set AMADEUS_API_KEY and AMADEUS_API_SECRET environment variables.")
        
        self.amadeus = Client(
            client_id=api_key,
            client_secret=api_secret,
            hostname='test',  # Start with test environment for development
            log_level='debug'  # Enable debug logging
        )
    
    async def search_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        try:
            # Build the search parameters according to Amadeus API spec
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
            print(f"Making Amadeus API call with params: {params}")
            response = self.amadeus.shopping.flight_offers_search.get(**params)
            print(f"API call successful, received {len(response.data)} offers")
            
            # Parse the response
            flights = []
            search_id = f"amadeus_search_{request.origin}_{request.destination}_{request.departure_date}"
            
            for offer in response.data:
                # Each offer represents a complete flight option (one-way or round-trip)
                itinerary = offer['itineraries'][0]  # Take first itinerary (outbound)
                
                # Get the first and last segments for overall journey info
                first_segment = itinerary['segments'][0]
                last_segment = itinerary['segments'][-1]
                
                # Parse datetime strings to datetime objects
                departure_time = datetime.fromisoformat(first_segment['departure']['at'].replace('Z', '+00:00'))
                arrival_time = datetime.fromisoformat(last_segment['arrival']['at'].replace('Z', '+00:00'))
                
                # Get airline info from operating carrier or marketing carrier
                operating_carrier = first_segment.get('operating', {})
                carrier_code = operating_carrier.get('carrierCode', first_segment['carrierCode'])
                
                flight = FlightOption(
                    flight_id=f"{offer['id']}_{first_segment['departure']['at'][:10]}",
                    airline_code=carrier_code,
                    airline_name=carrier_code,  # Would need airline name mapping for full names
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    duration=itinerary['duration'],
                    stops=len(itinerary['segments']) - 1,
                    price=float(offer['price']['total']),
                    currency=offer['price']['currency'],
                    fare_class=offer['travelerPricings'][0]['fareDetailsBySegment'][0]['cabin'],
                    departure_airport=first_segment['departure']['iataCode'],
                    arrival_airport=last_segment['arrival']['iataCode'],
                    aircraft_type=first_segment.get('aircraft', {}).get('code', ''),
                    booking_class=offer['travelerPricings'][0]['fareDetailsBySegment'][0]['class']
                )
                flights.append(flight)
            
            return FlightSearchResponse(
                flights=flights[:request.max_results],
                search_id=search_id,
                total_results=len(flights)
            )
            
        except ResponseError as error:
            print(f"Amadeus ResponseError - Status: {error.response.status_code}, Body: {error.response.body}")
            raise Exception(f"Amadeus API error: Status {error.response.status_code} - {error.response.body}")
        except Exception as error:
            print(f"Unexpected error type: {type(error).__name__}, message: {str(error)}")
            raise Exception(f"Unexpected error: {type(error).__name__}: {str(error)}")
    
    async def get_flight_pricing(self, request: FlightPricingRequest) -> List[FlightPricingResponse]:
        # TODO: Implement real Amadeus flight-offers-pricing API
        # For now, this would require implementing offer confirmation flow
        raise NotImplementedError("Flight pricing API not yet implemented. Use flight search results for pricing.")