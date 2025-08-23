import { DialogMessage } from "../types";

// Mock AI responses for manager conversation
export const generateManagerResponse = (
  userInput: string,
  stage: number
): string => {
  const responses: { [key: number]: string[] } = {
    0: [
      "That sounds wonderful! When would you like to travel?",
      "Excellent choice! What dates work best for you?",
      "I'd love to help you plan that! When are you thinking of going?",
    ],
    1: [
      "How many days are you planning to stay?",
      "Perfect! And how long would you like your trip to be?",
      "Great dates! How many nights will you be staying?",
    ],
    2: [
      "What's your budget for this trip?",
      "Let's talk budget - what range are you comfortable with?",
      "To help find the best options, what's your budget looking like?",
    ],
    3: [
      "Are you interested in any specific activities?",
      "What kind of experiences are you looking for?",
      "Any must-do activities on your list?",
    ],
    4: [
      "Great! Let me coordinate with my team to create the perfect itinerary for you.",
      "Wonderful! I'll have my specialists work on this right away.",
      "Perfect! My team will put together an amazing package for you.",
    ],
  };

  const stageResponses = responses[stage] || responses[0];
  return stageResponses[Math.floor(Math.random() * stageResponses.length)];
};

// Parse user input for travel details
export const parseUserInput = (
  input: string
): { destination?: string; dates?: string } => {
  const result: { destination?: string; dates?: string } = {};

  // Simple keyword extraction for destination
  const destinations = [
    "hawaii",
    "paris",
    "tokyo",
    "london",
    "rome",
    "bali",
    "dubai",
    "new york",
  ];
  const lowerInput = input.toLowerCase();

  for (const dest of destinations) {
    if (lowerInput.includes(dest)) {
      result.destination = dest.charAt(0).toUpperCase() + dest.slice(1);
      break;
    }
  }

  // Simple date pattern matching
  const datePattern =
    /(january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2}\/\d{1,2}|\d{1,2}-\d{1,2})/i;
  const dateMatch = input.match(datePattern);
  if (dateMatch) {
    result.dates = dateMatch[0];
  }

  return result;
};

// Generate random travel plan details
export const generateTravelPlan = (
  destination: string = "Hawaii"
): DialogMessage[] => {
  const hotels = [
    "Beachfront Resort & Spa",
    "Grand Palace Hotel",
    "Sunset Paradise Resort",
    "Ocean View Suites",
  ];

  const activities = [
    ["Snorkeling tour", "Sunset cruise", "Beach volleyball"],
    ["City tour", "Museum visits", "Local cuisine tasting"],
    ["Hiking adventure", "Waterfall exploration", "Zip-lining"],
    ["Spa day", "Shopping tour", "Cultural show"],
  ];

  const selectedHotel = hotels[Math.floor(Math.random() * hotels.length)];
  const selectedActivities =
    activities[Math.floor(Math.random() * activities.length)];
  const price = 1500 + Math.floor(Math.random() * 2000);

  return [
    {
      speaker: "Manager Mike",
      text: `I've got your perfect ${destination} vacation ready! Here's what we've prepared for you:`,
      isUser: false,
    },
    {
      speaker: "Manager Mike",
      text: `✈️ FLIGHT: Direct flight with premium airline, great departure times!`,
      isUser: false,
    },
    {
      speaker: "Manager Mike",
      text: `🏨 HOTEL: ${selectedHotel} - 5-star rated with amazing amenities!`,
      isUser: false,
    },
    {
      speaker: "Manager Mike",
      text: `💰 BUDGET: Total package $${price} - Incredible value with our exclusive deals!`,
      isUser: false,
    },
    {
      speaker: "Manager Mike",
      text: `🎭 ACTIVITIES: ${selectedActivities.join(", ")} and more!`,
      isUser: false,
    },
    {
      speaker: "Manager Mike",
      text: "Would you like to book this amazing trip?",
      isUser: false,
    },
  ];
};

// Type text effect helper
export const typeText = (
  text: string,
  onUpdate: (partial: string) => void,
  onComplete: () => void,
  speed: number = 50
): (() => void) => {
  let index = 0;
  const timer = setInterval(() => {
    if (index <= text.length) {
      onUpdate(text.substring(0, index));
      index++;
    } else {
      clearInterval(timer);
      onComplete();
    }
  }, speed);

  return () => clearInterval(timer);
};
