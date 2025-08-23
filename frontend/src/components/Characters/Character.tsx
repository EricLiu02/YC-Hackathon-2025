import React from "react";
import { Character as CharacterType } from "../../types";
import "./Character.css";

interface CharacterProps {
  character: CharacterType;
  showThought?: boolean;
  onClick?: () => void;
}

const Character: React.FC<CharacterProps> = ({
  character,
  showThought,
  onClick,
}) => {
  // Determine character state for visual effects
  const getCharacterState = () => {
    if (character.isMoving) return "moving";
    if (character.currentThought) return "thinking";
    return "idle";
  };

  return (
    <div
      className={`character-container character-${
        character.type
      } ${getCharacterState()}`}
      style={{
        left: `${character.position.x}px`,
        top: `${character.position.y}px`,
      }}
      onClick={onClick}
    >
      <div className="character-sprite">
        {/* Character with unique personality */}
        <div className="character-body">
          <div className="character-head">
            <div className="character-eyes">
              <div className="character-eye"></div>
              <div className="character-eye"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Character name label with glow */}
      <div className="character-name">{character.name}</div>

      {/* Enhanced thought bubble */}
      {showThought && character.currentThought && (
        <div className="thought-bubble">
          <span className="thought-text">{character.currentThought}</span>
          <div className="thought-dots">
            <span className="thought-dot"></span>
            <span className="thought-dot"></span>
            <span className="thought-dot"></span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Character;
