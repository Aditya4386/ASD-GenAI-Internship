# Contributing to VeriMind

Thank you for your interest in contributing to VeriMind! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive criticism
- Respect differing opinions

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key (for LLM features)

### Development Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/yourusername/verimind.git
cd verimind
```

2. **Backend setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

3. **Frontend setup**
```bash
cd frontend
npm install
```

4. **Run development servers**
```bash
# Terminal 1 - Backend
cd backend && python main.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```

## How to Contribute

### Reporting Bugs
1. Check existing issues first
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python/Node versions)
   - Screenshots if applicable

### Suggesting Features
1. Check existing issues and discussions
2. Create a feature request with:
   - Clear use case
   - Proposed solution
   - Alternative solutions considered
   - Any relevant mockups or diagrams

### Pull Request Process

1. **Create a branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

2. **Make changes**
- Follow code style guidelines
- Add tests for new functionality
- Update documentation as needed

3. **Run tests**
```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && npm run test
```

4. **Commit with clear messages**
```bash
git commit -m "feat: add new verification agent for fact-checking"
# or
git commit -m "fix: resolve TF-IDF retrieval issue with special characters"
```

5. **Push and create PR**
```bash
git push origin feature/your-feature-name
```

### Commit Message Convention
We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8
- Use type hints
- Max line length: 100 characters
- Use `black` for formatting
- Use `isort` for import sorting

```bash
# Format code
black .
isort .
```

### JavaScript/React (Frontend)
- Use ESLint + Prettier
- Functional components with hooks
- Descriptive component/file names
- JSDoc for complex functions

```bash
# Format code
npm run lint:fix
```

### Testing
- Write unit tests for new agents
- Add integration tests for API endpoints
- Test edge cases (empty docs, malformed input, etc.)

## Architecture Guidelines

### Adding New Agents
1. Create agent in `backend/agents/`
2. Extend `BaseAgent`
3. Add to `backend/agents/__init__.py`
4. Register in `backend/agents/graph.py`
5. Add tests in `backend/tests/agents/`

### Modifying RAG Pipeline
1. Update `backend/rag/processor.py`
2. Maintain backward compatibility
3. Document new parameters
4. Add retrieval benchmarks

## Documentation
- Update README.md for user-facing changes
- Update docstrings for code changes
- Add API docs in OpenAPI/Swagger format
- Create diagrams for architecture changes (Mermaid/PlantUML)

## Release Process
1. Version bump in `pyproject.toml` / `package.json`
2. Update CHANGELOG.md
3. Create release tag
4. GitHub Actions builds and publishes

## Questions?
- Open a Discussion on GitHub
- Check existing documentation
- Review related issues/PRs

Thank you for contributing! 🎉