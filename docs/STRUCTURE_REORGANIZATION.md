# Documentation Structure Reorganization

## Summary

All setup and documentation files have been reorganized into a cleaner, more logical structure.

## Before

```
stocky/
├── README.md
├── ARCHITECTURE_SETUP.md          # Setup doc
├── START_DEVELOPMENT.md            # Setup doc
├── ENV_SETUP.md                    # Setup doc
├── RUN_SERVERS.md                  # Setup doc
├── QUICK_START.md                  # Setup doc
├── STOCK_FEATURE_COMPLETE.md       # Feature doc
├── TESTING_SUMMARY.md              # Testing doc
├── TESTING_WORKFLOW.md             # Testing doc
├── WHY_TESTS_MISSED.md            # Testing doc
├── FUTURE_IMPROVEMENTS.md         # Planning doc
└── rules/
    └── tech-preferences copy 2.md  # Duplicate file
```

**Issues:**
- All files in root directory
- No clear organization
- Hard to find related documentation
- Duplicate/orphaned files

## After

```
stocky/
├── README.md                       # Main project README
├── FUTURE_IMPROVEMENTS.md          # Planning (stays in root)
├── PROJECT_STRUCTURE.md            # Structure guide (new)
├── docs/                           # All documentation organized
│   ├── README.md                   # Documentation index
│   ├── setup/                      # Setup & installation guides
│   │   ├── README.md               # Setup index
│   │   ├── QUICK_START.md
│   │   ├── ENV_SETUP.md
│   │   ├── RUN_SERVERS.md
│   │   ├── ARCHITECTURE_SETUP.md
│   │   └── START_DEVELOPMENT.md
│   ├── testing/                    # Testing documentation
│   │   ├── README.md               # Testing index
│   │   ├── TESTING_WORKFLOW.md
│   │   ├── TESTING_SUMMARY.md
│   │   └── WHY_TESTS_MISSED.md
│   ├── features/                   # Feature documentation
│   │   ├── README.md               # Features index
│   │   └── STOCK_FEATURE_COMPLETE.md
│   └── design-docs/                # Design documents (existing)
│       └── 001-stock-insight-app-overview.md
└── scripts/                      # Utility scripts
    ├── setup.sh
    └── setup-database-and-run.sh
```

**Improvements:**
- ✅ Clear categorization by purpose
- ✅ Easy navigation with README files in each directory
- ✅ Related docs grouped together
- ✅ Clean root directory
- ✅ Duplicate files removed

## File Organization Rules

### Root Directory
- `README.md` - Main project README
- `FUTURE_IMPROVEMENTS.md` - Planning document
- `PROJECT_STRUCTURE.md` - Structure guide
- Setup scripts (`.sh` files)

### Documentation Directories

**`docs/setup/`** - Setup & Installation
- Quick start guides
- Environment configuration
- Server management
- Architecture overview
- Development setup

**`docs/testing/`** - Testing Documentation
- Testing workflows
- Test summaries
- Testing analysis

**`docs/features/`** - Feature Documentation
- Completed feature docs
- Implementation summaries

**`docs/design-docs/`** - Design Documents
- Architecture decisions
- Feature designs
- System designs

## Navigation

Each directory has a `README.md` that:
- Lists all files in that directory
- Provides quick navigation
- Explains the purpose of each file
- Links to related documentation

## Updated References

All internal links have been updated:
- ✅ `README.md` - Updated documentation links
- ✅ `docs/setup/QUICK_START.md` - Fixed relative links
- ✅ `docs/testing/README.md` - Fixed relative links
- ✅ `docs/testing/TESTING_SUMMARY.md` - Fixed links
- ✅ `docs/testing/WHY_TESTS_MISSED.md` - Fixed links

## Rules Added

### File Structure Rules
Added to `.cursor/rules/project-overview.md`:
- Mandatory file structure standards
- Directory conventions
- Naming conventions
- File placement guidelines
- Checklist for adding new files

### Backend Rules
Added to `backend/.cursorrules`:
- File structure requirements
- Directory conventions
- Naming patterns

### Frontend Rules
Added to `frontend/.cursorrules`:
- File structure requirements
- Directory conventions
- Naming patterns

## Benefits

1. **Better Organization** - Related files grouped together
2. **Easier Navigation** - README files guide users
3. **Cleaner Root** - Only essential files in root
4. **Scalability** - Easy to add new documentation
5. **Consistency** - Clear rules for future files

## Future Files

When adding new documentation:
1. Place in appropriate `docs/` subdirectory
2. Update the directory's `README.md`
3. Update main `docs/README.md` if needed
4. Follow naming conventions
5. Add cross-references
