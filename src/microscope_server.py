import os
import sys
import base64
import signal
import logging
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent
from vision_engine import AndonstarEngine

# --- LOGGER CONFIGURATION ---
# Ugyanazt a formátumot használjuk, mint a vision_engine-ben, 
# így a logfájlban egységes lesz a megjelenés.
logger = logging.getLogger("AndonstarServer")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# A FastMCP stderr-re logol, ami a kliens logfájljaiba kerül
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# Initialize FastMCP and the Engine
mcp = FastMCP("Andonstar-AD207S")
engine = AndonstarEngine()

@mcp.tool()
def shutdown_server() -> str:
    """
    Safely shuts down the MCP server and releases camera resources.
    """
    logger.info("Shutdown request received via MCP tool.")
    # Graceful termination
    os.kill(os.getpid(), signal.SIGTERM)
    return "Server is shutting down. Camera resources have been released."

@mcp.tool()
def set_project_name(name: str) -> str:
    """
    Sets the active project name for watermarking and file organization.
    If no name is provided, it defaults to 'Microscope_Project'.
    """
    # Az engine.set_project már belül logol, így itt nem muszáj külön
    new_name = engine.set_project(name)
    return f"Active project context is now: {new_name}"

@mcp.tool()
def start_focus_assistant() -> str:
    """
    Opens the live focus assistant window with real-time sharpness scoring.
    """
    logger.info("Opening Focus Assistant window on host.")
    try:
        last, best = engine.run_focus_assistant()
        return f"Focus assistant closed. Last: {last}, Best: {best}"
    except Exception as e:
        logger.error(f"Failed to start focus assistant: {str(e)}")
        return f"Error: Focus assistant could not be started. Check logs."

@mcp.tool()
def capture_microscope_image() -> list[TextContent | ImageContent]:
    """
    Captures a high-resolution image and returns it directly to the chat for analysis.
    """
    logger.info("Image capture and analysis requested.")
    path = engine.take_snapshot()
    
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            
            logger.info(f"Image successfully sent to client: {path}")
            return [
                TextContent(type="text", text=f"Snapshot captured: {path}"),
                ImageContent(type="image", data=img_data, mimeType="image/jpeg")
            ]
        except Exception as e:
            logger.error(f"Error encoding image: {str(e)}")
            return [TextContent(type="text", text=f"Error: Could not process image file. {str(e)}")]
    
    logger.error("Snapshot capture failed.")
    return [TextContent(type="text", text="Error: Microscope failed to capture the image.")]

@mcp.tool()
def record_video(seconds: int = 5) -> str:
    """
    Records a video clip. Audio signals will indicate the start and end of recording.
    """
    logger.info(f"Video recording triggered for {seconds} seconds.")
    path = engine.record_clip(seconds)
    if path:
        return f"Video recorded successfully: {path}"
    
    logger.error("Video recording failed.")
    return "Error: Could not record video clip."

if __name__ == "__main__":
    # FastMCP run handling
    logger.info("Starting Andonstar MCP Server...")
    mcp.run()