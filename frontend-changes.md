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
