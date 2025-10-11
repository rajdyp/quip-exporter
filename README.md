# Quip Exporter

Export Quip documents as Markdown files (images not included).

## Installation

```bash
# Install in development mode
pip install -e .
```

## Usage

### Export Specific Folder

To export a specifig folder in Quip:

```bash
# Export a specific folder
quip-export --token YOUR_TOKEN --folder-id FOLDER_ID
```

### Export Everything

To export all folders you have access to in Quip:

```bash
# Export ALL accessible folders
quip-export --token YOUR_TOKEN --all
```

This will:
- Discover all shared folders and group folders
- Export each one to a separate directory
- Maintain folder structure if `--maintain-structure` is used

### Maintaining Folder Structure

By default, all documents are exported to the root output directory. To maintain the Quip folder hierarchy:

```bash
quip-export --token YOUR_TOKEN --folder-id FOLDER_ID --maintain-structure
```

This will create subdirectories matching your Quip folder structure:
```
output/
├── _assets/              # All images (not supported)
├── document1.md          # Root-level documents
├── subfolder1/
│   ├── document2.md
│   └── document3.md
└── subfolder2/
    └── nested/
        └── document4.md
```

## Configuration

Set environment variables to avoid passing arguments each time:

```bash
export QUIP_TOKEN="your_personal_access_token"
export QUIP_FOLDER_ID="eKLAOA5UvPd"
export QUIP_OUT="~/Documents/QuipNotes"  # optional, this is the default
```

Then simply run:
```bash
quip-export
```

## Options

- `--token`: Quip Personal Access Token (or set `QUIP_TOKEN`)
- `--folder-id`: Folder ID from Quip URL (or set `QUIP_FOLDER_ID`)
- `--out`: Output directory (default: `~/Documents/QuipNotes`)
- `--no-recursive`: Don't include subfolders
- `--maintain-structure`: Maintain Quip folder structure in output (documents are organized in matching subdirectories)

## Project Structure

```
quip-exporter/
├── quip_exporter/          # Main package
│   ├── __init__.py
│   ├── __main__.py         # CLI entry point
│   ├── api/                # Quip API client
│   │   ├── client.py       # Session & base requests
│   │   └── endpoints.py    # Folder/thread operations
│   ├── conversion/         # HTML to Markdown
│   │   ├── html_processor.py  # Image handling
│   │   └── markdown.py     # Markdown conversion
│   ├── export/             # Export orchestration
│   │   ├── exporter.py     # Main export logic
│   │   └── manifest.py     # Change tracking
│   ├── models/             # Data models
│   │   └── types.py        # ThreadMeta, etc.
│   └── utils/              # Utilities
│       ├── filesystem.py   # File operations
│       ├── network.py      # Retry logic
│       └── helpers.py      # General helpers
├── pyproject.toml          # Package configuration
├── .env.example
└── README.md
```

## Features

- ✅ Exports Quip documents to Markdown
- ✅ Incremental exports (skips unchanged docs)
- ✅ Handles subfolders recursively
- ✅ Retry logic for network errors
- ✅ Modular, testable code structure

## How It Works

1. **API Module**: Authenticates and fetches folder/thread data from Quip
2. **Conversion Module**: Converts HTML to Markdown
3. **Export Module**: Orchestrates the export and tracks changes via manifest
4. **Utils Module**: Provides filesystem, network, and helper utilities
