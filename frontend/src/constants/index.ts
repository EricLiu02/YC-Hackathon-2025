import { Character, Room } from "../types";

// Pixel size for 8-bit aesthetic
export const PIXEL_SIZE = 4;

// Office dimensions - optimized for viewport
export const OFFICE_WIDTH = 1200;
export const OFFICE_HEIGHT = 650;

// Character size
export const CHARACTER_SIZE = 32;

// Movement speed
export const MOVEMENT_SPEED = 2;

// Dialog timing
export const DIALOG_SPEED = 50; // ms per character
export const THOUGHT_BUBBLE_DURATION = 3000; // ms

// Office layout - compact centered grid
export const OFFICE_LAYOUT: Room[] = [
  {
    id: "manager-office",
    type: "manager",
    position: { x: 400, y: 40 },
    width: 400,
    height: 140,
    decorations: [
      { type: "desk", position: { x: 180, y: 60 } },
      { type: "computer", position: { x: 190, y: 55 } },
      { type: "plant", position: { x: 40, y: 20 } },
      { type: "plant", position: { x: 340, y: 20 } },
    ],
  },
  {
    id: "hotel-office",
    type: "hotel",
    position: { x: 50, y: 210 },
    width: 320,
    height: 160,
    decorations: [
      { type: "hotel", position: { x: 250, y: 20 } },
      { type: "desk", position: { x: 130, y: 80 } },
      { type: "computer", position: { x: 140, y: 75 } },
      { type: "plant", position: { x: 40, y: 30 } },
    ],
  },
  {
    id: "lobby",
    type: "lobby",
    position: { x: 400, y: 210 },
    width: 400,
    height: 160,
    decorations: [
      { type: "plant", position: { x: 20, y: 20 } },
      { type: "plant", position: { x: 360, y: 20 } },
      { type: "plant", position: { x: 20, y: 120 } },
      { type: "plant", position: { x: 360, y: 120 } },
      { type: "desk", position: { x: 180, y: 110 } },
      { type: "computer", position: { x: 190, y: 105 } },
    ],
  },
  {
    id: "flight-office",
    type: "flight",
    position: { x: 830, y: 210 },
    width: 320,
    height: 160,
    decorations: [
      { type: "plane", position: { x: 250, y: 20 } },
      { type: "desk", position: { x: 130, y: 80 } },
      { type: "computer", position: { x: 140, y: 75 } },
      { type: "plant", position: { x: 40, y: 30 } },
    ],
  },
  {
    id: "budget-office",
    type: "budget",
    position: { x: 50, y: 400 },
    width: 320,
    height: 160,
    decorations: [
      { type: "money", position: { x: 250, y: 20 } },
      { type: "desk", position: { x: 130, y: 80 } },
      { type: "computer", position: { x: 140, y: 75 } },
      { type: "plant", position: { x: 40, y: 30 } },
    ],
  },
  {
    id: "activities-office",
    type: "activities",
    position: { x: 830, y: 400 },
    width: 320,
    height: 160,
    decorations: [
      { type: "activity", position: { x: 250, y: 20 } },
      { type: "desk", position: { x: 130, y: 80 } },
      { type: "computer", position: { x: 140, y: 75 } },
      { type: "plant", position: { x: 40, y: 30 } },
    ],
  },
];

// Initial characters - positioned for flexbox layout
export const INITIAL_CHARACTERS: Character[] = [
  {
    id: "manager",
    type: "manager",
    name: "Manager Mike",
    position: { x: 600, y: 100 }, // Center of manager office
    isMoving: false,
  },
  {
    id: "hotel-agent",
    type: "hotel",
    name: "Holly Hotel",
    position: { x: 250, y: 280 }, // Center of hotel office
    isMoving: false,
  },
  {
    id: "flight-agent",
    type: "flight",
    name: "Freddy Flights",
    position: { x: 1010, y: 280 }, // Center of flight office
    isMoving: false,
  },
  {
    id: "budget-agent",
    type: "budget",
    name: "Betty Budget",
    position: { x: 250, y: 450 }, // Center of budget office
    isMoving: false,
  },
  {
    id: "activities-agent",
    type: "activities",
    name: "Andy Activities",
    position: { x: 1010, y: 450 }, // Center of activities office
    isMoving: false,
  },
];

// Sample thoughts for planning stage
export const AGENT_THOUGHTS = {
  hotel: [
    "Looking for the best hotels...",
    "Checking availability...",
    "Found a great deal!",
    "This place has amazing reviews!",
    "5-star options available!",
    "Breakfast included!",
  ],
  flight: [
    "Searching for flights...",
    "Comparing prices...",
    "Direct flight available!",
    "Window seat secured!",
    "Great departure times!",
    "Extra legroom seats!",
  ],
  budget: [
    "Calculating costs...",
    "Optimizing the budget...",
    "Found some savings!",
    "Great value for money!",
    "Within budget perfectly!",
    "Discount codes applied!",
  ],
  activities: [
    "Finding fun activities...",
    "Restaurant reservations...",
    "Local attractions mapped!",
    "This will be amazing!",
    "Tours booked!",
    "Special events found!",
  ],
  manager: [
    "Coordinating the team...",
    "Everything coming together!",
    "Quality check time...",
    "Almost ready!",
    "Looking good!",
    "Team's doing great!",
  ],
};

// Idle conversation topics
export const IDLE_THOUGHTS = {
  hotel: [
    "Need coffee...",
    "Checking emails...",
    "New hotel opened!",
    "Review update...",
  ],
  flight: [
    "Flight delayed...",
    "New route available!",
    "Fuel prices up...",
    "System maintenance...",
  ],
  budget: [
    "Numbers look good!",
    "Quarterly report...",
    "Exchange rates...",
    "Budget review time...",
  ],
  activities: [
    "Cool new restaurant!",
    "Event this weekend...",
    "Tour guide called...",
    "Weather looks nice!",
  ],
  manager: [
    "Team meeting soon...",
    "Good morning all!",
    "Keep up the work!",
    "Coffee time!",
  ],
};
