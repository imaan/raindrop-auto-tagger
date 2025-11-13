# Contributing to Raindrop Auto-Tagger

Thank you for your interest in contributing to Raindrop Auto-Tagger! We welcome contributions from the community to make this tool even better.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing opinions and experiences

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/raindrop-auto-tagger.git
   cd raindrop-auto-tagger
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 📋 How to Contribute

### Reporting Bugs

- Check if the bug has already been reported in [Issues](https://github.com/yourusername/raindrop-auto-tagger/issues)
- If not, create a new issue with:
  - Clear, descriptive title
  - Steps to reproduce
  - Expected vs actual behavior
  - System information (OS, Python version)
  - Relevant logs (with sensitive data redacted)

### Suggesting Features

- Check existing [Issues](https://github.com/yourusername/raindrop-auto-tagger/issues) and [Discussions](https://github.com/yourusername/raindrop-auto-tagger/discussions)
- Open a discussion for major features
- For smaller features, create an issue with:
  - Use case description
  - Proposed implementation
  - Potential impacts

### Submitting Code

1. **Follow the coding standards**:
   - Python PEP 8 style guide
   - Type hints for function parameters
   - Docstrings for classes and functions
   - Comments for complex logic

2. **Write tests** for new features:
   ```python
   def test_your_feature():
       """Test description"""
       assert your_function() == expected_result
   ```

3. **Update documentation**:
   - README.md for user-facing changes
   - Code comments for implementation details
   - API documentation for new functions

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

   Follow conventional commits:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `style:` Code style
   - `refactor:` Code refactoring
   - `test:` Testing
   - `chore:` Maintenance

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe what changes you made and why
   - Include screenshots if relevant

## 🎯 Priority Areas

We especially welcome contributions in these areas:

### High Priority
- **MCP Server Development**: Help build the Claude Desktop integration
- **Multi-language Support**: Improve handling of non-English bookmarks
- **Testing Suite**: Add comprehensive unit and integration tests

### Medium Priority
- **Categorization Improvements**: Better prompts and tag logic
- **Performance Optimization**: Faster processing, better batching
- **Error Recovery**: More robust error handling

### Nice to Have
- **UI/Dashboard**: Web interface for configuration
- **Analytics**: Bookmark statistics and insights
- **Export Features**: Various export formats

## 🧪 Testing

Before submitting a PR:

1. **Run the existing tests**:
   ```bash
   python -m pytest tests/
   ```

2. **Test your changes locally**:
   ```bash
   # Dry run mode
   python raindrop_auto_tagger.py --dry-run
   ```

3. **Check code quality**:
   ```bash
   # Linting
   pylint raindrop_auto_tagger.py

   # Type checking
   mypy raindrop_auto_tagger.py
   ```

## 📚 Resources

### Understanding the Codebase

- `raindrop_auto_tagger.py`: Main application logic
- `.github/workflows/`: GitHub Actions automation
- `README.md`: User documentation
- `requirements.txt`: Python dependencies

### Key Concepts

- **Raindrop.io API**: [Documentation](https://developer.raindrop.io/)
- **Claude API**: [Anthropic Docs](https://docs.anthropic.com/)
- **MCP Protocol**: [Model Context Protocol](https://github.com/anthropics/mcp)

### Development Tools

- Python 3.9+
- GitHub Actions for CI/CD
- pytest for testing
- Black for code formatting

## 🤔 Questions?

- Open a [Discussion](https://github.com/yourusername/raindrop-auto-tagger/discussions)
- Join our community chat (coming soon)
- Check the [FAQ](https://github.com/yourusername/raindrop-auto-tagger/wiki/FAQ)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make Raindrop Auto-Tagger better for everyone! 🎉