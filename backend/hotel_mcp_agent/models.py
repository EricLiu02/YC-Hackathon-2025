from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum


class HotelSearchRequest(BaseModel):
    city: str
    check_in_date: date
    check_out_date: date
    adults: int = 2
    children: int = 0
    rooms: int = 1
    hotel_class: Optional[str] = None  # "3", "4", "5" star rating
    max_price: Optional[float] = None
    amenities: Optional[List[str]] = None  # ["wifi", "pool", "gym", "spa"]
    sort_by: Optional[str] = "price"  # "price", "rating", "distance"
    max_results: int = 10


class HotelAmenity(BaseModel):
    name: str
    available: bool = True


class HotelLocation(BaseModel):
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_to_center: Optional[str] = None


class HotelReview(BaseModel):
    rating: float
    total_reviews: int
    source: Optional[str] = "Google"


class RoomType(BaseModel):
    room_id: str
    room_name: str
    description: Optional[str] = None
    max_occupancy: int
    bed_info: Optional[str] = None
    price_per_night: float
    total_price: float
    currency: str = "USD"
    cancellation_policy: Optional[str] = None
    breakfast_included: bool = False


class Hotel(BaseModel):
    hotel_id: str
    name: str
    location: HotelLocation
    star_rating: Optional[int] = None
    review: Optional[HotelReview] = None
    amenities: List[HotelAmenity] = []
    images: List[str] = []
    description: Optional[str] = None
    rooms: List[RoomType] = []
    price_range: Optional[str] = None


class HotelSearchResponse(BaseModel):
    hotels: List[Hotel]
    search_id: str
    total_results: int
    city: str
    check_in_date: date
    check_out_date: date


class HotelPricingRequest(BaseModel):
    hotel_id: str
    room_type: Optional[str] = None
    check_in_date: date
    check_out_date: date
    adults: int = 2
    children: int = 0
    rooms: int = 1


class PricingDetails(BaseModel):
    base_price: float
    taxes_and_fees: float
    total_price: float
    currency: str = "USD"
    price_per_night: float
    total_nights: int


class CancellationPolicy(BaseModel):
    is_refundable: bool
    cancellation_deadline: Optional[date] = None
    penalty_amount: Optional[float] = None
    policy_description: str


class HotelPricingResponse(BaseModel):
    hotel_id: str
    hotel_name: str
    room_type: str
    pricing: PricingDetails
    cancellation_policy: CancellationPolicy
    booking_conditions: Optional[List[str]] = None
    last_updated: Optional[str] = None