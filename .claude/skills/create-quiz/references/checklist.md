# Pre-Launch Checklist

Before considering a quiz complete, verify each item:

## Structure
- [ ] Single self-contained HTML file (all CSS/JS inline)
- [ ] Dark theme (background: #0d1117 or #1a1a2e)
- [ ] Consistent accent color throughout
- [ ] Title in header matches filename intent

## Functionality
- [ ] All data loads without errors (no console errors on page load)
- [ ] Game state tracks correctly (score updates, completion triggers)
- [ ] Completion modal shows accurate final score
- [ ] "Play Again" button reloads cleanly

## Mobile
- [ ] Responsive layout works on 375px width
- [ ] Touch targets are at least 44x44px
- [ ] No horizontal scrolling
- [ ] Text is readable without zooming

## Accessibility
- [ ] All interactive elements are focusable
- [ ] Color is not the only indicator of state (use text/icons too)
- [ ] Sufficient contrast ratio (4.5:1 minimum for text)

## Integration
- [ ] Added to `index.html` landing page with appropriate icon and color
- [ ] Quiz works when served via `python3 -m http.server`
- [ ] No external dependencies beyond CDN (vis-network for graph quizzes)
