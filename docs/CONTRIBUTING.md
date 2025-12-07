# Contributing to Weaver

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Git
- A code editor (VS Code, PyCharm, etc.)

### Development Setup

1. **Fork the repository**

   Click the "Fork" button on GitHub to create your own copy of the repository.

2. **Clone your fork**

   ```bash
   git clone https://github.com/sherkevin/Weaver.git
   cd Weaver
   ```

3. **Add upstream remote**

   ```bash
   git remote add upstream https://github.com/originalowner/Weaver.git
   ```

4. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**

   ```bash
   pip install -r src/requirements.txt
   ```

## 📝 Development Workflow

### 1. Create a Branch

Create a feature branch from `main`:

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or updates

### 2. Make Changes

- Write clean, readable code
- Follow existing code style and conventions
- Add comments for complex logic
- Update documentation as needed
- Add tests for new features

### 3. Commit Changes

Write clear, descriptive commit messages:

```bash
git commit -m "Add feature: description of what was added"
```

Commit message format:
- Use present tense ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Add detailed description if needed

### 4. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 5. Create a Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template
5. Submit the PR

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Code follows the project's style guidelines
- [ ] All tests pass (if applicable)
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts with main branch

### PR Template

When creating a PR, please include:

- **Description**: What changes were made and why
- **Type**: Feature, Bug Fix, Documentation, etc.
- **Testing**: How the changes were tested
- **Screenshots**: If applicable (for UI changes)
- **Checklist**: Confirm all items are completed

### Review Process

- PRs will be reviewed by maintainers
- Address review comments promptly
- Be open to feedback and suggestions
- Keep discussions respectful and constructive

## 🎨 Code Style

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Example

```python
from typing import Dict, List, Optional

def process_workflow(
    workflow_name: str,
    config: Optional[Dict[str, any]] = None
) -> Dict[str, any]:
    """
    Process a workflow with the given name and configuration.
    
    Args:
        workflow_name: Name of the workflow to process
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing workflow execution results
    """
    # Implementation here
    pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_workflow.py

# Run with coverage
pytest --cov=src tests/
```

### Writing Tests

- Write tests for new features
- Aim for good test coverage
- Use descriptive test names
- Test both success and failure cases

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints in function signatures

### Example

```python
def create_agent(
    agent_name: str,
    agent_type: str = "coder"
) -> Agent:
    """
    Create an agent instance.
    
    Args:
        agent_name: Unique name for the agent
        agent_type: Type of agent (coder, architect, etc.)
        
    Returns:
        Agent instance
        
    Raises:
        ValueError: If agent_type is invalid
    """
    pass
```

### Updating README

- Keep README.md up to date with new features
- Update examples when APIs change
- Add new sections as needed

## 🐛 Reporting Bugs

### Before Reporting

1. Check existing issues to avoid duplicates
2. Verify the bug exists in the latest version
3. Try to reproduce the bug

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.0]
- Framework version: [e.g., 2.0.0]

**Additional context**
Any other relevant information.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Any other relevant information.
```

## 🏗️ Project Structure

Understanding the project structure helps with contributions:

```
src/
├── core/          # Core workflow components
├── engines/        # Execution engines
├── services/       # Service layer
├── workflows/      # Workflow definitions
├── config/         # Configuration management
└── diagnostics/    # Logging and error handling
```

## 📞 Getting Help

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Email**: Contact maintainers directly if needed

## 🙏 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing! 🎉

