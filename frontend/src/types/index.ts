// Character types
export type CharacterType =
  | "manager"
  | "hotel"
  | "flight"
  | "budget"
  | "activities";

export interface Position {
  x: number;
  y: number;
}

export interface Character {
  id: string;
  type: CharacterType;
  name: string;
  position: Position;
  targetPosition?: Position;
  isMoving: boolean;
  currentThought?: string;
}

// Game stages
export type GameStage = "intro" | "planning" | "final" | "idle";

export interface DialogMessage {
  speaker: string;
  text: string;
  isUser?: boolean;
  characterType?: string; // For showing character avatar
}

export interface TravelPlan {
  destination?: string;
  dates?: {
    start?: string;
    end?: string;
  };
  budget?: number;
  activities?: string[];
  hotel?: string;
  flight?: string;
}

// Office layout
export interface Room {
  id: string;
  type: CharacterType | "lobby";
  position: Position;
  width: number;
  height: number;
  decorations?: Decoration[];
}

export interface Decoration {
  type:
    | "plane"
    | "hotel"
    | "money"
    | "activity"
    | "desk"
    | "plant"
    | "computer";
  position: Position;
}
