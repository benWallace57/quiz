---
name: network-quiz
description: Reference patterns for creating vis-network force-directed graph quizzes. Use when building any network/relationship graph quiz — character networks, border maps, collaboration graphs, etc.
when_to_use: network quiz, graph quiz, vis-network, force directed, relationship quiz, border quiz, character quiz
user-invocable: true
---

# Network Graph Quiz Pattern

## HTML Structure

```html
<div id="header">        <!-- fixed top bar: title + score -->
<div id="network-container">  <!-- fullscreen vis-network canvas -->
<div id="name-list">    <!-- right sidebar: alphabetical clickable name buttons -->
<div id="guess-panel">  <!-- bottom center: hints + attempt counter, shown on node click -->
<div id="completion-modal">  <!-- overlay on quiz complete -->
```

## vis-network Setup

```javascript
const network = new vis.Network(container, { nodes, edges }, {
  physics: {
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {
      gravitationalConstant: -60,
      centralGravity: 0.012,
      springLength: 120,
      springConstant: 0.06,
      damping: 0.4
    },
    stabilization: { iterations: 1500, updateInterval: 25 }
  },
  interaction: { hover: true, tooltipDelay: 300, zoomView: true, dragView: true, dragNodes: false }
});

// Freeze after stabilization
network.once('stabilizationIterationsDone', () => network.setOptions({ physics: false }));
```

## Data Structures

**Nodes:**
```javascript
{ id: "Walter", weight: 6528, community: 0, aliases: ["walt", "heisenberg", "mr white"] }
```

**Edges:**
```javascript
{ source: "Walter", target: "Jesse", weight: 2185 }
```

For border quizzes, edges can include a `type` field: `"border"` or `"maritime"`.

## Sizing Formulas

**Node size** (sqrt scaling for area-based visual):
```javascript
function nodeSize(weight) {
  const norm = (Math.sqrt(weight) - sqrtMin) / (sqrtMax - sqrtMin);
  return 12 + norm * 43;  // range: 12px to 55px
}
```

**Edge width** (log or power scaling):
```javascript
function edgeWidth(weight) {
  const norm = (Math.log(weight) - logMin) / (logMax - logMin);
  return 0.5 + norm * 11.5;
}
// Or power scaling for more dramatic differences:
// return 0.3 + Math.pow(norm, 0.6) * 8;
```

## Community Colors

Use muted/bright variants — muted for unrevealed, bright for correctly guessed:
```javascript
const COMMUNITY_COLORS = {
  0: { muted: 'rgba(46, 134, 171, 0.6)', bright: '#2E86AB' },
  1: { muted: 'rgba(27, 67, 50, 0.7)', bright: '#2d8a5e' },
  // ... one per community/group
};
```

## Game State Pattern

```javascript
let gameState = {
  revealed: new Set(),
  guessedCorrectly: new Set(),
  failedReveal: new Set(),
  selectedNode: null,
  attempts: {},        // nodeId -> attempt count
  totalGuesses: 0
};
```

## Guess Mechanics

1. User clicks an unrevealed node → `selectNode(nodeId)`
2. Show hint panel with: connection count, names of revealed neighbours
3. User clicks a name button in the sidebar
4. If correct: reveal node with bright color + white label
5. If wrong: shake animation, increment attempts
6. After 3 wrong attempts: auto-reveal with muted label (fail state)
7. Mark used name buttons (correct = green strikethrough, failed = red strikethrough)

## Reveal Node

```javascript
function revealNode(nodeId, guessedCorrectly) {
  gameState.revealed.add(nodeId);
  if (guessedCorrectly) {
    // Bright color, white border, visible label
    nodes.update({ id: nodeId, label: char.id, color: { background: bright, border: '#fff' }, font: { color: '#fff', size: 14 } });
  } else {
    // Muted color, dim label
    nodes.update({ id: nodeId, label: char.id, color: { border: 'rgba(224,122,95,0.6)' }, font: { color: 'rgba(255,255,255,0.5)', size: 12 } });
  }
}
```

## CSS Layout

- Body: `overflow: hidden; height: 100vh; width: 100vw;`
- Network container: `width: calc(100vw - 220px); height: 100vh;`
- Name list sidebar: `position: fixed; right: 0; width: 220px; height: 100vh; overflow-y: auto;`
- Header: `position: fixed; top: 0; z-index: 100;`
- Guess panel: `position: fixed; bottom: 24px; left: calc((100vw - 220px) / 2); transform: translateX(-50%);`

## Variant: Border/Geography Quiz

For country border quizzes, additional features:
- Node size = country area (use sqrt scaling)
- Edge width = border length (use power scaling with exponent 0.6)
- Toggle button to switch between uniform and area-based sizing
- Maritime borders drawn as dashed lines (`dashes: [8, 8]`)
- Border objects: `{ id: "France", borders: [{id: "Germany", len: 451}], maritime: ["United Kingdom"] }`

## Data Sources for Network Quizzes

- Character interactions: co-occurrence in scenes/chapters (weight = shared screen time)
- Country borders: Natural Earth shapefiles, Wikipedia border length tables
- Collaborations: co-authorship, band members, movie casts
- Any entity + relationship dataset works — nodes are entities, edges are relationships
