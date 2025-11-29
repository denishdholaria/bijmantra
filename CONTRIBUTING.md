# Contributing to Bijmantra

First off, thank you for considering contributing to Bijmantra! 🌱

It's people like you that make Bijmantra such a great tool for the plant breeding community.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Describe the behavior you observed and what you expected**
- **Include screenshots if relevant**
- **Include your environment details** (OS, browser, versions)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List any similar features in other tools**

### Pull Requests

- Fill in the required template
- Follow the coding style (see below)
- Include tests when adding features
- Update documentation as needed
- End all files with a newline

## Development Process

1. **Fork the repo** and create your branch from `develop`
2. **Make your changes** following our coding standards
3. **Add tests** if you've added code that should be tested
4. **Ensure the test suite passes** (`make test`)
5. **Make sure your code lints** (`make lint`)
6. **Format your code** (`make format`)
7. **Commit your changes** using conventional commits
8. **Push to your fork** and submit a pull request

### Branch Naming Convention

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new BrAPI endpoint for trials
fix: resolve authentication issue
docs: update README with installation steps
test: add tests for programs endpoint
chore: update dependencies
```

## Coding Standards

### Backend (Python)

- Follow PEP 8
- Use type hints
- Write docstrings for all functions/classes
- Use `ruff` for linting and formatting
- Maximum line length: 100 characters

### Frontend (TypeScript/React)

- Follow ESLint configuration
- Use TypeScript for type safety
- Write JSDoc comments for complex functions
- Use functional components with hooks
- Maximum line length: 100 characters

### General

- Write clear, self-documenting code
- Add comments for complex logic
- Keep functions small and focused
- Follow DRY (Don't Repeat Yourself)
- Write tests for new features

## Testing

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run test`
- All tests: `make test`

## Documentation

- Update README.md if needed
- Add/update API documentation
- Include code examples
- Keep documentation in sync with code

## Community

- Be respectful and inclusive
- Help others when you can
- Share your knowledge
- Give constructive feedback

## Questions?

Feel free to open an issue with the `question` label or start a discussion in GitHub Discussions.

## Recognition

Contributors will be recognized in our README and release notes.

---

**Thank you for contributing to Bijmantra!** 🙏

**Jay Shree Ganeshay Namo Namah!**
