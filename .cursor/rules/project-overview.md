# Global Project Rules: Stock Insight App

## Project Overview
You are building a financial stock analysis platform. The goal is to provide daily, weekly, and monthly insights using AI.

## Project Structure
- /frontend: Next.js (Client & UI)
- /backend: FastAPI (Data Processing & AI Logic)

## Communication Protocol
- Frontend and Backend communicate via JSON REST API.
- All API endpoints must be documented in the backend using FastAPI's Swagger (OpenAPI).

## Future Improvements Documentation

### ⚠️ MANDATORY: Document All Ideas

**For EVERY request, feature, or idea:**

1. **Add to FUTURE_IMPROVEMENTS.md**:
   - Every feature request should be documented
   - Every improvement idea should be added
   - Every "nice to have" should be recorded
   - Every technical debt item should be noted

2. **When to Add**:
   - When user requests a new feature
   - When you identify an improvement opportunity
   - When discussing future enhancements
   - When encountering technical limitations
   - When suggesting optimizations

3. **How to Add**:
   - Categorize by section (Backend, Frontend, Infrastructure, etc.)
   - Use checkboxes `- [ ]` for tracking
   - Add priority markers `[HIGH]`, `[MEDIUM]`, `[LOW]` if applicable
   - Include brief description of the idea
   - Link to related issues or discussions if available

4. **File Location**: `/FUTURE_IMPROVEMENTS.md` (root directory)

**Example**:
```markdown
### Features
- [ ] Add stock watchlist functionality [HIGH]
- [ ] Implement stock price alerts (email/push notifications) [MEDIUM]
```

**DO NOT skip documenting ideas - even if they seem obvious or minor!**

## File Structure & Organization

### ⚠️ MANDATORY: Follow Project Structure Standards

**When creating ANY new file:**

1. **Check existing structure** - Look for similar files to understand organization patterns
2. **Follow directory conventions** - Place files in appropriate directories
3. **Use consistent naming** - Follow existing naming patterns
4. **Update documentation** - Add references to new files in relevant docs

### Project Structure Standards

```
learnCursor/
├── README.md                    # Main project README
├── FUTURE_IMPROVEMENTS.md      # All ideas and improvements
├── docs/                        # All documentation
│   ├── setup/                  # Setup and installation guides
│   ├── guides/                 # Development guides
│   ├── testing/                # Testing documentation
│   ├── features/               # Feature completion docs
│   └── design-docs/            # Design documents
├── frontend/                    # Frontend application
│   ├── app/                    # Next.js App Router
│   ├── components/             # React components
│   ├── lib/                    # Utilities and API clients
│   ├── __tests__/              # Unit and integration tests
│   └── e2e/                    # E2E tests
├── backend/                     # Backend application
│   ├── app/                    # Application code
│   ├── tests/                  # Test suite
│   └── alembic/                # Database migrations
└── .cursor/                     # Cursor AI rules
    └── rules/                   # Project rules and guidelines
```

### File Naming Conventions

- **Documentation**: `UPPERCASE_WITH_UNDERSCORES.md` (e.g., `QUICK_START.md`)
- **Code files**: Follow language conventions (e.g., `stock_service.py`, `StockCard.tsx`)
- **Test files**: `test_*.py` (backend) or `*.test.tsx` (frontend)
- **Config files**: `.filename` or `filename.config.js`
- **Language-specific configs**: Place in respective directories
  - `pyrightconfig.json` → `backend/` (Python type checking)
  - `tsconfig.json` → `frontend/` (TypeScript config)
  - `pyproject.toml` → `backend/` (Python project config)

### Documentation File Placement

- **Setup guides** → `docs/setup/`
- **Testing docs** → `docs/testing/`
- **Feature docs** → `docs/features/`
- **Design docs** → `docs/design-docs/`
- **Main README** → Root directory
- **Future improvements** → Root directory (`FUTURE_IMPROVEMENTS.md`)

### Configuration File Placement

- **Python configs** (`pyrightconfig.json`, `pyproject.toml`) → `backend/`
- **TypeScript configs** (`tsconfig.json`) → `frontend/`
- **IDE configs** (`.vscode/settings.json`) → Root directory (workspace-level)
- **Root-level configs** (`.gitignore`) → Root directory
- **Setup scripts** (`.sh` files) → `scripts/` directory

### Before Creating New Files

1. **Search for similar files** - Check if similar functionality exists
2. **Check directory structure** - Ensure file goes in the right place
3. **Review naming patterns** - Follow existing conventions
4. **Update documentation** - Add references in relevant docs
5. **Update FUTURE_IMPROVEMENTS.md** - If it's a new feature/idea

### File Organization Checklist

When adding a new file:
- [ ] File is in the correct directory
- [ ] File name follows naming conventions
- [ ] Related documentation is updated
- [ ] Cross-references are added
- [ ] FUTURE_IMPROVEMENTS.md is updated (if applicable)
