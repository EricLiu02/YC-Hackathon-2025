# Static Demo Fixtures

This directory contains deterministic JSON fixtures for powering demo mode while live APIs are work-in-progress.

## Files Overview

### Flights
- **`flights_SFO_JP.json`** - 5 flights from SFO to Japan (HND/NRT)
  - Mix of nonstop (3) and 1-stop (2) flights
  - Includes redeye options (late night/early morning arrivals)
  - Airlines: United, ANA, Delta, American, JAL
  - Prices range: $620-$1150 USD

### Hotels

#### Tokyo
- **`hotels_Tokyo.json`** - 5 diverse Tokyo accommodations
  - Asakusa River Boutique (boutique near transit) - $140-$220
  - Shibuya Business Tower (modern business) - $180-$280
  - Ginza Imperial Suite (luxury shopping district) - $320-$480
  - Shinjuku Capsule Plus (modern capsule experience) - $45-$75
  - Ueno Garden Ryokan (traditional Japanese experience) - $160-$240

#### Kyoto
- **`hotels_Kyoto.json`** - 5 diverse Kyoto accommodations
  - Gion Traditional Ryokan (traditional ryokan) - $280-$450
  - Arashiyama Bamboo Lodge (boutique near bamboo forest) - $180-$280
  - Kyoto Station Business Hotel (modern business) - $90-$140
  - Kiyomizu Temple Inn (boutique near temples) - $160-$250
  - Philosopher's Path Luxury Suite (luxury cultural experience) - $450-$680

### Activities

#### Tokyo
- **`activities_Tokyo.json`** - 10 diverse Tokyo experiences
  - Food: Tsukiji Market tour, Robot Restaurant
  - Culture: National Museum, Harajuku fashion, Meiji Shrine
  - Tech: Akihabara electronics district
  - Nature: Imperial Gardens, Sumida River cruise
  - Day trips: Kamakura
  - Coffee: Shibuya coffee culture walk

#### Kyoto
- **`activities_Kyoto.json`** - 10 diverse Kyoto experiences
  - Temples: Higashiyama walk, Fushimi Inari, Golden Pavilion
  - Culture: Tea ceremony, Gion district, Nijo Castle
  - Food: Kaiseki dining, Buddhist vegetarian cuisine
  - Nature: Bamboo grove, Philosopher's Path
  - Spiritual: Various temple and shrine visits

## Data Characteristics

### Deterministic Design
- All prices, times, and ratings are hand-picked (no randomness)
- Consistent data structure matching raw agent schemas
- Realistic but static data for reliable testing

### Coverage Requirements Met
- ✅ Nonstop and 1-stop flights
- ✅ Redeye flight options
- ✅ Diverse hotel vibes and price ranges
- ✅ Traditional ryokan options in Kyoto
- ✅ Rich activity themes (food, culture, temples, nature)
- ✅ Multiple images per hotel
- ✅ Transit accessibility information

### Schema Compatibility
- Flights: Match `FlightOptionRaw` schema
- Hotels: Match `HotelRaw` schema with demo extensions (`vibe`, `near_transit_min`)
- Activities: Custom schema for activity planning

## Validation

Run the validation script to ensure all fixtures are valid:

```bash
cd backend
python scripts/validate_fixtures.py
```

The validator checks:
- **Flights**: Array length (5), required fields, currency=USD, stops∈{0,1}, flight type diversity
- **Hotels**: Array length (5), star ratings (3-5), ≥2 images, transit info, vibe diversity
- **Activities**: Array length (10), non-empty themes, duration>0, theme diversity

## Usage in Demo Mode

When `demo: true` is set in the system:
1. Load fixtures instead of calling live APIs
2. Return deterministic, consistent results
3. Enable offline development and testing
4. Provide stable data for PDF/ICS generation

## Future Extensions

- Add seasonal variations (cherry blossom, autumn leaves)
- Include accessibility information
- Add pricing tiers and package deals
- Expand to other Japanese cities (Osaka, Hiroshima)
- Add multi-day itinerary templates
