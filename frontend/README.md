# 8-Bit Travel Agency Game 🎮✈️

An interactive 8-bit style game inspired by Pokemon Red and Black Mirror: Bandersnatch, where you plan your dream vacation through a pixel art travel agency!

## 🎯 Game Overview

Experience a nostalgic journey through a pixelated travel agency where specialized agents work together to create your perfect vacation package. The game features:

- **Manager Mike** - The coordinator who handles your initial consultation
- **Holly Hotel** - Your accommodation specialist
- **Freddy Flights** - Your aviation expert  
- **Betty Budget** - Your financial advisor
- **Andy Activities** - Your entertainment and dining curator

## 🎮 How to Play

### Stage 1: Initial Consultation
1. Start by typing your travel request (e.g., "I want to travel to Hawaii")
2. Answer Manager Mike's questions about:
   - Travel dates
   - Duration of stay
   - Budget
   - Preferred activities

### Stage 2: Planning Phase
- Watch as the agents move around the office
- See their thought bubbles as they work on your itinerary
- Agents will interact with each other to coordinate your perfect trip

### Stage 3: Final Presentation
- Manager Mike returns with your complete travel package
- Review your customized itinerary including:
  - Flight details
  - Hotel accommodation
  - Budget breakdown
  - Activity recommendations

## 🚀 Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open your browser and navigate to:
```
http://localhost:3000
```

## 🎨 Features

### Visual Design
- **8-bit pixel art characters** with unique designs for each agent type
- **Detailed office layout** with themed rooms for each specialist
- **Retro decorations** including planes, hotels, money symbols, and activity icons
- **CRT TV effect** for authentic retro gaming feel
- **Scanline effects** to enhance the nostalgic atmosphere

### Animations
- **Character walking animations** with pixel-perfect movement
- **Thought bubbles** that float above characters
- **Typewriter text effects** for dialog
- **Pulsing and glowing UI elements**

### Interactive Elements
- **Real-time character movement** during planning phase
- **Dynamic dialog system** with typewriter effects
- **Stage-based progression** with smooth transitions
- **Responsive user input** with 8-bit styled text boxes

## 🛠️ Technical Architecture

### Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── Characters/    # Character sprites and animations
│   │   ├── Office/        # Office layout and rooms
│   │   ├── UI/            # Dialog boxes and UI elements
│   │   └── Game/          # Main game controller
│   ├── types/             # TypeScript type definitions
│   ├── constants/         # Game configuration and data
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Helper functions
│   └── styles/            # Global CSS and themes
```

### Technologies Used
- **React** with TypeScript for robust component architecture
- **CSS3** with custom pixel art styling
- **Web Fonts** (Press Start 2P) for authentic 8-bit text
- **React Hooks** for state management and effects

## 🎮 Game Controls

- **Type** in the text box to interact with Manager Mike
- **Enter** to submit your responses
- **Watch** the automated planning phase
- **Enjoy** the nostalgic 8-bit experience!

## 🔧 Development

### Available Scripts

- `npm start` - Run development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

### Customization

You can customize various aspects of the game:

1. **Characters** - Modify character appearances in `Character.css`
2. **Office Layout** - Adjust room positions in `constants/index.ts`
3. **Dialog** - Edit conversation flows in `utils/dialogUtils.ts`
4. **Animations** - Tweak animation speeds in component CSS files

## 🎨 Design Philosophy

This game combines:
- **Nostalgic 8-bit aesthetics** from classic Pokemon games
- **Interactive storytelling** inspired by Black Mirror: Bandersnatch
- **Modern web technologies** for smooth performance
- **Modular architecture** for easy extensibility

## 📝 Future Enhancements

Potential features for expansion:
- [ ] Save/load travel plans
- [ ] Multiple destination options
- [ ] Mini-games for each agent specialty
- [ ] Multiplayer agency management
- [ ] Real travel API integration
- [ ] Achievement system
- [ ] Sound effects and 8-bit music

## 🤝 Contributing

Feel free to fork this project and add your own features! Some ideas:
- New character types
- Additional office decorations
- More dialog options
- Enhanced animations
- Mobile responsiveness

## 📜 License

This project is created for the YC Hackathon 2025.

---

Enjoy your pixelated travel planning adventure! 🎮✈️🏨💰🎭