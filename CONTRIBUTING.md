# Contributing to StyleTTS2 Dataset Toolkit

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

---

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please open an issue using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, GPU, etc.)
- Error messages or logs

### Suggesting Features

Have an idea for a new feature? Open an issue using the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:

- Clear description of the feature
- Use case and motivation
- Proposed implementation (if you have ideas)

### Submitting Pull Requests

1. **Fork the repository** and clone your fork
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the code style guidelines
4. **Test your changes** to ensure they work correctly
5. **Commit your changes** with clear, descriptive messages
6. **Push to your fork** and open a Pull Request

---

## 📋 Development Setup

### Prerequisites

- Windows 10/11
- Python 3.10 or 3.11
- Git
- NVIDIA GPU with CUDA support (for GPU features)

### Setup Steps

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/Lostenergydrink/styletts2-dataset-toolkit.git
   cd styletts2-dataset-toolkit
   ```

2. **Set up stem-separation environment:**
   ```powershell
   cd stem-separation
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   pip install -r requirements.txt
   ```

3. **Set up styletts2-setup environment:**
   ```powershell
   cd ..\styletts2-setup
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   pip install styletts2 gradio openai-whisper pydub librosa soundfile
   ```

---

## 📝 Code Style Guidelines

### Python Code

- Follow PEP 8 style guide
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Add comments for complex logic

### Commit Messages

Use clear, descriptive commit messages:

**Good:**
```
Fix: Make FFmpeg path configurable via environment variable
Add: Support for custom cache directory in launcher
Update: Documentation for path configuration
```

**Bad:**
```
fix stuff
updates
changes
```

### File Organization

- Keep related code together
- Separate concerns (UI, processing, utilities)
- Use appropriate file names (descriptive, lowercase with underscores)

---

## 🧪 Testing

Before submitting a PR, please:

1. **Test your changes** on Windows 10/11
2. **Verify launchers work** with your changes
3. **Test with different configurations** (custom paths, etc.)
4. **Check for errors** in console output
5. **Verify documentation** is updated if needed

### Manual Testing Checklist

- [ ] Launcher scripts work correctly
- [ ] Path configuration works as expected
- [ ] Error handling works properly
- [ ] Documentation is clear and accurate
- [ ] No hardcoded paths or user-specific values

---

## 📚 Documentation

### When to Update Documentation

- Adding new features → Update README.md and relevant guides
- Changing behavior → Update affected documentation
- Fixing bugs → Update troubleshooting guide if relevant
- Adding configuration → Update path configuration guide

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Add screenshots for UI changes (if applicable)
- Keep formatting consistent with existing docs

---

## 🔍 Pull Request Process

### Before Submitting

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Ensure your code:**
   - Follows style guidelines
   - Has no hardcoded paths
   - Includes error handling
   - Is tested and working

3. **Update documentation** if your changes affect:
   - Installation process
   - Configuration options
   - Usage instructions
   - Troubleshooting

### PR Checklist

When opening a PR, please ensure:

- [ ] Code follows style guidelines
- [ ] Changes are tested and working
- [ ] Documentation is updated (if needed)
- [ ] Commit messages are clear
- [ ] No hardcoded paths or user-specific values
- [ ] Error handling is present
- [ ] PR description explains the changes

### Review Process

- Maintainers will review your PR
- Feedback may be requested
- Changes may be requested before merging
- All PRs require approval before merging

---

## 🐛 Bug Fixes

When fixing bugs:

1. **Identify the root cause** - don't just patch symptoms
2. **Add error handling** if missing
3. **Update tests** if applicable
4. **Document the fix** in commit message
5. **Update troubleshooting guide** if it's a common issue

---

## ✨ Feature Additions

When adding features:

1. **Discuss first** - open an issue to discuss the feature
2. **Keep it focused** - one feature per PR
3. **Update documentation** - README, guides, etc.
4. **Add examples** - show how to use the feature
5. **Consider backward compatibility** - don't break existing functionality

---

## 📦 Dependencies

### Adding New Dependencies

- **Justify the addition** - explain why it's needed
- **Check compatibility** - ensure it works with existing dependencies
- **Update requirements.txt** - add with version constraints
- **Document usage** - explain how to use the new dependency

### Updating Dependencies

- **Test thoroughly** - ensure updates don't break functionality
- **Update version constraints** in requirements.txt
- **Document breaking changes** if any

---

## 🚫 What Not to Commit

- ❌ Hardcoded paths (use environment variables or config)
- ❌ User-specific values
- ❌ API keys or secrets
- ❌ Large files (models, datasets, outputs)
- ❌ Temporary files
- ❌ IDE-specific files (already in .gitignore)

---

## 💡 Tips for Contributors

1. **Start small** - fix typos, improve documentation, add examples
2. **Ask questions** - open an issue if you're unsure
3. **Be patient** - maintainers are volunteers
4. **Be respectful** - follow the code of conduct
5. **Test thoroughly** - ensure your changes work

---

## 📞 Getting Help

- **Open an issue** for bugs or questions
- **Check documentation** in `docs/` directory
- **Review existing issues** to see if your question was answered

---

## 🙏 Thank You!

Your contributions make this project better for everyone. Thank you for taking the time to contribute!

---

**Last Updated:** 2025-01-27








