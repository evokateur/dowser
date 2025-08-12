# dowser.py

Dowses a URL for audio streams

## What it does

Looks for audio streams on a webpage and attempts to rank them by quality.
The stream of the highest perceived quality will be copied to the paste buffer.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Basic usage:

```bash
./dowser https://example.com/some-page
```

See all audio streams found:

```bash
./dowser --list-all https://example.com/some-page
```

Don't copy to clipboard:

```bash
./dowser --no-clipboard https://example.com/some-page
```

Verbose output for debugging:

```bash
./dowser -v https://example.com/some-page
```
