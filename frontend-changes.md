# Frontend Code Quality Tools - Changes

## Overview

Added essential code quality tools to the frontend development workflow, including automatic code formatting with Prettier and linting with ESLint.

## Files Added

### Configuration Files

1. **`frontend/package.json`** - Node.js package configuration with dev dependencies and npm scripts:
   - `npm run format` - Format all JS, CSS, and HTML files with Prettier
   - `npm run format:check` - Check formatting without making changes
   - `npm run lint` - Run ESLint on JavaScript files
   - `npm run lint:fix` - Auto-fix linting issues
   - `npm run quality` - Run both format check and lint
   - `npm run quality:fix` - Fix both formatting and linting issues

2. **`frontend/.prettierrc`** - Prettier configuration:
   - Semi-colons enabled
   - Single quotes for strings
   - 4-space indentation
   - 100 character line width
   - Trailing commas in ES5 contexts

3. **`frontend/.eslintrc.json`** - ESLint configuration:
   - Browser environment with ES2021 support
   - Recommended ESLint rules
   - Custom rules for code quality (no-var, prefer-const, eqeqeq, curly braces required)
   - `marked` library declared as global

4. **`frontend/.prettierignore`** - Files to exclude from Prettier formatting

5. **`frontend/.eslintignore`** - Files to exclude from ESLint

6. **`frontend/.gitignore`** - Git ignore file for node_modules

### Development Scripts

7. **`frontend/scripts/quality-check.sh`** - Bash script for running quality checks:
   - Run without arguments: checks formatting and linting (exits with error if issues found)
   - Run with `--fix`: automatically fixes all formatting and linting issues
   - Auto-installs dependencies if node_modules is missing

## Files Modified

- **`frontend/script.js`** - Formatted with Prettier and fixed ESLint issues:
  - Applied consistent code style (single quotes, semicolons, spacing)
  - Added curly braces to single-line if statements

- **`frontend/style.css`** - Formatted with Prettier:
  - Applied consistent indentation and spacing

- **`frontend/index.html`** - Formatted with Prettier:
  - Applied consistent indentation

## Usage

### Install Dependencies
```bash
cd frontend
npm install
```

### Check Code Quality
```bash
npm run quality
# or
./scripts/quality-check.sh
```

### Fix Code Quality Issues
```bash
npm run quality:fix
# or
./scripts/quality-check.sh --fix
```

### Individual Commands
```bash
# Format only
npm run format

# Lint only
npm run lint

# Check formatting without fixing
npm run format:check
```

## Dependencies Added

- **prettier** (^3.2.5) - Code formatter for JS, CSS, HTML
- **eslint** (^8.57.0) - JavaScript linter

---

# Frontend Changes: Dark/Light Theme Toggle

## Overview
Added a theme toggle button that allows users to switch between dark and light themes with smooth transitions and persistent preference storage.

## Files Modified

### 1. `frontend/index.html`
- Added theme toggle button element with sun/moon SVG icons
- Button is positioned in the top-right corner using fixed positioning
- Includes proper accessibility attributes (`aria-label`, `title`)
- Updated cache-busting version numbers for CSS (v11) and JS (v10)

### 2. `frontend/style.css`
**New CSS Variables for Light Theme:**
- Added `[data-theme="light"]` selector with light-appropriate colors:
  - `--background: #f8fafc` (light gray-white)
  - `--surface: #ffffff` (white)
  - `--surface-hover: #f1f5f9` (subtle gray)
  - `--text-primary: #1e293b` (dark slate)
  - `--text-secondary: #64748b` (medium slate)
  - `--border-color: #e2e8f0` (light border)
  - `--code-bg: rgba(0, 0, 0, 0.05)` (subtle code background)

**New Variables Added to Root:**
- `--code-bg` for code block backgrounds
- `--theme-toggle-bg` and `--theme-toggle-hover` for toggle button styling

**Theme Transition Animation:**
- Added smooth 0.3s transitions on `background-color`, `color`, `border-color`, and `box-shadow` for all elements

**Theme Toggle Button Styles:**
- Fixed positioning in top-right corner
- 44x44px circular button with hover/focus/active states
- Animated icon swap between sun and moon icons
- Accessible focus ring styling

### 3. `frontend/script.js`
**New Functions:**
- `initializeTheme()`: Loads saved theme from localStorage on page load (defaults to dark)
- `toggleTheme()`: Switches between dark/light themes and persists to localStorage
- `updateThemeToggleLabel()`: Updates accessibility labels based on current theme

**Event Listener:**
- Added click event listener on theme toggle button

## Features
1. **Toggle Button Design**: Circular button with sun/moon icons positioned in top-right
2. **Smooth Transitions**: All color changes animate over 0.3 seconds
3. **Persistence**: Theme preference saved to localStorage and restored on page reload
4. **Accessibility**:
   - Keyboard navigable (focusable button)
   - Dynamic aria-label and title attributes
   - Visible focus ring
5. **Both themes maintain**: Good contrast ratios, visual hierarchy, and design language

## Usage
Click the toggle button in the top-right corner to switch between themes. The preference is automatically saved and will be remembered on future visits.
