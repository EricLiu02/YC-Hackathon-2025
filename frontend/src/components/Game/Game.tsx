import React, {
  useState,
  useCallback,
  useMemo,
  useRef,
  useEffect,
} from "react";
import Office from "../Office/Office";
import Character from "../Characters/Character";
import DialogBox from "../UI/DialogBox";
import {
  Character as CharacterType,
  GameStage,
  DialogMessage,
} from "../../types";
import {
  INITIAL_CHARACTERS,
  AGENT_THOUGHTS,
  IDLE_THOUGHTS,
} from "../../constants";
import "./Game.css";

const Game: React.FC = () => {
  const [gameStage, setGameStage] = useState<GameStage>("idle");
  const [characters, setCharacters] =
    useState<CharacterType[]>(INITIAL_CHARACTERS);
  const [dialogMessages, setDialogMessages] = useState<DialogMessage[]>([]);
  const [showDialog, setShowDialog] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [showActionButton, setShowActionButton] = useState(false);
  const [activeAgentChat, setActiveAgentChat] = useState<CharacterType | null>(
    null
  );
  const [agentChatMessages, setAgentChatMessages] = useState<DialogMessage[]>(
    []
  );
  const intervalIdsRef = useRef<NodeJS.Timeout[]>([]);
  const timeoutsRef = useRef<NodeJS.Timeout[]>([]);

  // Mock manager questions for the intro stage
  const managerQuestions = useMemo(
    () => [
      "That sounds wonderful! When would you like to travel?",
      "How many days are you planning to stay?",
      "What's your budget for this trip?",
      "Are you interested in any specific activities?",
      "Great! Let me coordinate with my team to create the perfect itinerary for you.",
    ],
    []
  );
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Show final travel plan
  const showFinalPlan = useCallback(() => {
    setShowDialog(true);
    setShowActionButton(false); // Reset action button
    setDialogMessages([
      {
        speaker: "Manager Mike",
        text: "I've got your perfect Hawaii vacation ready! Here's what we've prepared for you:",
        isUser: false,
        characterType: "manager",
      },
      {
        speaker: "Manager Mike",
        text: "✈️ FLIGHT: Direct flight from SFO to Honolulu, window seat secured!",
        isUser: false,
      },
      {
        speaker: "Manager Mike",
        text: "🏨 HOTEL: Beachfront resort with ocean view, breakfast included!",
        isUser: false,
      },
      {
        speaker: "Manager Mike",
        text: "💰 BUDGET: Total cost $2,500 - Great value with our partner discounts!",
        isUser: false,
      },
      {
        speaker: "Manager Mike",
        text: "🎭 ACTIVITIES: Snorkeling tour, luau dinner, Pearl Harbor visit, and hiking Diamond Head!",
        isUser: false,
      },
      {
        speaker: "Manager Mike",
        text: "Would you like to book this amazing trip?",
        isUser: false,
      },
    ]);
    setIsTyping(true);

    // Show action button after final message
    setTimeout(() => {
      setShowActionButton(true);
    }, 5000); // Wait for messages to display
  }, []);

  // Clear all intervals and timeouts
  const clearAllIntervals = useCallback(() => {
    intervalIdsRef.current.forEach((id) => clearInterval(id));
    timeoutsRef.current.forEach((id) => clearTimeout(id));
    intervalIdsRef.current = [];
    timeoutsRef.current = [];
  }, []);

  // Get room bounds for a character type
  const getRoomBounds = useCallback((charType: string) => {
    // Define static bounds for each room based on flexbox layout
    const bounds: Record<
      string,
      { minX: number; maxX: number; minY: number; maxY: number }
    > = {
      manager: { minX: 450, maxX: 750, minY: 60, maxY: 140 },
      hotel: { minX: 100, maxX: 400, minY: 230, maxY: 330 },
      lobby: { minX: 450, maxX: 750, minY: 230, maxY: 330 },
      flight: { minX: 800, maxX: 1100, minY: 230, maxY: 330 },
      budget: { minX: 100, maxX: 400, minY: 400, maxY: 500 },
      activities: { minX: 800, maxX: 1100, minY: 400, maxY: 500 },
    };

    return bounds[charType] || { minX: 450, maxX: 750, minY: 230, maxY: 330 }; // Default to lobby
  }, []);

  // Get character's home position (center of their office)
  const getHomePosition = useCallback((charType: string) => {
    // Define static home positions for each character type
    const positions: Record<string, { x: number; y: number }> = {
      manager: { x: 600, y: 100 },
      hotel: { x: 250, y: 280 },
      flight: { x: 1010, y: 280 },
      budget: { x: 250, y: 450 },
      activities: { x: 1010, y: 450 },
    };

    return positions[charType] || { x: 600, y: 300 }; // Center of lobby as fallback
  }, []);

  // Realistic character movement - mostly stay in office, occasionally visit others
  const moveCharacters = useCallback(() => {
    setCharacters((prevChars) => {
      return prevChars.map((char, index) => {
        // Don't move if character is thinking (during planning stage only)
        if (char.currentThought && gameStage === "planning") {
          return { ...char, isMoving: false };
        }

        // Each character has different movement probability
        const shouldMove = Math.random() < 0.3; // Only 30% chance to move at all
        if (!shouldMove) {
          return { ...char, isMoving: false };
        }

        // 10% chance to visit someone else's office (realistic office behavior)
        if (Math.random() < 0.1) {
          const otherChars = prevChars.filter((c) => c.id !== char.id);
          if (otherChars.length > 0) {
            const target =
              otherChars[Math.floor(Math.random() * otherChars.length)];
            const targetHome = getHomePosition(target.type);

            // Move to a spot near the target's desk
            const meetingX = targetHome.x + (Math.random() - 0.5) * 30;
            const meetingY = targetHome.y + (Math.random() - 0.5) * 30;

            // Schedule return to own office after visit
            const returnTimeout = setTimeout(() => {
              setCharacters((prev) =>
                prev.map((c) => {
                  if (c.id === char.id) {
                    const homePos = getHomePosition(c.type);
                    return {
                      ...c,
                      position: homePos,
                      isMoving: true,
                    };
                  }
                  return c;
                })
              );

              // Stop moving after returning
              setTimeout(() => {
                setCharacters((prev) =>
                  prev.map((c) =>
                    c.id === char.id ? { ...c, isMoving: false } : c
                  )
                );
              }, 3000);
            }, 8000 + Math.random() * 4000); // Stay for 8-12 seconds

            timeoutsRef.current.push(returnTimeout);

            // Show thought bubble during visit (80% chance)
            if (gameStage === "idle" && Math.random() > 0.2) {
              const thoughtTimeout = setTimeout(() => {
                setCharacters((prev) =>
                  prev.map((c) => {
                    if (c.id === char.id) {
                      const thoughts =
                        IDLE_THOUGHTS[char.type as keyof typeof IDLE_THOUGHTS];
                      if (thoughts) {
                        return {
                          ...c,
                          currentThought:
                            thoughts[
                              Math.floor(Math.random() * thoughts.length)
                            ],
                        };
                      }
                    }
                    return c;
                  })
                );
              }, 1000);

              timeoutsRef.current.push(thoughtTimeout);

              // Clear thought after a bit
              const clearThoughtTimeout = setTimeout(() => {
                setCharacters((prev) =>
                  prev.map((c) =>
                    c.id === char.id ? { ...c, currentThought: undefined } : c
                  )
                );
              }, 8000);

              timeoutsRef.current.push(clearThoughtTimeout);
            }

            return {
              ...char,
              position: { x: meetingX, y: meetingY },
              isMoving: true,
            };
          }
        }

        // 90% of the time, just move within own office
        const bounds = getRoomBounds(char.type);
        const homePos = getHomePosition(char.type);

        // Small movements within office (more realistic)
        const newX = homePos.x + (Math.random() - 0.5) * 40;
        const newY = homePos.y + (Math.random() - 0.5) * 30;

        const finalX = Math.max(bounds.minX, Math.min(bounds.maxX, newX));
        const finalY = Math.max(bounds.minY, Math.min(bounds.maxY, newY));

        // Stop moving after reaching destination
        const stopTimeout = setTimeout(() => {
          setCharacters((prev) =>
            prev.map((c) => (c.id === char.id ? { ...c, isMoving: false } : c))
          );
        }, 3000);

        timeoutsRef.current.push(stopTimeout);

        return {
          ...char,
          position: { x: finalX, y: finalY },
          isMoving: true,
        };
      });
    });
  }, [getRoomBounds, getHomePosition, gameStage]);

  // Start planning stage with character movements and thoughts
  const startPlanningStage = useCallback(() => {
    // Clear any existing intervals first
    clearAllIntervals();

    // Planning stage setup - no need for character states

    // Create a coordinated planning sequence
    let visitIndex = 0;
    const agentTypes = ["hotel", "flight", "budget", "activities"];

    // Manager visits each agent in sequence
    const managerVisitSequence = () => {
      if (visitIndex < agentTypes.length) {
        const targetType = agentTypes[visitIndex];
        const manager = characters.find((c) => c.type === "manager");
        const targetAgent = characters.find((c) => c.type === targetType);

        if (manager && targetAgent) {
          // Move manager to visit agent
          setCharacters((prevChars) =>
            prevChars.map((char) => {
              if (char.type === "manager") {
                const targetHome = getHomePosition(targetType);
                const meetingX = targetHome.x - 30; // Stand near the agent
                const meetingY = targetHome.y;

                return {
                  ...char,
                  position: { x: meetingX, y: meetingY },
                  isMoving: true,
                };
              }
              return char;
            })
          );

          // Show agent's thought when manager arrives
          setTimeout(() => {
            setCharacters((prevChars) =>
              prevChars.map((char) => {
                if (char.type === targetType) {
                  const thoughts =
                    AGENT_THOUGHTS[targetType as keyof typeof AGENT_THOUGHTS];
                  return {
                    ...char,
                    currentThought:
                      thoughts[Math.floor(Math.random() * thoughts.length)],
                  };
                }
                return char;
              })
            );
          }, 1500);

          // Clear thought after a moment
          setTimeout(() => {
            setCharacters((prevChars) =>
              prevChars.map((char) => ({
                ...char,
                currentThought: undefined,
              }))
            );
          }, 7000);
        }

        visitIndex++;
      }
    };

    // Show random thoughts
    const showThoughts = () => {
      setCharacters((prevChars) =>
        prevChars.map((char) => {
          // 50% chance to show a thought
          if (Math.random() > 0.5) {
            return char;
          }

          const thoughts =
            AGENT_THOUGHTS[char.type as keyof typeof AGENT_THOUGHTS];
          if (!thoughts || thoughts.length === 0) {
            return char;
          }

          const randomThought =
            thoughts[Math.floor(Math.random() * thoughts.length)];

          return {
            ...char,
            currentThought: randomThought,
          };
        })
      );
    };

    // Start the manager visit sequence
    managerVisitSequence();
    const visitInterval = setInterval(managerVisitSequence, 4000); // Visit next agent every 4 seconds

    // General movement for other agents
    const moveInterval = setInterval(moveCharacters, 2500); // Move every 2.5 seconds
    const thoughtInterval = setInterval(showThoughts, 2500); // Show thoughts every 2.5 seconds

    // Start immediate movement
    moveCharacters();

    // Clear thoughts periodically
    const clearThoughtsInterval = setInterval(() => {
      setCharacters((prevChars) =>
        prevChars.map((char) => ({
          ...char,
          currentThought: undefined,
        }))
      );
    }, 9000); // Clear thoughts every 9 seconds

    // Store interval IDs
    intervalIdsRef.current = [
      visitInterval,
      moveInterval,
      thoughtInterval,
      clearThoughtsInterval,
    ];

    // After 20 seconds, transition to final stage
    const finalTimeout = setTimeout(() => {
      clearAllIntervals();
      setGameStage("final");
      showFinalPlan();
    }, 20000);

    // Store timeout as well
    intervalIdsRef.current.push(finalTimeout);
  }, [
    showFinalPlan,
    clearAllIntervals,
    moveCharacters,
    characters,
    getHomePosition,
  ]);

  // Handle user input in intro stage
  const handleUserInput = useCallback(
    (input: string) => {
      if (gameStage === "idle") {
        // Start the game
        setGameStage("intro");
        setDialogMessages([
          { speaker: "You", text: input, isUser: true },
          {
            speaker: "Manager Mike",
            text: managerQuestions[0],
            isUser: false,
            characterType: "manager",
          },
        ]);
        setIsTyping(true);
        setCurrentQuestionIndex(1);
      } else if (gameStage === "intro") {
        // Continue intro conversation
        const newMessages = [
          ...dialogMessages,
          { speaker: "You", text: input, isUser: true },
        ];

        if (currentQuestionIndex < managerQuestions.length) {
          newMessages.push({
            speaker: "Manager Mike",
            text: managerQuestions[currentQuestionIndex],
            isUser: false,
            characterType: "manager",
          });
          setDialogMessages(newMessages);
          setCurrentQuestionIndex(currentQuestionIndex + 1);
          setIsTyping(true);

          // If this was the last question, show the action button
          if (currentQuestionIndex === managerQuestions.length - 1) {
            setTimeout(() => {
              setShowActionButton(true);
            }, 3000); // Wait for the typing animation to finish
          }
        }
      }
    },
    [gameStage, dialogMessages, currentQuestionIndex, managerQuestions]
  );

  // Handle agent click - open chat dialog
  const handleAgentClick = useCallback(
    (character: CharacterType) => {
      // Don't open chat during intro or final stages
      if (gameStage === "intro" || gameStage === "final") return;

      setActiveAgentChat(character);
      setAgentChatMessages([
        {
          speaker: character.name,
          text:
            character.currentThought ||
            `Hi! I'm ${character.name}. How can I help you today?`,
          isUser: false,
          characterType: character.type,
        },
      ]);
    },
    [gameStage]
  );

  // Handle agent chat input
  const handleAgentChatInput = useCallback(
    (input: string) => {
      if (!activeAgentChat) return;

      // Add user message
      setAgentChatMessages((prev) => [
        ...prev,
        {
          speaker: "You",
          text: input,
          isUser: true,
        },
      ]);

      // Generate agent response based on their type
      setTimeout(() => {
        const responses: Record<string, string[]> = {
          hotel: [
            "I've found some amazing beachfront properties!",
            "The sunset views from these hotels are incredible!",
            "All our hotels include breakfast and WiFi.",
            "I can get you a special discount on ocean view rooms!",
          ],
          flight: [
            "I can find you the best flight deals!",
            "Window or aisle seat preference?",
            "Direct flights are available at great prices!",
            "I've secured priority boarding for you!",
          ],
          budget: [
            "Let me optimize your travel budget!",
            "I can find great value deals for you.",
            "Your budget will go far with these options!",
            "I've calculated the best cost-effective choices!",
          ],
          activities: [
            "There are so many exciting things to do!",
            "I've found the best restaurants in the area!",
            "How about some adventure activities?",
            "The local culture experiences are amazing!",
          ],
          manager: [
            "I'm coordinating everything for your perfect trip!",
            "Let me check with the team on that.",
            "We'll make sure everything is perfect!",
            "Your satisfaction is our priority!",
          ],
        };

        const agentResponses = responses[activeAgentChat.type] || [
          "I'm here to help!",
        ];
        const randomResponse =
          agentResponses[Math.floor(Math.random() * agentResponses.length)];

        setAgentChatMessages((prev) => [
          ...prev,
          {
            speaker: activeAgentChat.name,
            text: randomResponse,
            isUser: false,
            characterType: activeAgentChat.type,
          },
        ]);
      }, 1000);
    },
    [activeAgentChat]
  );

  // Handle action button click
  const handleActionButton = useCallback(() => {
    if (gameStage === "intro") {
      // Start planning stage
      setShowDialog(false);
      setShowActionButton(false);
      setGameStage("planning");
      startPlanningStage();
    } else if (gameStage === "final") {
      // Book the trip - restart game or show success
      setDialogMessages([
        {
          speaker: "Manager Mike",
          text: "🎉 Fantastic! Your trip is booked! Have an amazing vacation!",
          isUser: false,
          characterType: "manager",
        },
      ]);
      setShowActionButton(false);
      setIsTyping(true);

      // Reset game after 3 seconds
      const resetTimeout = setTimeout(() => {
        clearAllIntervals(); // Clear any running intervals
        setGameStage("idle");
        setShowDialog(true);
        setDialogMessages([]);
        setCurrentQuestionIndex(0);
        setShowActionButton(false);
        // Reset characters to initial positions
        setCharacters(INITIAL_CHARACTERS);
      }, 3000);

      timeoutsRef.current.push(resetTimeout);
    }
  }, [gameStage, startPlanningStage, clearAllIntervals]);

  // Handle dialog close
  const handleDialogClose = useCallback(() => {
    setShowDialog(false);
    // If we're in intro and have the action button, start planning
    if (gameStage === "intro" && showActionButton) {
      setShowActionButton(false);
      setGameStage("planning");
      startPlanningStage();
    } else if (gameStage === "final") {
      // If closing during final stage, clear intervals and hide dialog
      clearAllIntervals();
      setShowActionButton(false);
    }
  }, [gameStage, showActionButton, startPlanningStage, clearAllIntervals]);

  // Handle character movement based on game stage
  useEffect(() => {
    // Start movement in idle stage
    if (gameStage === "idle") {
      // Clear any existing intervals first
      clearAllIntervals();
      // In idle stage, characters move occasionally
      const moveInterval = setInterval(moveCharacters, 5000); // Check for movement every 5 seconds

      // Add random thought bubbles in idle stage
      const idleThoughtInterval = setInterval(() => {
        setCharacters((prevChars) =>
          prevChars.map((char) => {
            // 40% chance to show a thought
            if (Math.random() < 0.4 && !char.currentThought) {
              const thoughts =
                IDLE_THOUGHTS[char.type as keyof typeof IDLE_THOUGHTS];
              if (thoughts && thoughts.length > 0) {
                // Set thought
                setTimeout(() => {
                  setCharacters((prev) =>
                    prev.map((c) => {
                      if (c.id === char.id) {
                        return {
                          ...c,
                          currentThought:
                            thoughts[
                              Math.floor(Math.random() * thoughts.length)
                            ],
                        };
                      }
                      return c;
                    })
                  );
                }, Math.random() * 2000); // Random delay up to 2 seconds

                // Clear thought after 6-8 seconds
                setTimeout(() => {
                  setCharacters((prev) =>
                    prev.map((c) =>
                      c.id === char.id ? { ...c, currentThought: undefined } : c
                    )
                  );
                }, 6000 + Math.random() * 2000);
              }
            }
            return char;
          })
        );
      }, 3000); // Check every 3 seconds

      intervalIdsRef.current = [moveInterval, idleThoughtInterval];

      // Start with a slight delay for more natural feel
      setTimeout(() => moveCharacters(), 1000);
    } else if (gameStage === "intro" || gameStage === "final") {
      // Stop movement in intro and final stages
      clearAllIntervals();
      // Reset everyone to their desks
      setCharacters((prevChars) =>
        prevChars.map((char) => {
          const homePos = getHomePosition(char.type);
          return {
            ...char,
            position: homePos,
            isMoving: false,
          };
        })
      );
    }
    // Planning stage is handled by startPlanningStage

    // Cleanup on unmount
    return () => {
      clearAllIntervals();
    };
  }, [gameStage, moveCharacters, clearAllIntervals, getHomePosition]);

  // Reset character movement state is now handled within movement logic
  // Characters are always moving - no manual controls needed

  return (
    <div className="game-container">
      <div className="game-header">
        <h1 className="game-title">Pocket Office</h1>
      </div>

      <div className="game-world">
        <Office rooms={[]} />

        {characters.map((character) => (
          <Character
            key={character.id}
            character={character}
            showThought={gameStage === "planning"}
            onClick={() => handleAgentClick(character)}
          />
        ))}
      </div>

      {showDialog && (
        <DialogBox
          messages={dialogMessages}
          onUserInput={handleUserInput}
          showInput={
            gameStage === "idle" ||
            (gameStage === "intro" &&
              currentQuestionIndex < managerQuestions.length &&
              !showActionButton)
          }
          placeholder={
            gameStage === "idle"
              ? "Hi, how can I help you?"
              : "Type your answer..."
          }
          isTyping={isTyping}
          actionButton={
            showActionButton
              ? {
                  text: gameStage === "final" ? "Book it! 🎉" : "Let's do it!",
                  onClick: handleActionButton,
                }
              : undefined
          }
          onClose={handleDialogClose}
        />
      )}

      {activeAgentChat && (
        <DialogBox
          messages={agentChatMessages}
          onUserInput={handleAgentChatInput}
          showInput={true}
          placeholder={`Chat with ${activeAgentChat.name}...`}
          isTyping={false}
          onClose={() => setActiveAgentChat(null)}
        />
      )}

      {gameStage === "planning" && (
        <div className="planning-indicator">
          <div className="loading-dots">
            <span>Planning your trip</span>
            <span className="dot">.</span>
            <span className="dot">.</span>
            <span className="dot">.</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Game;
