import os
import requests
from typing import List, Optional
from datetime import date, datetime
from dotenv import load_dotenv

from .models import FlightSearchRequest, FlightSearchResponse, FlightOption, FlightPricingRequest, FlightPricingResponse, FlightCalendarRequest, FlightCalendarResponse, CalendarPrice

load_dotenv()


class SearchAPIFlightClient:
    def __init__(self):
        api_key = os.getenv('SEARCHAPI_KEY')
        
        if not api_key:
            raise ValueError("SearchAPI key not found. Set SEARCHAPI_KEY environment variable.")
        
        self.api_key = api_key
        self.base_url = "https://www.searchapi.io/api/v1/search"
    
    async def search_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        # First try Google Flights API
        try:
            response = await self._search_google_flights(request)
            
            # If no flights found, try Google Travel Explore API as fallback
            if not response.flights:
                print("No flights found with Google Flights API, trying Travel Explore API as fallback...")
                response = await self._search_travel_explore(request)
            
            return response
            
        except Exception as google_flights_error:
            print(f"Google Flights API failed: {google_flights_error}")
            print("Trying Travel Explore API as fallback...")
            
            # If Google Flights API fails completely, try Travel Explore as fallback
            try:
                response = await self._search_travel_explore(request)
                return response
            except Exception as travel_explore_error:
                # If both APIs fail, raise a combined error
                raise Exception(f"Both APIs failed - Google Flights: {google_flights_error}, Travel Explore: {travel_explore_error}")
    
    async def _search_google_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        try:
            # Build SearchAPI parameters for Google Flights
            params = {
                'engine': 'google_flights',
                'api_key': self.api_key,
                'departure_id': request.origin,
                'arrival_id': request.destination,
                'outbound_date': request.departure_date.isoformat(),
                'adults': str(request.adults),
                'currency': 'USD',
                'hl': 'en'
            }
            
            # Add optional parameters
            if request.children > 0:
                params['children'] = str(request.children)
            if request.infants > 0:
                params['infants'] = str(request.infants)
            if request.travel_class:
                params['travel_class'] = str(request.travel_class).lower()
            
            if request.return_date:
                params['return_date'] = request.return_date.isoformat()
                params['type'] = '2'  # Round trip
            else:
                # For one-way flights, SearchAPI still requires return_date
                # Use the same date as departure for one-way flights
                params['return_date'] = request.departure_date.isoformat()
                params['type'] = '1'  # One way
            
            print(f"Making SearchAPI call with params: {params}")
            
            # Make the API call
            response = requests.get(self.base_url, params=params)
            
            # Debug response
            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response text: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"API call successful, received response")
            
            # Parse the SearchAPI response
            flights = []
            search_id = f"searchapi_search_{request.origin}_{request.destination}_{request.departure_date}"
            
            # Extract flights from SearchAPI response
            best_flights = data.get('best_flights', [])
            other_flights = data.get('other_flights', [])
            all_flights = best_flights + other_flights
            
            for flight_data in all_flights[:request.max_results]:
                # Parse flight details from SearchAPI format
                flights_info = flight_data.get('flights', [])
                if not flights_info:
                    continue
                
                first_flight = flights_info[0]
                last_flight = flights_info[-1]
                
                # Extract departure and arrival times
                departure_airport = first_flight.get('departure_airport', {}).get('id', request.origin)
                arrival_airport = last_flight.get('arrival_airport', {}).get('id', request.destination)
                
                # Parse datetime strings
                departure_time_str = first_flight.get('departure_airport', {}).get('time')
                arrival_time_str = last_flight.get('arrival_airport', {}).get('time')
                
                # Convert to datetime objects (SearchAPI format may vary)
                try:
                    departure_time = datetime.fromisoformat(departure_time_str) if departure_time_str else datetime.now()
                    arrival_time = datetime.fromisoformat(arrival_time_str) if arrival_time_str else datetime.now()
                except:
                    # Fallback if datetime parsing fails
                    departure_time = datetime.now()
                    arrival_time = datetime.now()
                
                # Get price info
                price_info = flight_data.get('price', 0)
                if isinstance(price_info, dict):
                    price = float(price_info.get('value', 0))
                else:
                    price = float(price_info)
                
                # Calculate stops
                stops = len(flights_info) - 1
                
                # Get airline info
                airline_name = first_flight.get('airline', 'Unknown')
                flight_number = first_flight.get('flight_number', '')
                
                # Convert duration to string format
                duration_val = flight_data.get('total_duration', '')
                if isinstance(duration_val, (int, float)):
                    duration_str = f"{duration_val}m"  # Convert minutes to string
                else:
                    duration_str = str(duration_val) if duration_val else ''
                
                flight = FlightOption(
                    flight_id=f"searchapi_{flight_number}_{departure_airport}_{arrival_airport}_{request.departure_date}",
                    airline_code=airline_name[:2] if airline_name else 'XX',
                    airline_name=airline_name,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    duration=duration_str,
                    stops=stops,
                    price=price,
                    currency='USD',  # SearchAPI typically returns USD
                    fare_class=request.travel_class or 'Economy',
                    departure_airport=departure_airport,
                    arrival_airport=arrival_airport,
                    aircraft_type='',  # Not always available in SearchAPI
                    booking_class=request.travel_class[0] if request.travel_class else 'Y'
                )
                flights.append(flight)
            
            return FlightSearchResponse(
                flights=flights,
                search_id=search_id,
                total_results=len(flights)
            )
            
        except requests.exceptions.RequestException as error:
            raise Exception(f"Google Flights API request error: {error}")
        except Exception as error:
            raise Exception(f"Google Flights API error: {type(error).__name__}: {str(error)}")
    
    async def _search_travel_explore(self, request: FlightSearchRequest) -> FlightSearchResponse:
        """Fallback to Google Travel Explore API when Google Flights returns no results"""
        try:
            # Build SearchAPI parameters for Google Travel Explore
            params = {
                'engine': 'google_travel_explore',
                'api_key': self.api_key,
                'travel_type': 'flights',
                'departure_id': request.origin,  # Use departure_id instead of 'from'
                'currency': 'USD',
                'hl': 'en-US'  # Travel Explore requires full locale
            }
            
            print(f"Making Travel Explore API call with params: {params}")
            
            # Make the API call
            response = requests.get(self.base_url, params=params)
            
            # Debug response
            print(f"Travel Explore response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Travel Explore response text: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"Travel Explore API call successful")
            
            # Parse the Travel Explore response
            flights = []
            search_id = f"searchapi_explore_{request.origin}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract travel destinations from Travel Explore
            destinations = data.get('destinations', [])
            
            for dest_data in destinations[:request.max_results]:
                # Extract destination info from Travel Explore response
                destination_name = dest_data.get('name', '')
                destination_code = dest_data.get('primary_airport', '')
                
                # Skip if this doesn't match our requested destination (if we have one)
                if request.destination and destination_code != request.destination:
                    continue
                
                # Get flight info from nested flight object
                flight_info = dest_data.get('flight', {})
                if not flight_info:
                    continue  # Skip destinations without flight info
                
                price = float(flight_info.get('price', 0))
                stops = flight_info.get('stops', 0)
                duration = flight_info.get('flight_duration', '6h')
                airline_name = flight_info.get('airline_name', 'Various Airlines')
                airline_code = flight_info.get('airline_code', 'XX')
                
                # Use outbound/return dates if available
                outbound_date_str = dest_data.get('outbound_date', request.departure_date.isoformat())
                try:
                    outbound_date = datetime.strptime(outbound_date_str, '%Y-%m-%d').date()
                except:
                    outbound_date = request.departure_date
                
                # Create a flight option from the travel explore data
                flight = FlightOption(
                    flight_id=f"explore_{request.origin}_{destination_code}_{outbound_date}",
                    airline_code=airline_code,
                    airline_name=airline_name,
                    departure_time=datetime.combine(outbound_date, datetime.min.time().replace(hour=12)),  # Default to noon
                    arrival_time=datetime.combine(outbound_date, datetime.min.time().replace(hour=18)),   # Estimate based on duration
                    duration=duration,
                    stops=stops,
                    price=price,
                    currency='USD',
                    fare_class=request.travel_class or 'Economy',
                    departure_airport=request.origin,
                    arrival_airport=destination_code,
                    aircraft_type='',
                    booking_class=request.travel_class[0] if request.travel_class else 'Y'
                )
                flights.append(flight)
            
            return FlightSearchResponse(
                flights=flights,
                search_id=search_id,
                total_results=len(flights)
            )
            
        except requests.exceptions.RequestException as error:
            raise Exception(f"Travel Explore API request error: {error}")
        except Exception as error:
            raise Exception(f"Travel Explore API error: {type(error).__name__}: {str(error)}")
    
    async def get_flight_pricing(self, request: FlightPricingRequest) -> List[FlightPricingResponse]:
        # SearchAPI returns pricing information in the search results
        # This endpoint would need to be implemented based on specific requirements
        raise NotImplementedError("Flight pricing API not yet implemented for SearchAPI. Use flight search results for pricing.")
    
    async def search_flight_calendar(self, request: FlightCalendarRequest) -> FlightCalendarResponse:
        """Search for flight prices across different dates using Google Flights Calendar API"""
        try:
            # Build SearchAPI parameters for Google Flights Calendar
            params = {
                'engine': 'google_flights_calendar',
                'api_key': self.api_key,
                'departure_id': request.origin,
                'arrival_id': request.destination,
                'outbound_date': request.departure_date.isoformat(),
                'adults': str(request.adults),
                'currency': 'USD',
                'hl': 'en'
            }
            
            # Add optional parameters
            if request.children > 0:
                params['children'] = str(request.children)
            if request.infants > 0:
                params['infants'] = str(request.infants)
            if request.travel_class:
                params['travel_class'] = str(request.travel_class).lower()
            
            if request.return_date:
                params['return_date'] = request.return_date.isoformat()
                params['type'] = '2'  # Round trip
            else:
                # For one-way flights, SearchAPI still requires return_date
                # Use the same date as departure for one-way flights
                params['return_date'] = request.departure_date.isoformat()
                params['type'] = '1'  # One way
            
            print(f"Making Google Flights Calendar API call with params: {params}")
            
            # Make the API call
            response = requests.get(self.base_url, params=params)
            
            # Debug response
            print(f"Calendar response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Calendar response text: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"Calendar API call successful")
            
            # Parse the Calendar response
            calendar_prices = []
            search_id = f"searchapi_calendar_{request.origin}_{request.destination}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract calendar data - SearchAPI returns calendar as an array
            calendar_entries = data.get('calendar', [])
            
            for entry in calendar_entries:
                try:
                    # Skip entries without flights
                    if entry.get('has_no_flights'):
                        continue
                    
                    # For one-way flights, use departure date; for round-trip, could use either
                    # Let's use departure date for consistency
                    date_str = entry.get('departure', '')
                    price = float(entry.get('price', 0))
                    
                    if price > 0 and date_str:
                        calendar_price = CalendarPrice(
                            date=date_str,
                            price=price,
                            currency='USD'
                        )
                        calendar_prices.append(calendar_price)
                        
                except (ValueError, TypeError):
                    continue  # Skip invalid price data
            
            # Sort by date
            calendar_prices.sort(key=lambda x: x.date)
            
            return FlightCalendarResponse(
                origin=request.origin,
                destination=request.destination,
                calendar_prices=calendar_prices,
                search_id=search_id
            )
            
        except requests.exceptions.RequestException as error:
            raise Exception(f"Google Flights Calendar API request error: {error}")
        except Exception as error:
            raise Exception(f"Google Flights Calendar API error: {type(error).__name__}: {str(error)}")