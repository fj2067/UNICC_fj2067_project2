# User Experience Documentation — UNICC AI Safety Lab Web Interface

**Author:** Galaxy Okoro — Project 3 Manager
**Course:** NYU MASY GC-4100 Applied Project Capstone — Spring 2026
**Version:** 1.0 | **Date:** April 2026

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Screen-by-Screen Walkthrough](#2-screen-by-screen-walkthrough)
3. [Color System](#3-color-system)
4. [Typography and Layout](#4-typography-and-layout)
5. [Accessibility Considerations](#5-accessibility-considerations)
6. [Technology Choices](#6-technology-choices)

---

## 1. Design Philosophy

The UNICC AI Safety Lab web interface is designed around four guiding principles:

### 1.1 Institutional Professionalism

The interface must convey authority and trustworthiness appropriate for a tool used within the United Nations system. Visual design draws from Google and Apple product aesthetics — clean lines, generous whitespace, restrained color usage — while maintaining the gravitas expected in institutional contexts. There are no playful illustrations, no casual language, and no unnecessary decorative elements. Every visual element serves a functional purpose.

### 1.2 Progressive Disclosure

Users see only what they need at each stage of the workflow. The input screen is deliberately minimal: a URL field, a button, and two optional controls. Complexity is revealed progressively — first the real-time progress log during evaluation, then the full report with nested detail levels. This prevents information overload while ensuring expert users can drill into any level of detail.

### 1.3 Clarity Over Decoration

Safety evaluation results must be immediately comprehensible. The circular safety score provides an instant overall assessment. Color coding (green/orange/red) maps directly to risk severity. Verdict pills use the same vocabulary as the underlying evaluation engine (pass, safe, caution, warn, unsafe, fail) so there is no translation gap between the UI and the technical reports.

### 1.4 Zero-Configuration Operation

The interface requires no setup, no account creation, and no configuration. Users paste a GitHub URL and click Evaluate. Sensible defaults are pre-selected (critical-only test suite, public_sector domain). Advanced users can override these defaults, but the default path produces a useful result immediately.

---

## 2. Screen-by-Screen Walkthrough

The interface is a single-page application (SPA) that transitions between three screens without full page reloads. State transitions are handled by showing/hiding DOM sections via JavaScript.

### 2.1 Input Screen (Hero)

**Purpose:** Accept a GitHub repository URL and optional evaluation parameters.

**Layout:**

The screen presents a centered card on a light gray background (`#f8f9fa`). The card has a maximum width of 960 pixels and generous padding on all sides.

**Components (top to bottom):**

1. **Title Block**
   - Primary title: "UNICC AI Safety Lab" in 2rem bold weight
   - Subtitle: "AI Safety Evaluation for Content Generation Tools" in muted gray, 1rem
   - This immediately communicates what the tool does and its institutional affiliation

2. **URL Input Field**
   - Full-width rounded input (`border-radius: 12px`) with a subtle border
   - Placeholder text: "https://github.com/organization/repository"
   - Focus state: border transitions to the primary accent color
   - Validation: client-side check that URL begins with `https://github.com/`
   - Input is styled as a prominent search-box element, signaling that this is the primary interaction point

3. **Evaluate Button**
   - Full-width button with green background (`#22c55e`) and white text
   - Rounded corners matching the input field
   - Hover state: slightly darker green
   - Disabled state (while evaluating): gray background, no hover effect
   - Text: "Evaluate Repository"

4. **Options Row**
   - Displayed below the button in a horizontal flex container
   - **Full Suite Checkbox:** Labeled "Run full suite (all 25+ prompts)". Unchecked by default (the system auto-selects prompts based on detected model type). Checking this forces all prompts to run, which takes longer but provides comprehensive coverage.
   - **Domain Selector Dropdown:** Labeled "Domain Context". Options:
     - `public_sector` (default) — General UN/government context
     - `humanitarian` — Refugee, disaster response, aid contexts
     - `healthcare` — Medical and health information contexts
     - `education` — Educational content and student-facing tools
     - `internal_assistant` — Internal organizational tools

**Interaction Flow:**
1. User pastes or types a GitHub URL
2. Optionally checks "Full Suite" and/or changes domain
3. Clicks "Evaluate Repository"
4. Button disables, input locks, screen transitions to Progress view

**Error States:**
- Empty URL: button remains inactive (disabled until URL field is non-empty)
- Invalid URL (not a GitHub URL): error message appears below the input in red text

### 2.2 Progress Screen

**Purpose:** Provide real-time feedback during the evaluation pipeline, which may take several minutes.

**Layout:**

The input card transforms in place. The URL input and options are replaced by the progress interface. The card remains centered with the same width.

**Components (top to bottom):**

1. **Progress Bar**
   - Full-width horizontal bar with rounded ends
   - Background: light gray track (`#e5e7eb`)
   - Fill: green gradient, width proportional to `percent` from SSE events (0-100%)
   - Percentage label displayed to the right of the bar or centered within it
   - Transitions smoothly as percentage updates arrive

2. **Status Message**
   - Single line of bold text showing the current stage
   - Updates with each SSE progress event
   - Examples: "Cloning repository...", "Running: prompt_injection / direct_injection_jailbreak", "Generating safety reports..."

3. **Log Container**
   - Scrolling container with a fixed maximum height (400px)
   - Monospace font for log entries
   - Each entry is a single line with three parts:
     - **Timestamp:** `HH:MM:SS` in muted gray
     - **Status Indicator:** A small colored circle (8px diameter)
     - **Message:** Description of the event

4. **Log Entry Color Coding:**

   | Event Type | Indicator Color | Example Message |
   |---|---|---|
   | `progress` | Blue (#3b82f6) | `[14:32:07] Cloning repository: https://github.com/user/repo` |
   | `test_result` (pass/safe) | Green (#22c55e) | `[14:33:12] PASS: safe_baseline/informational — verdict: safe, risk: low` |
   | `test_result` (unsafe/fail) | Red (#ef4444) | `[14:33:45] FAIL: prompt_injection/direct_injection — verdict: unsafe, risk: critical` |
   | `warning` | Orange (#f59e0b) | `[14:33:22] WARNING: No output captured for encoding_bypass` |
   | `error` | Red (#ef4444) | `[14:33:50] ERROR: Failed to clone repository: URL not found` |
   | `heartbeat` | (no entry shown) | SSE keepalive, not displayed in UI |

5. **Auto-Scroll Behavior:**
   - Log container scrolls to bottom automatically as new entries arrive
   - If user manually scrolls up to review earlier entries, auto-scroll pauses
   - Resumes auto-scroll when user scrolls back to bottom

**SSE Event Flow:**

The browser connects to `/api/stream/{job_id}` using the EventSource API. Events arrive as JSON objects with `event` and `data` fields:

```
Stage 1: Cloning (0-10%)
  -> progress: "Cloning repository: {url}" (5%)
  -> progress: "Repository profiled: {name} | Language: {lang}" (10%)

Stage 2: Test Selection (10-15%)
  -> progress: "Selected {n} test prompts for model type '{type}'" (15%)

Stage 3: Testing (15-90%)
  -> progress: "[1/{total}] Running: {category} / {subcategory}" (15%)
  -> test_result: {category, subcategory, verdict, risk_level}
  -> progress: "[2/{total}] Running: ..." (18%)
  -> test_result: ...
  (repeats for each test)

Stage 4: Reporting (90-100%)
  -> progress: "Generating safety reports..." (92%)
  -> complete: {summary, category_breakdown} (100%)
```

**Transition:** When the `complete` event arrives, the screen transitions to the Report view after a brief 500ms delay.

### 2.3 Report Screen

**Purpose:** Present the complete safety evaluation results in a format that supports both quick executive review and detailed technical analysis.

**Layout:**

The report screen expands to fill more of the viewport width (up to 960px). It is organized in a vertical stack of distinct sections, each visually separated.

**Components (top to bottom):**

1. **Circular Safety Score**
   - Large circular gauge (200px diameter) centered at the top
   - The ring fill represents the pass rate percentage
   - Center text shows the percentage in large bold font (e.g., "84%")
   - Ring color follows the safety color system:
     - 80-100%: Green (`#22c55e`) — Good safety posture
     - 60-79%: Orange (`#f59e0b`) — Moderate concerns
     - 40-59%: Red (`#ef4444`) — Significant issues
     - 0-39%: Dark Red (`#991b1b`) — Critical failures
   - Below the gauge: text label "Safety Score" and the repository name

2. **Summary Cards**
   - Four cards in a horizontal flex row (wrap on narrow screens)
   - Each card: white background, rounded corners, subtle shadow
   - Card contents:
     - **Tests Run:** Total number of tests executed (e.g., "25")
     - **Pass Rate:** Percentage of passing tests (e.g., "84%")
     - **Critical Issues:** Count of critical-risk findings (e.g., "0"), styled in red if > 0
     - **Human Review:** Count of evaluations flagged for human oversight (e.g., "2"), styled in orange if > 0

3. **Category Breakdown Chart**
   - Section title: "Results by Category"
   - Horizontal bar chart with one bar per test category
   - Each bar shows the category name on the left, a stacked horizontal bar in the middle (green for pass, red for fail), and pass/total count on the right
   - Categories displayed:
     - Prompt Injection
     - Harmful Content
     - PII Leakage
     - Hate/Discrimination
     - Governance
     - Safe Baseline
   - Bars are proportional to the total tests in each category

4. **Detailed Test Results Table**
   - Section title: "Detailed Results"
   - Full-width table with columns:
     - **Category:** Test category name
     - **Subcategory:** Specific test name (e.g., "direct_injection_jailbreak")
     - **Severity:** Badge with text and background color
       - Critical: dark red background, white text
       - High: red background, white text
       - Medium: orange background, dark text
       - Low: green background, dark text
     - **Verdict:** Pill-shaped badge
       - pass/safe: green background
       - caution: yellow/amber background
       - warn: orange background
       - unsafe/fail: red background
     - **Risk Level:** Pill-shaped badge
       - low: green
       - medium: orange
       - high: red
       - critical: dark red
   - Rows are grouped by category with subtle dividers
   - Alternating row backgrounds for readability

5. **Recommendations Section**
   - Section title: "Recommendations"
   - Each recommendation displayed as a card with:
     - Left border color indicating priority:
       - Green (4px): Low priority — informational suggestions
       - Orange (4px): Medium priority — should address before deployment
       - Red (4px): High/Critical priority — must address immediately
     - Recommendation title in bold
     - Detailed remediation guidance in regular weight
   - Recommendations are generated by the governance judge based on the evaluation findings
   - Sorted by priority (critical first)

6. **AI-Generated Analysis Summary**
   - Section title: "Analysis"
   - A text block containing a synthesized narrative produced by the council:
     - Overall risk posture assessment
     - Key areas of concern with specific examples
     - Compliance status against relevant frameworks
     - Recommendations for human reviewers
   - Styled as a blockquote with a left border and slightly muted background

7. **Action Button**
   - "Evaluate Another Repository" button
   - Same styling as the original Evaluate button
   - Clicking resets the interface to the Input screen, clearing all state

---

## 3. Color System

The interface uses a deliberate, constrained color palette. Colors carry semantic meaning tied directly to safety evaluation concepts.

### 3.1 Safety Status Colors

| CSS Variable | Hex Value | Usage |
|---|---|---|
| `--safe` | `#22c55e` | Safe verdicts, passing tests, positive indicators |
| `--caution` | `#f59e0b` | Caution verdicts, medium risk, warnings |
| `--warn` | `#ef4444` | Unsafe/fail verdicts, high risk, errors |
| `--critical` | `#991b1b` | Critical risk level, severe failures |

### 3.2 UI Chrome Colors

| Purpose | Hex Value | Usage |
|---|---|---|
| Background | `#f8f9fa` | Page background |
| Card Background | `#ffffff` | Content cards |
| Text Primary | `#111827` | Headings, important text |
| Text Secondary | `#6b7280` | Descriptions, labels, timestamps |
| Border | `#e5e7eb` | Card borders, table dividers |
| Accent Blue | `#3b82f6` | Informational indicators, links |

### 3.3 Score Gauge Thresholds

| Score Range | Color | Interpretation |
|---|---|---|
| 80-100% | `#22c55e` (green) | Good safety posture. Most or all tests pass. |
| 60-79% | `#f59e0b` (orange) | Moderate concerns. Several tests flagged issues. |
| 40-59% | `#ef4444` (red) | Significant issues. Many tests detected problems. |
| 0-39% | `#991b1b` (dark red) | Critical failures. System is not safe for deployment. |

---

## 4. Typography and Layout

### 4.1 Font Stack

The interface uses the system font stack, which provides native-looking text on every platform without requiring font downloads:

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
             "Helvetica Neue", Arial, sans-serif;
```

Log entries use a monospace stack:

```css
font-family: "SF Mono", "Fira Code", "Fira Mono", "Roboto Mono",
             "Courier New", monospace;
```

### 4.2 Type Scale

| Element | Size | Weight | Color |
|---|---|---|---|
| Page title | 2rem (32px) | 700 (Bold) | `#111827` |
| Section headings | 1.5rem (24px) | 600 (Semi-Bold) | `#111827` |
| Card values | 1.75rem (28px) | 700 (Bold) | Varies by context |
| Card labels | 0.875rem (14px) | 400 (Regular) | `#6b7280` |
| Body text | 1rem (16px) | 400 (Regular) | `#111827` |
| Log entries | 0.8125rem (13px) | 400 (Regular) | Varies by event type |
| Badges/pills | 0.75rem (12px) | 600 (Semi-Bold) | White on colored background |

### 4.3 Layout System

- **Maximum content width:** 960px, centered with `margin: 0 auto`
- **Card padding:** 2rem (32px)
- **Section spacing:** 2rem (32px) margin between major sections
- **Grid:** CSS Flexbox for summary cards (4 columns, wrapping); CSS Grid is avoided for broader browser support
- **Responsive behavior:**
  - Below 768px: summary cards stack to 2 columns
  - Below 480px: summary cards stack to 1 column
  - Table becomes horizontally scrollable on narrow screens
  - Chart bars reduce font size but maintain legibility

### 4.4 Card Design

All content sections are rendered within cards:
- Background: `#ffffff`
- Border: `1px solid #e5e7eb`
- Border-radius: `12px`
- Box-shadow: `0 1px 3px rgba(0, 0, 0, 0.08)`
- Padding: `1.5rem` (24px)

---

## 5. Accessibility Considerations

### 5.1 Color Contrast

All text and background color combinations meet WCAG 2.1 AA contrast requirements (minimum 4.5:1 for normal text, 3:1 for large text):

| Combination | Contrast Ratio | Compliance |
|---|---|---|
| Dark text (`#111827`) on white (`#ffffff`) | 16.2:1 | AAA |
| Dark text (`#111827`) on light gray (`#f8f9fa`) | 14.7:1 | AAA |
| Muted text (`#6b7280`) on white (`#ffffff`) | 5.0:1 | AA |
| White text on green (`#22c55e`) | 3.1:1 | AA Large |
| White text on red (`#ef4444`) | 3.9:1 | AA Large |
| White text on dark red (`#991b1b`) | 8.5:1 | AAA |

### 5.2 Interactive States

- **Focus indicators:** All interactive elements (input, button, checkbox, select) display a visible focus ring (`outline: 2px solid #3b82f6; outline-offset: 2px`) when focused via keyboard
- **Hover states:** Buttons darken slightly on hover; table rows gain a light background tint
- **Disabled states:** Disabled buttons display reduced opacity (0.6) and change cursor to `not-allowed`

### 5.3 Screen Reader Support

- All form inputs have associated `<label>` elements
- The progress bar has `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, and `aria-valuemax` attributes
- Verdict and risk badges include `aria-label` with the full text (e.g., `aria-label="Verdict: unsafe"`)
- The circular safety score includes an `aria-label` with the numerical value
- Log entries are rendered in an `aria-live="polite"` container so screen readers announce new entries

### 5.4 Keyboard Navigation

- Tab order follows visual layout: URL input -> Full Suite checkbox -> Domain selector -> Evaluate button
- Enter key in the URL input triggers evaluation (same as clicking the button)
- Report screen table rows are not individually focusable (they are display-only)

---

## 6. Technology Choices

### 6.1 Backend: Flask

**Choice:** Flask 3.0+

**Rationale:**
- Lightweight and sufficient for a single-purpose evaluation tool
- Native SSE support via `Response` with `stream_with_context`
- Threading support for background evaluation jobs
- No complex deployment requirements (runs with `python web/app.py`)
- P2 engine is already Python, so Flask provides zero-friction integration
- No database required; evaluation state is held in-memory dicts

### 6.2 Frontend: Vanilla JavaScript

**Choice:** No framework (no React, Vue, or Angular). No build step (no Webpack, Vite, or similar).

**Rationale:**
- The interface has only three screens and five interactive elements. A framework would add complexity without proportional benefit.
- Vanilla JS `EventSource` API provides native SSE support with no polyfills required.
- No build step means the application can be deployed by copying files. This is critical for DGX Spark deployment where Node.js may not be available.
- Reduced attack surface: no npm dependencies, no supply chain concerns.
- DOM manipulation is straightforward: show/hide sections, update text content, append log entries.
- Total JavaScript is under 200 lines.

### 6.3 Real-Time Updates: Server-Sent Events (SSE)

**Choice:** SSE over WebSockets

**Rationale:**
- SSE is unidirectional (server to client), which matches the evaluation workflow exactly: the server pushes progress updates, the client only consumes them.
- SSE is simpler than WebSockets: no handshake upgrade, no ping/pong, automatic reconnection built into the EventSource API.
- SSE works over standard HTTP, which simplifies proxy and firewall configuration in institutional network environments.
- The Flask backend pushes events via `queue.Queue` per job, which is thread-safe and straightforward.

### 6.4 Styling: Inline CSS / Single Stylesheet

**Choice:** CSS within the HTML template or a single static CSS file. No CSS preprocessors (Sass, Less, etc.).

**Rationale:**
- The design system is small enough (approximately 300 lines of CSS) that a preprocessor provides no benefit.
- CSS custom properties (`--safe`, `--caution`, `--warn`, `--critical`) provide the variable system needed for the color theme.
- No build step required.
- Single-file deployment simplifies DGX Spark operations.

---

*Document prepared by Galaxy Okoro, Project 3 Manager*
*Last updated: April 2026*
