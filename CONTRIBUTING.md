
# 🤝 Contribution Guide

Thank you for your interest in contributing to **NMEA Tracker Server**! This guide will help you understand how to participate in the development of the project.


## 🌟 Types of Contributions

We welcome all types of contributions:

- 🐛 **Bug reports** and fixes
- ✨ **New features** and improvements
- 📚 **Documentation** and translations
- 🧪 **Tests** and validation
- 🎨 **User interface** and design
- 🔧 **Optimizations** and refactoring


## 🚀 Quick Start

### 1. Fork and Clone

```bash
# Fork the repository on GitHub then:
git clone https://github.com/YOUR_USERNAME/nmea-tracker-server.git
cd nmea-tracker-server
```

### 2. Set Up the Environment

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Test Everything Works

```bash
python nmea_server.py
# Open https://localhost:5000/config.html
```


## 📋 Contribution Process

### 1. Create an Issue (Recommended)

Before starting, [create an issue](https://github.com/YOUR_USERNAME/nmea-tracker-server/issues/new) to:

- 🐛 Report a bug
- 💡 Propose a feature
- 🤔 Ask a question

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```


### 3. Develop

- ✅ Write clean, documented code
- ✅ Follow Python conventions (PEP 8)
- ✅ Add tests if possible
- ✅ Update documentation


### 4. Test

```bash
# Manual testing
python nmea_server.py

# Build the executable
./build_unix.sh  # or build_windows.bat
./test_executable.sh
```


### 5. Commit and Push

```bash
git add .
git commit -m "✨ Add new feature XYZ

- Description of what was added
- Why it was needed
- How it works"

git push origin feature/your-feature-name
```


### 6. Pull Request

1. Go to GitHub and create a **Pull Request**
2. Clearly describe your changes
3. Link the corresponding issue if applicable
4. Wait for review and comments


## 📝 Code Standards

### Python

```python
# Use docstrings
def my_function(param: str) -> bool:
    """
    Function description.
    
    Args:
        param: Description of the parameter
    Returns:
        Description of the return value
    """
    return True

# Descriptive names
enable_serial = True  # ✅
es = True            # ❌
```

### Commit Messages

Use **emojis** and be descriptive:

```bash
✨ Add AIS protocol support
🐛 Fix NMEA decoding error
📚 Improve API documentation
🎨 Refactor web interface
🔧 Optimize UDP performance
♻️ Refactor serial code
```

### File Structure

```bash
nmea-tracker-server/
├── nmea_server.py          # 🚫 DO NOT touch main structure
├── templates/              # ✅ UI improvements allowed
├── requirements.txt        # ✅ New dependencies OK
├── docs/                   # ✅ Additional documentation
└── tests/                  # ✅ Tests encouraged
```


## 🧪 Tests

### Manual Tests

1. **Basic functionality**: Server starts and interface is accessible
2. **Connections**: UDP, TCP, Serial work
3. **Interface**: Configuration and visualization operational
4. **Build**: Executable compiles and works

### Automated Tests (coming soon)

We plan to add:

- Unit tests for NMEA decoding
- Integration tests for network connections
- Performance tests


## 🚫 What to Avoid

- ❌ Modifying SSL certificates without reason
- ❌ Changing the main structure without discussion
- ❌ Adding heavy unnecessary dependencies
- ❌ Breaking existing compatibility
- ❌ Undocumented or untested code


## 🎯 Contribution Ideas

### 🥇 High Priority

- 🔐 Web authentication interface
- 📊 Historical GPS data charts
- 🌍 Multi-language support (EN, ES, DE)
- 📱 Improved responsive mobile interface

### 🥈 Medium Priority

- 🧪 Automated test suite
- 📦 Docker package
- ⚙️ REST API for integrations
- 🔄 Cloud data synchronization

### 🥉 Future Ideas

- 🤖 Command-line interface
- 🎨 Customizable interface themes
- 📈 Real-time performance metrics
- 🔌 Plugin system


## 💬 Communication

- 🐛 **Bugs**: [GitHub Issues](https://github.com/YOUR_USERNAME/nmea-tracker-server/issues)
- 💡 **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/nmea-tracker-server/discussions)
<!-- - 📧 **Direct contact**: your.email@example.com -->


## 🏆 Recognition

All contributors will be:

- ✨ Mentioned in the **CHANGELOG.md**
- 🎖️ Added to the **Contributors** section of the README
- 💝 Thanked personally


## 📄 License

By contributing, you agree that your contributions will be licensed under the **MIT** license like the rest of the project.


---

## Thank you for making NMEA Tracker Server a better tool for the maritime community! ⚓🧭
