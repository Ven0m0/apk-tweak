# Development Guidelines

Critical information for working with this codebase. Follow these guidelines precisely.

## Package Management

## **ONLY use uv, NEVER pip**

```bash
uv add package              # Install package
uv add --dev package        # Install dev package
uv run tool                 # Run tool
uv add package --upgrade-package package  # Upgrade package
```

**FORBIDDEN**: `uv pip install`, `@latest` syntax

## Code Quality

### Type Checking
- Type hints required for all code
- Run `pyrefly init` to initialize
- Run `pyrefly check` after every change and fix resulting errors
- Explicit None checks for Optional types
- Type narrowing for strings
- Version warnings can be ignored if checks pass

### Code Standards
- Line length: 88 chars maximum
- Public APIs must have docstrings
- Functions must be focused and small
- Follow existing patterns exactly

### Naming Conventions (PEP 8)
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Handlers: prefix with `handle_`

### Formatting
- Use f-strings for string formatting
- Use Ruff for code formatting

## Testing

```bash
uv run pytest               # Run tests
```

- Framework: pytest with anyio (NOT asyncio) for async tests
- Coverage: test edge cases and errors
- New features require tests
- Bug fixes require regression tests
- Test frequently with realistic inputs

## Development Philosophy

Core principles in order of priority:

1. **Simplicity**: Write straightforward code, avoid clever solutions
2. **Readability**: Make code easy to understand
3. **Less Code = Less Debt**: Minimize code footprint
4. **Maintainability**: Write code that's easy to update
5. **Testability**: Ensure code is testable
6. **Performance**: Consider performance without sacrificing readability

## Best Practices

### Code Organization
- Early returns to avoid nested conditions
- Define composing functions before their components
- Keep core logic clean, push implementation details to edges
- Balance file organization with simplicity
- Keep files to a minimum (this is a simple chatbot)

### Coding Style
- DRY (Don't Repeat Yourself)
- Use constants over functions where possible
- Prefer functional, immutable approaches when clear
- Only modify code related to the task
- Mark issues with `TODO:` prefix

### Iterative Development
1. Start with minimal functionality
2. Verify it works before adding complexity
3. Test frequently with realistic inputs
4. Create test environments for hard-to-validate components

## System Architecture

- Use Pydantic and LangChain
- This is a simple chatbot - keep minimal files
- Use context7 MCP to check library details

## Git Workflow

### Branch Strategy
- Always use feature branches, never commit directly to `main`
- Branch naming: `fix/auth-timeout`, `feat/api-pagination`, `chore/ruff-fixes`
- One logical change per branch

### Commit Practices
- Atomic commits (one logical change per commit)
- Conventional commit style: `type(scope): short description`
- Examples: `feat(eval): group logs per test`, `fix(cli): handle missing key`
- Keep granular history on feature branch, squash when merging to `main`

### Pull Requests
- Open draft PR early for visibility
- Convert to ready when complete and tests pass
- Create detailed PR description focusing on:
  - High-level problem description
  - How it's solved
  - Avoid code specifics unless they add clarity

### Issue Linking
- Reference existing issue or create one before starting
- Use `Fixes #123` in commit/PR messages for auto-linking

### Workflow Steps
1. Create or reference an issue
2. `git checkout -b feat/issue-123-description`
3. Commit in small, logical increments
4. `git push` and open draft PR early
5. Convert to ready when functionally complete and tests pass
6. Merge after reviews and checks pass

## Code Formatting & Linting

### Ruff
```bash
uv run ruff format .        # Format code
uv run ruff check .         # Check for issues
uv run ruff check . --fix   # Auto-fix issues
```

**Critical issues**:
- Line length (88 chars)
- Import sorting (I001)
- Unused imports

**Line wrapping**:
- Strings: use parentheses
- Function calls: multi-line with proper indent
- Imports: split into multiple lines

## Error Resolution

### CI Failure Fix Order
1. Formatting (`ruff format`)
2. Type errors (`pyrefly check`)
3. Linting (`ruff check`)

### Common Issues

**Line Length**:
- Break strings with parentheses
- Multi-line function calls
- Split imports

**Type Errors**:
- Get full line context
- Check Optional types
- Add type narrowing
- Verify function signatures
- Add explicit None checks
- Narrow string types
- Match existing patterns

### Pre-Commit Checklist
- [ ] Check git status
- [ ] Run formatters before type checks
- [ ] Keep changes minimal
- [ ] Follow existing patterns
- [ ] Document public APIs
- [ ] Test thoroughly
