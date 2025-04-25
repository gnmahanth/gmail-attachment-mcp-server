# Gmail Attachment MCP Server

A server that provides a microservice for downloading Gmail attachments using the Message Control Protocol (MCP).

## Overview

This project implements a FastMCP server that allows you to download attachments from Gmail messages using a message ID. It uses IMAP to connect to Gmail and fetch the attachments.

## Features

- Download attachments from Gmail messages using message ID
- Secure connection to Gmail using IMAP over SSL
- Environment variable configuration for credentials
- Simple API interface through MCP

## Prerequisites

- Python 3.7 or higher
- uv needs to be installed
- Gmail account with IMAP enabled
- App Password for Gmail (if using 2-Step Verification)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gmail-attachment-mcp-server.git
cd gmail-attachment-mcp-server

# Install dependencies
uv sync
```

## Configuration

Set the following environment variables:

```bash
export GMAIL_USERNAME="your.email@gmail.com"
export GMAIL_PASSWORD="your_app_password"
export GMAIL_IMAP_SERVER="imap.gmail.com" # Optional, defaults to imap.gmail.com
```

> **Note**: For Gmail, you should use an App Password instead of your regular password. See [Google's documentation](https://support.google.com/accounts/answer/185833) for more information.

## Usage

### Starting the server

```bash
python server.py
# or
mcp run server.py
```

### Using the tool

The server exposes a `download_attachments_tool` that accepts the following parameters:

- `message_id`: The Gmail message ID in hexadecimal format
- `download_folder`: (Optional) The folder to download attachments to (defaults to "./attachments")

The function returns a list of paths to the downloaded attachment files.

### using with mcp inspector
```bash
npx @modelcontextprotocol/inspector uv run mcp run server.py
```

### using with goose
```yaml
extensions:
  gmail-attachment-mcp-server:
    args:
      - run
      - /path to virtual env/.venv/bin/mcp
      - run
      - /path to gmail-attachment-mcp-server/server.py
    bundled: null
    cmd: uv
    description: null
    enabled: true
    env_keys:
      - GMAIL_USERNAME
      - GMAIL_PASSWORD
    envs: {}
    name: gmail-attachment-mcp-server
    timeout: 300
    type: stdio
```

## API Reference

### `download_attachments_tool`

```python
download_attachments_tool(message_id: str, download_folder="./attachments") -> list[str]
```

Downloads attachments from a Gmail message identified by its message ID.

#### Parameters:

- `message_id`: The Gmail message ID in hexadecimal format
- `download_folder`: (Optional) The folder to download attachments to (defaults to "./attachments")

#### Returns:

- A list of strings containing the file paths of downloaded attachments

## License

[MIT](LICENSE)