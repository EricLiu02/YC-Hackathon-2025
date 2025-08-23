import React, { useState, useEffect, useRef } from "react";
import { DialogMessage } from "../../types";
import "./DialogBox.css";

// Helper component for character avatar
const CharacterAvatar: React.FC<{ characterType?: string }> = ({
  characterType,
}) => {
  if (!characterType) return null;

  return (
    <div className={`message-avatar avatar-${characterType}`}>
      <div className="avatar-sprite">
        <div className="avatar-head">
          <div className="avatar-eyes">
            <div className="avatar-eye"></div>
            <div className="avatar-eye"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface DialogBoxProps {
  messages: DialogMessage[];
  onUserInput?: (input: string) => void;
  showInput?: boolean;
  placeholder?: string;
  isTyping?: boolean;
  actionButton?: {
    text: string;
    onClick: () => void;
  };
  onClose?: () => void;
}

const DialogBox: React.FC<DialogBoxProps> = ({
  messages,
  onUserInput,
  showInput = false,
  placeholder = "Hi, how can I help you?",
  isTyping = false,
  actionButton,
  onClose,
}) => {
  const [userInput, setUserInput] = useState("");
  const [displayedText, setDisplayedText] = useState("");
  const contentRef = useRef<HTMLDivElement>(null);

  const currentMessage = messages[messages.length - 1];

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [messages, displayedText]);

  useEffect(() => {
    if (currentMessage && isTyping) {
      let index = 0;
      const text = currentMessage.text;
      setDisplayedText("");

      const timer = setInterval(() => {
        if (index < text.length) {
          setDisplayedText(text.substring(0, index + 1));
          index++;
        } else {
          clearInterval(timer);
        }
      }, 50);

      return () => clearInterval(timer);
    } else if (currentMessage) {
      setDisplayedText(currentMessage.text);
    }
  }, [currentMessage, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (userInput.trim() && onUserInput) {
      onUserInput(userInput.trim());
      setUserInput("");
    }
  };

  return (
    <div className="dialog-box">
      {onClose && (
        <button
          className="dialog-close-button"
          onClick={onClose}
          aria-label="Close dialog"
        >
          ×
        </button>
      )}
      {messages.length > 0 && (
        <div className="dialog-content" ref={contentRef}>
          {messages.length > 1 && (
            <div className="message-history">
              {messages.slice(0, -1).map((msg, index) => (
                <div
                  key={index}
                  className={`message ${msg.isUser ? "user" : "agent"}`}
                >
                  {!msg.isUser && (
                    <CharacterAvatar characterType={msg.characterType} />
                  )}
                  <div className="message-content">
                    <span className="speaker">{msg.speaker}:</span>
                    <span className="text">{msg.text}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {currentMessage && (
            <div
              className={`current-message ${
                currentMessage.isUser ? "user" : "agent"
              }`}
            >
              {!currentMessage.isUser && (
                <CharacterAvatar characterType={currentMessage.characterType} />
              )}
              <div className="message-content">
                <span className="speaker">{currentMessage.speaker}:</span>
                <span className="text">
                  {displayedText}
                  {isTyping &&
                    displayedText.length < currentMessage.text.length && (
                      <span className="cursor">▮</span>
                    )}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {showInput && (
        <form onSubmit={handleSubmit} className="dialog-input-form">
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder={placeholder}
            className="dialog-input"
            autoFocus
          />
          <button type="submit" className="dialog-submit pixel-button">
            SEND
          </button>
        </form>
      )}

      {actionButton && !showInput && (
        <div className="dialog-action-container">
          <button
            onClick={actionButton.onClick}
            className="dialog-action pixel-button"
          >
            {actionButton.text}
          </button>
        </div>
      )}
    </div>
  );
};

export default DialogBox;
