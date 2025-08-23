import React from "react";
import { Room } from "../../types";
import "./Office.css";

interface OfficeProps {
  rooms: Room[];
}

const Office: React.FC<OfficeProps> = ({ rooms }) => {
  // We'll use a static flexbox layout instead of dynamic positioning
  return (
    <div className="office-container">
      <div className="office-layout">
        {/* Top row - Meeting Rooms and Manager's Office */}
        <div className="office-row office-row-top">
          <div className="room room-meeting room-meeting-left">
            <div className="room-label">Meeting Room A</div>
            <div className="room-decorations">
              <div className="decoration conference-table">
                <div className="table-surface"></div>
                <div className="chair chair-top-left">🪑</div>
                <div className="chair chair-top-right">🪑</div>
                <div className="chair chair-bottom-left">🪑</div>
                <div className="chair chair-bottom-right">🪑</div>
                <div className="chair chair-left">🪑</div>
                <div className="chair chair-right">🪑</div>
              </div>
              <div className="decoration whiteboard">📋</div>
              <div className="decoration projector">📽️</div>
            </div>
          </div>

          <div className="room room-manager" data-room-id="manager-office">
            <div className="room-label">Manager Mike's Office</div>
            <div className="room-decorations">
              <div className="decoration desk" />
              <div className="decoration computer" />
              <div className="decoration plant left" />
              <div className="decoration plant right" />
            </div>
          </div>

          <div className="room room-meeting room-meeting-right">
            <div className="room-label">Meeting Room B</div>
            <div className="room-decorations">
              <div className="decoration conference-table">
                <div className="table-surface"></div>
                <div className="chair chair-top-left">🪑</div>
                <div className="chair chair-top-right">🪑</div>
                <div className="chair chair-bottom-left">🪑</div>
                <div className="chair chair-bottom-right">🪑</div>
                <div className="chair chair-left">🪑</div>
                <div className="chair chair-right">🪑</div>
              </div>
              <div className="decoration tv-screen">📺</div>
              <div className="decoration conference-phone">☎️</div>
            </div>
          </div>
        </div>

        {/* Middle row - Hotel, Lobby, Flight */}
        <div className="office-row office-row-middle">
          <div className="room room-hotel" data-room-id="hotel-office">
            <div className="room-label">Holly Hotel's Office</div>
            <div className="room-decorations">
              <div className="decoration hotel-icon">🏨</div>
              <div className="decoration desk" />
              <div className="decoration computer" />
              <div className="decoration plant" />
            </div>
          </div>

          <div className="room room-lobby" data-room-id="lobby">
            <div className="room-label">LOBBY</div>
            <div className="room-decorations">
              <div className="decoration plant top-left" />
              <div className="decoration plant top-right" />
              <div className="decoration plant bottom-left" />
              <div className="decoration plant bottom-right" />
              <div className="decoration desk reception" />
              <div className="decoration computer" />
            </div>
          </div>

          <div className="room room-flight" data-room-id="flight-office">
            <div className="room-label">Freddy Flights's Office</div>
            <div className="room-decorations">
              <div className="decoration plane-icon">✈️</div>
              <div className="decoration desk" />
              <div className="decoration computer" />
              <div className="decoration plant" />
            </div>
          </div>
        </div>

        {/* Bottom row - Budget and Activities */}
        <div className="office-row office-row-bottom">
          <div className="room room-budget" data-room-id="budget-office">
            <div className="room-label">Betty Budget's Office</div>
            <div className="room-decorations">
              <div className="decoration money-icon">💰</div>
              <div className="decoration desk" />
              <div className="decoration computer" />
              <div className="decoration plant" />
            </div>
          </div>

          <div className="room room-kitchen">
            <div className="room-label">Kitchen & Break Room</div>
            <div className="room-decorations">
              <div className="decoration coffee-machine">☕</div>
              <div className="decoration fridge">🍕</div>
              <div className="decoration microwave">🍿</div>
              <div className="decoration sink">🚰</div>
              <div className="decoration table kitchen-table" />
              <div className="decoration vending-machine">🥤</div>
              <div className="decoration fruit-basket">🍎</div>
            </div>
          </div>

          <div
            className="room room-activities"
            data-room-id="activities-office"
          >
            <div className="room-label">Andy Activities's Office</div>
            <div className="room-decorations">
              <div className="decoration activity-icon">🎭</div>
              <div className="decoration desk" />
              <div className="decoration computer" />
              <div className="decoration plant" />
            </div>
          </div>
        </div>

        {/* Office hallway decorations */}
        <div className="office-hallway-decorations">
          <div className="decoration water-cooler">💧</div>
          <div className="decoration bulletin-board">📌</div>
          <div className="decoration clock">🕐</div>
          <div className="decoration fire-extinguisher">🧯</div>
          <div className="decoration exit-sign">🚪</div>
        </div>
      </div>
    </div>
  );
};

export default Office;
