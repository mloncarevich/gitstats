# 📊 gitstats

> Beautiful git statistics in your terminal

[![CI](https://github.com/mloncarevich/gitstats/actions/workflows/ci.yml/badge.svg)](https://github.com/mloncarevich/gitstats/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 📈 Commit statistics at a glance
- 🗓️ Activity heatmap by day of week
- ⏰ Peak coding hours analysis
- 👥 Contributor insights
- 🎨 Beautiful terminal output

## 🚀 Installation

```bash
pip install gitstats
```

Or install from source:

```bash
git clone https://github.com/mloncarevich/gitstats.git
cd gitstats
pip install -e .
```

## 📖 Usage

```bash
# Show stats for current directory
gitstats stats

# Show stats for a specific repo
gitstats stats /path/to/repo
```

## 🛠️ Development

```bash
# Clone the repo
git clone https://github.com/mloncarevich/gitstats.git
cd gitstats

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.
