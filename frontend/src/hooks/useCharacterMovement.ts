import { useState, useEffect, useCallback } from "react";
import { Character, Position } from "../types";
import { OFFICE_LAYOUT } from "../constants";

interface MovementBounds {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
}

export const useCharacterMovement = (initialCharacters: Character[]) => {
  const [characters, setCharacters] = useState<Character[]>(initialCharacters);

  // Calculate movement bounds based on office layout
  const getMovementBounds = (characterType: string): MovementBounds => {
    const room = OFFICE_LAYOUT.find((r) => r.type === characterType);
    if (room) {
      return {
        minX: room.position.x + 20,
        maxX: room.position.x + room.width - 40,
        minY: room.position.y + 20,
        maxY: room.position.y + room.height - 40,
      };
    }
    // Default bounds for lobby/general movement
    return {
      minX: 50,
      maxX: 750,
      minY: 50,
      maxY: 550,
    };
  };

  // Move character to a random position within their bounds
  const moveCharacterRandomly = useCallback(
    (character: Character): Character => {
      const bounds = getMovementBounds(character.type);

      const newX = bounds.minX + Math.random() * (bounds.maxX - bounds.minX);
      const newY = bounds.minY + Math.random() * (bounds.maxY - bounds.minY);

      return {
        ...character,
        position: { x: newX, y: newY },
        targetPosition: { x: newX, y: newY },
        isMoving: true,
      };
    },
    []
  );

  // Move character towards another character (for interactions)
  const moveCharacterTowards = useCallback(
    (
      character: Character,
      target: Position,
      distance: number = 50
    ): Character => {
      const dx = target.x - character.position.x;
      const dy = target.y - character.position.y;
      const angle = Math.atan2(dy, dx);

      const newX = target.x - Math.cos(angle) * distance;
      const newY = target.y - Math.sin(angle) * distance;

      const bounds = getMovementBounds(character.type);
      const boundedX = Math.max(bounds.minX, Math.min(bounds.maxX, newX));
      const boundedY = Math.max(bounds.minY, Math.min(bounds.maxY, newY));

      return {
        ...character,
        position: { x: boundedX, y: boundedY },
        targetPosition: { x: boundedX, y: boundedY },
        isMoving: true,
      };
    },
    []
  );

  // Make manager visit an agent
  const managerVisitAgent = useCallback(
    (agentType: string) => {
      setCharacters((prevChars) => {
        const manager = prevChars.find((c) => c.type === "manager");
        const agent = prevChars.find((c) => c.type === agentType);

        if (!manager || !agent) return prevChars;

        return prevChars.map((char) => {
          if (char.type === "manager") {
            return moveCharacterTowards(char, agent.position);
          }
          return char;
        });
      });
    },
    [moveCharacterTowards]
  );

  // Simulate planning stage movements
  const startPlanningMovements = useCallback(() => {
    const agentTypes = ["hotel", "flight", "budget", "activities"];
    let currentVisitIndex = 0;

    // Manager visits each agent
    const visitInterval = setInterval(() => {
      if (currentVisitIndex < agentTypes.length) {
        managerVisitAgent(agentTypes[currentVisitIndex]);
        currentVisitIndex++;
      } else {
        clearInterval(visitInterval);
      }
    }, 3000);

    // Random agent movements
    const moveInterval = setInterval(() => {
      setCharacters((prevChars) =>
        prevChars.map((char) => {
          if (char.type !== "manager" && Math.random() > 0.6) {
            return moveCharacterRandomly(char);
          }
          return char;
        })
      );
    }, 4000);

    return () => {
      clearInterval(visitInterval);
      clearInterval(moveInterval);
    };
  }, [managerVisitAgent, moveCharacterRandomly]);

  // Reset movement flags
  useEffect(() => {
    const resetInterval = setInterval(() => {
      setCharacters((prevChars) =>
        prevChars.map((char) => ({
          ...char,
          isMoving: false,
        }))
      );
    }, 600);

    return () => clearInterval(resetInterval);
  }, []);

  return {
    characters,
    setCharacters,
    moveCharacterRandomly,
    moveCharacterTowards,
    managerVisitAgent,
    startPlanningMovements,
  };
};
