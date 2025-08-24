import os
import requests
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LocationInfo:
    """Enriched location information from Perplexity research"""
    city: str
    country: str
    country_code: str
    coordinates: Optional[tuple[float, float]] = None  # (lat, lng)
    bounding_box: Optional[list[float]] = None  # [min_lng, min_lat, max_lng, max_lat]
    timezone: Optional[str] = None
    currency: Optional[str] = None
    popular_areas: list[str] = None
    tourist_season: Optional[str] = None
    
    def __post_init__(self):
        if self.popular_areas is None:
            self.popular_areas = []


class PerplexityLocationEnricher:
    """Uses Perplexity Sonar to research and enrich location information"""
    
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def enrich_location(self, user_query: str) -> LocationInfo:
        """
        Research location information using Perplexity Sonar
        
        Args:
            user_query: User's location request (e.g., "hotels in Paris", "New York City hotels")
        
        Returns:
            LocationInfo with enriched data
        """
        
        research_prompt = f"""
        Research the following location query for hotel booking: "{user_query}"
        
        Please provide the following information in a structured format:
        1. Primary city name (standardized)
        2. Country name and ISO country code (2-letter)
        3. Latitude and longitude coordinates (decimal format)
        4. Bounding box coordinates for the city area [min_longitude, min_latitude, max_longitude, max_latitude]
        5. Timezone (IANA format like "America/New_York")
        6. Local currency code (ISO 3-letter like "USD", "EUR")
        7. Popular hotel areas/districts in the city (2-4 areas)
        8. Current tourist season (high/low/shoulder)
        
        Format your response as JSON with these exact keys:
        {{
            "city": "standardized city name",
            "country": "full country name", 
            "country_code": "2-letter ISO code",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "bounding_box": [-74.2591, 40.4774, -73.7004, 40.9176],
            "timezone": "America/New_York",
            "currency": "USD",
            "popular_areas": ["Manhattan", "Brooklyn", "Queens"],
            "tourist_season": "high"
        }}
        
        Only return the JSON object, no additional text.
        """
        
        try:
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "user",
                        "content": research_prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content'].strip()
            
            # Parse JSON response
            try:
                location_data = json.loads(content)
                
                return LocationInfo(
                    city=location_data.get('city', ''),
                    country=location_data.get('country', ''),
                    country_code=location_data.get('country_code', 'US'),
                    coordinates=(location_data.get('latitude'), location_data.get('longitude')),
                    bounding_box=location_data.get('bounding_box'),
                    timezone=location_data.get('timezone'),
                    currency=location_data.get('currency', 'USD'),
                    popular_areas=location_data.get('popular_areas', []),
                    tourist_season=location_data.get('tourist_season')
                )
                
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                return self._parse_fallback_response(user_query, content)
                
        except Exception as e:
            print(f"Perplexity API error: {e}")
            # Return basic location info based on user query
            return self._create_fallback_location(user_query)
    
    def _parse_fallback_response(self, user_query: str, content: str) -> LocationInfo:
        """Parse non-JSON response as fallback"""
        # Extract city name from user query as fallback
        city = user_query.replace("hotels in ", "").replace("hotel in ", "").strip()
        
        return LocationInfo(
            city=city,
            country="United States",
            country_code="US",
            currency="USD"
        )
    
    def _create_fallback_location(self, user_query: str) -> LocationInfo:
        """Create basic location info when API fails"""
        city = user_query.replace("hotels in ", "").replace("hotel in ", "").strip()
        
        # Basic fallbacks for common cities
        fallbacks = {
            "new york": LocationInfo("New York", "United States", "US", (40.7128, -74.0060), 
                                   [-74.2591, 40.4774, -73.7004, 40.9176], "America/New_York", "USD",
                                   ["Manhattan", "Brooklyn", "Queens"], "high"),
            "paris": LocationInfo("Paris", "France", "FR", (48.8566, 2.3522),
                                [-2.4699, 48.8155, 2.4699, 48.9021], "Europe/Paris", "EUR",
                                ["1st Arrondissement", "Champs-Élysées", "Montmartre"], "high"),
            "london": LocationInfo("London", "United Kingdom", "GB", (51.5074, -0.1278),
                                 [-0.3517, 51.3850, 0.1276, 51.6723], "Europe/London", "GBP",
                                 ["Westminster", "Covent Garden", "South Bank"], "high")
        }
        
        city_lower = city.lower()
        return fallbacks.get(city_lower, LocationInfo(city, "United States", "US", currency="USD"))