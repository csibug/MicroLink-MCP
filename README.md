# Andonstar MCP Microscope Controller

This project provides a **Model Context Protocol (MCP)** implementation for Andonstar digital microscopes (optimized for the AD207S). It enables AI assistants, such as Claude, to interact with your microscope for electronics repair, inspection, and documentation.

## Features

- **Model Context Protocol Integration**: Seamlessly connects your microscope to LLM-based workflows.
- **Smart Hardware Discovery**: Automatically scans USB ports to find the high-resolution microscope device.
- **High-Definition Capture**: Reliable 1920x1080 MJPG frame grabbing with sensor stabilization.
- **Interactive Focus Assistant**: A real-time sharpness scoring window with peak value tracking.
- **Project-Based Organization**: Automatic watermarking and folder-based sorting for your repair captures.
- **Audio Feedback**: System beeps to notify the user of video recording states.

## Project Structure

```text
Andonstar-MCP/
├── captures/               # Snapshot and video storage (git-ignored)
├── src/
│   ├── server.py           # FastMCP Wrapper (Main Entry Point)
│   ├── vision_engine.py    # Core camera and image processing logic
│   └── tools/              # Diagnostic and research scripts
│       ├── check_capabilities.py
│       └── debug_hd_capture.py
├── .gitignore              # Rules for Git exclusion
└── README.md               # You are here
```

## Installation

### 1. Prerequisites
- Python 3.10 or higher
- A digital microscope (e.g., Andonstar AD207S) connected via USB.

### 2. Install Dependencies
```bash
pip install opencv-python mcp
```

### 3. Setup Claude Desktop
Add the following configuration to your `claude_desktop_config.json` (usually located in `%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "andonstar": {
      "command": "python",
      "args": ["C:/Users/YOUR_USER/Path/To/Project/src/microscope_server.py"]
    }
  }
}
```

## Usage

Once the server is running, you can ask Claude to:
- *"Capture an image of this PCB."*
- *"Set the project name to Sony TC-FX44."*
- *"Start the focus assistant."*
- *"Record a 10-second video of the soldering process."*

## Diagnostic Tools

If you encounter issues with resolution or camera detection, use the provided tools in `src/tools/`:

- **`check_capabilities.py`**: Verifies if the OS can see the 1080p stream and displays the FOURCC code.

## License

This project is licensed under the MIT License.