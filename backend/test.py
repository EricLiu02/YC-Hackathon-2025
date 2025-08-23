from amadeus import Client, ResponseError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Amadeus client with your API credentials
amadeus = Client(
    client_id=os.getenv('AMADEUS_API_KEY'),
    client_secret=os.getenv('AMADEUS_API_SECRET'),
    # hostname='test'  # Try production environment instead
)

try:
    # Try simpler API first - get airport info
    print("🔍 Testing airport lookup API...")
    response = amadeus.reference_data.locations.get(
        keyword='SFO',
        subType='AIRPORT'
    )
    print(f"✅ Airport API success! Found {len(response.data)} results")
    
    # Now try flight search
    print("\n🔍 Testing flight search API...")
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='SFO',
        destinationLocationCode='JFK',
        departureDate='2025-09-10',
        adults=1
    )
    print(f"✅ Flight search success! Found {len(response.data)} flight offers")
    for i, offer in enumerate(response.data[:3]):  # Show first 3 offers
        price = offer['price']['total']
        currency = offer['price']['currency']
        print(f"  Offer {i+1}: {price} {currency}")
        
except ResponseError as error:
    print(f"❌ ResponseError: {error}")
    print(f"   Status: {error.response.status_code}")
    print(f"   Body: {error.response.body}")
except Exception as error:
    print(f"❌ Unexpected error: {type(error).__name__}: {str(error)}")