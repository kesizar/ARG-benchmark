# ESCAPE THE WEBSITE

An interactive, immersive web-based mini adventure game where the player solves puzzles and navigates secrets to escape the website itself.

## Technologies Used

- **HTML5** (Semantic structure)
- **CSS3 / Vanilla CSS** (Custom theme variables and layout)
- **Vanilla JavaScript** (Modular ES6 architecture, no heavy frameworks)
- **Bootstrap 5** (Layout and base utility classes via CDN)
- **GSAP (GreenSock Animation Platform)** (Smooth visual animations via CDN)
- **Google Fonts** (Orbitron, Inter, JetBrains Mono)

## Project Structure

```text
escape-the-website/
├── index.html          # Main HTML entry point
├── css/
│   ├── style.css       # Core styles and color palette
│   └── animations.css  # Keyframe animations and transitions
├── js/
│   ├── main.js         # App bootstrap and DOM wiring
│   ├── game.js         # Game state & localStorage management
│   ├── puzzles.js      # Puzzle registration and validation logic
│   └── audio.js        # Audio & sound effects controller
├── assets/
│   ├── images/         # Game visual assets
│   ├── icons/          # UI and puzzle icons
│   └── sounds/         # Audio clips & ambient sound tracks
└── README.md           # Project documentation
```

## How to Run

Because this is a 100% static web application, no build steps, backend servers, or databases are required.

### Method 1: Local HTTP Server (Recommended)
Using Python or Node.js to serve the directory:

```bash
# Using Python 3:
python -m http.server 8000

# Or using npx serve:
npx serve .
```
Then open [http://localhost:8000](http://localhost:8000) in any modern browser.

### Method 2: Direct File Opening
Double-click `index.html` or open it directly inside your browser.
