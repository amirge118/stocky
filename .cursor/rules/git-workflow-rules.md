# Git Workflow Rules: Version Control Standards

## Git Workflow Strategy

### 1. Branching Strategy
- **main/master**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature branches (`feature/add-stock-search`)
- **bugfix/**: Bug fix branches (`bugfix/fix-price-calculation`)
- **hotfix/**: Critical production fixes (`hotfix/security-patch`)

### 2. Branch Naming Conventions
```
feature/{description}
bugfix/{description}
hotfix/{description}
refactor/{description}
docs/{description}
test/{description}
```

**Examples:**
- `feature/add-stock-chart`
- `bugfix/fix-api-error-handling`
- `hotfix/fix-authentication-bug`
- `refactor/restructure-api-routes`

## Commit Message Standards

### 3. Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**
```
feat(stocks): add stock search functionality

Implement stock search with autocomplete and filtering.
Add debounce to prevent excessive API calls.

Closes #123
```

```
fix(api): handle null stock prices gracefully

Return default value of 0.00 when stock price is null
instead of throwing error.

Fixes #456
```

### 4. Commit Message Rules
- **Subject**: Use imperative mood ("add" not "added" or "adds")
- **Length**: Keep subject under 50 characters
- **Body**: Explain what and why, not how
- **Reference Issues**: Reference issues/PRs in footer
- **Breaking Changes**: Mark with `BREAKING CHANGE:` in footer

## Pull Request Process

### 5. PR Creation Rules
- **Small PRs**: Keep PRs small and focused (one feature/fix per PR)
- **Description**: Write clear PR description with:
  - What changes were made
  - Why the changes were made
  - How to test the changes
  - Screenshots (for UI changes)
- **Linked Issues**: Link related issues
- **Draft PRs**: Use draft PRs for work in progress

### 6. PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### 7. PR Review Process
- **Self-Review**: Review your own PR before requesting review
- **Request Reviewers**: Request at least one reviewer
- **Address Feedback**: Address all review comments
- **Update PR**: Keep PR up to date with base branch
- **Squash Commits**: Squash commits before merging (if required)

## Code Review Guidelines

### 8. Review Checklist
- **Functionality**: Does the code work as intended?
- **Code Quality**: Is the code clean and maintainable?
- **Tests**: Are there adequate tests?
- **Documentation**: Is code documented?
- **Performance**: Are there performance concerns?
- **Security**: Are there security issues?
- **Standards**: Does it follow project standards?

### 9. Review Comments
- **Be Constructive**: Provide constructive feedback
- **Be Specific**: Point to specific lines and suggest improvements
- **Be Respectful**: Maintain professional tone
- **Explain Why**: Explain why changes are needed

## Git Best Practices

### 10. Commit Frequency
- **Small Commits**: Make small, logical commits
- **Atomic Commits**: Each commit should be a complete, working change
- **Frequent Commits**: Commit often, push regularly
- **Before Break**: Commit before taking a break

### 11. Commit Content
- **One Concern**: Each commit should address one concern
- **Working Code**: Only commit working code
- **No Debug Code**: Don't commit debug code or commented-out code
- **No Secrets**: Never commit secrets, API keys, or credentials

### 12. .gitignore Rules
```
# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
env/

# Environment variables
.env
.env.local
.env.*.local

# Build outputs
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Testing
.coverage
.pytest_cache/
```

## Merge Strategies

### 13. Merge Methods
- **Squash and Merge**: For feature branches (clean history)
- **Merge Commit**: For important branches (preserve history)
- **Rebase and Merge**: For linear history (use carefully)

### 14. Before Merging
- **All Tests Pass**: Ensure all CI tests pass
- **Approvals**: Get required approvals
- **Conflicts Resolved**: Resolve all merge conflicts
- **Up to Date**: Keep branch up to date with base branch

## Release Management

### 15. Versioning (Semantic Versioning)
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### 16. Release Process
1. Create release branch from `main`
2. Update version numbers
3. Update CHANGELOG.md
4. Create release PR
5. Merge to `main`
6. Tag release (`v1.2.3`)
7. Deploy to production

## Git Hooks

### 17. Pre-commit Hooks
```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run linters
npm run lint
python -m flake8 app/

# Run tests
npm test
pytest tests/unit/

# Check for secrets
git-secrets scan
```

### 18. Commit-msg Hook
```bash
#!/bin/sh
# .git/hooks/commit-msg

# Validate commit message format
commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|ci)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format!"
    echo "Format: <type>(<scope>): <subject>"
    exit 1
fi
```

## Conflict Resolution

### 19. Handling Conflicts
- **Update Base**: Keep branch up to date with base branch
- **Resolve Early**: Resolve conflicts as soon as possible
- **Understand Changes**: Understand both sides of conflict
- **Test After**: Test thoroughly after resolving conflicts

### 20. Rebase vs Merge
- **Rebase**: For cleaner history (use on feature branches)
- **Merge**: For preserving history (use on shared branches)
- **Never Rebase**: Never rebase shared/public branches

## Key Rules Summary

1. **Use** descriptive branch names
2. **Write** clear commit messages
3. **Keep** PRs small and focused
4. **Review** code thoroughly
5. **Test** before committing
6. **Never** commit secrets
7. **Keep** branches up to date
8. **Squash** commits when merging features
9. **Follow** semantic versioning
10. **Resolve** conflicts promptly
