# scripts/validate_fixtures.py
from __future__ import annotations
import json, sys, pathlib
from typing import Optional, List
from pydantic import BaseModel, ValidationError, Field

ROOT = pathlib.Path(__file__).resolve().parents[1]
FX = ROOT / "services" / "agents" / "fixtures"

# Try to import raw models; fallback to local light models
try:
    from services.agents.schemas import FlightOptionRaw as _FlightRaw
    from services.agents.schemas import HotelRaw as _HotelRaw
except Exception:
    class _FlightRaw(BaseModel):
        flight_id: str
        airline_code: str
        airline_name: str
        departure_time: str
        arrival_time: str
        duration: str
        stops: int
        price: float
        currency: str
        fare_class: str
        departure_airport: str
        arrival_airport: str

    class _HotelLoc(BaseModel):
        address: Optional[str] = None
        latitude: Optional[float] = None
        longitude: Optional[float] = None
        
    class _HotelReview(BaseModel):
        rating: Optional[float] = None
        total_reviews: Optional[int] = None
        source: Optional[str] = None
        
    class _HotelRaw(BaseModel):
        hotel_id: str
        name: str
        city: str
        location: _HotelLoc
        star_rating: Optional[int] = None
        review: Optional[_HotelReview] = None
        amenities: List[dict] = []
        images: List[str] = []
        rooms: List[dict] = []
        price_range: Optional[str] = None
        vibe: Optional[str] = None
        near_transit_min: Optional[int] = None

class _Activity(BaseModel):
    id: str
    name: str
    city: str
    theme: List[str]
    price_usd: float
    duration_hr: float
    image: str

def _load(path: pathlib.Path):
    with path.open() as f:
        return json.load(f)

def _ok(msg): print(f"✅ {msg}")
def _bad(msg): print(f"❌ {msg}")

def validate_flights():
    p = FX / "flights_SFO_JP.json"
    data = _load(p)
    assert isinstance(data, list) and len(data) == 5, "flights array must have length 5"
    
    # Check for required flight types
    nonstop_count = sum(1 for item in data if item.get("stops") == 0)
    onestop_count = sum(1 for item in data if item.get("stops") == 1)
    redeye_count = 0
    
    for i, item in enumerate(data):
        try:
            obj = _FlightRaw(**item)
        except ValidationError as e:
            _bad(f"{p.name}[{i}] schema error: {e}")
            raise
        assert obj.currency == "USD", "currency must be USD"
        assert obj.stops in (0,1), "stops must be 0 or 1"
        
        # Check for redeye (late night departure or early morning arrival next day)
        from datetime import datetime
        try:
            dep_time = datetime.fromisoformat(obj.departure_time.replace('Z', '+00:00'))
            arr_time = datetime.fromisoformat(obj.arrival_time.replace('Z', '+00:00'))
            dep_hour = dep_time.hour
            arr_day_diff = (arr_time.date() - dep_time.date()).days
            if (22 <= dep_hour or dep_hour <= 2) or (arr_day_diff >= 1 and arr_time.hour < 8):
                redeye_count += 1
        except:
            pass
    
    assert nonstop_count >= 1, "Must have at least one nonstop flight"
    assert onestop_count >= 1, "Must have at least one 1-stop flight"
    assert redeye_count >= 1, "Must have at least one redeye flight"
    
    _ok(f"{p.name} validated ({len(data)} items, {nonstop_count} nonstop, {onestop_count} 1-stop, {redeye_count} redeye)")

def validate_hotels(name):
    p = FX / name
    data = _load(p)
    assert isinstance(data, list) and len(data) == 5, f"{name} must have 5 items"
    
    vibes = set()
    for i, item in enumerate(data):
        obj = _HotelRaw(**item)
        assert obj.star_rating is None or 3 <= obj.star_rating <= 5, "star_rating 3..5"
        assert obj.near_transit_min is not None, "near_transit_min required"
        assert len(obj.images) >= 2, "need at least 2 images"
        if obj.vibe:
            vibes.add(obj.vibe)
    
    # Check for diverse vibes
    if "kyoto" in name.lower():
        assert any("ryokan" in vibe.lower() or "traditional" in vibe.lower() for vibe in vibes), "Kyoto should have traditional ryokan"
    
    _ok(f"{p.name} validated ({len(data)} items, vibes: {', '.join(sorted(vibes))})")

def validate_activities(name):
    p = FX / name
    data = _load(p)
    assert isinstance(data, list) and len(data) == 10, f"{name} must have 10 items"
    
    themes = set()
    for i, item in enumerate(data):
        obj = _Activity(**item)
        assert len(obj.theme) >= 1, "theme required"
        assert obj.duration_hr > 0, "duration_hr must be >0"
        themes.update(obj.theme)
    
    # Check for diverse themes
    if "tokyo" in name.lower():
        assert "food" in themes, "Tokyo should have food activities"
        assert any(t in themes for t in ["museum", "park", "nature"]), "Tokyo should have cultural/nature activities"
    elif "kyoto" in name.lower():
        assert "temple" in themes, "Kyoto should have temple activities"
        assert "culture" in themes, "Kyoto should have cultural activities"
    
    _ok(f"{p.name} validated ({len(data)} items, themes: {', '.join(sorted(themes))})")

if __name__ == "__main__":
    try:
        print("🚀 Validating fixtures...\n")
        
        validate_flights()
        validate_hotels("hotels_Tokyo.json")
        validate_hotels("hotels_Kyoto.json")
        validate_activities("activities_Tokyo.json")
        validate_activities("activities_Kyoto.json")
        
        print("\n" + "="*50)
        _ok("All fixtures OK")
        print("="*50)
        sys.exit(0)
    except Exception as e:
        _bad(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
