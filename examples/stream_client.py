"""
A2A Stream Client
Connects to the streaming server and displays events in real-time
"""

import requests
import json
import sys
from datetime import datetime


def colorize(text: str, color: str) -> str:
    """Add color to text"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bold": "\033[1m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def print_header():
    """Print header"""
    print("\n" + "=" * 80)
    print(colorize("🌊 A2A STREAM CLIENT", "cyan"))
    print("=" * 80 + "\n")


def format_event(event_num: int, event: dict):
    """Format and print an event"""
    event_type = event.get("type", "unknown")
    
    # Header
    print(f"\n{colorize(f'Event #{event_num}', 'bold')} | Type: {colorize(event_type, 'yellow')}")
    print("-" * 80)
    
    if event_type == "statusUpdate":
        # Status update - NO PARTS
        print(f"  {colorize('❌ NO PARTS', 'red')} - Status updates are state-only")
        print(f"  State: {colorize(event.get('state', 'N/A'), 'cyan')}")
        print(f"  Task ID: {event.get('task_id', 'N/A')}")
        print(f"  Context ID: {event.get('context_id', 'N/A')}")
    
    elif event_type == "agent_parts":
        # Agent message - HAS PARTS
        print(f"  {colorize('✅ HAS PARTS', 'green')} - Messages have content")
        print(f"  Role: {colorize(event.get('role', 'N/A'), 'magenta')}")
        
        parts = event.get('parts', [])
        print(f"  Parts (full structure): {colorize(str(parts), 'cyan')}")
        
        # Also show just the content for readability
        for i, part in enumerate(parts):
            content = part.get('content', '')
            if content:
                print(f"  Content: {colorize(content, 'white')}")
        
        print(f"  Task ID: {event.get('task_id', 'N/A')}")
        print(f"  Context ID: {event.get('context_id', 'N/A')}")
    
    elif event_type == "artifactUpdate":
        # Artifact update - HAS CONTENT
        print(f"  {colorize('✅ HAS CONTENT', 'green')} - Artifacts have content")
        print(f"  Artifact ID: {colorize(event.get('artifact_id', 'N/A'), 'cyan')}")
        print(f"  Content: {colorize(event.get('content', 'N/A'), 'white')}")
        
        metadata = event.get('metadata', {})
        if metadata:
            print(f"  Metadata: {metadata}")
    
    elif event_type == "end":
        # End signal
        print(f"  {colorize('🏁 STREAM COMPLETE', 'green')}")
    
    else:
        # Unknown event
        print(f"  {colorize('⚠️  Unknown event type', 'yellow')}")
        print(f"  Data: {json.dumps(event, indent=2)}")


def stream_events(url: str):
    """Connect to stream and display events"""
    
    print_header()
    print(f"Connecting to: {colorize(url, 'cyan')}\n")
    
    try:
        # Connect to stream
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        print(colorize("✅ Connected! Receiving events...\n", "green"))
        print("=" * 80)
        
        event_num = 0
        
        # Read stream line by line
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                
                # SSE format: "data: {...}"
                if line.startswith('data: '):
                    data = line[6:]  # Remove "data: " prefix
                    
                    try:
                        event = json.loads(data)
                        event_num += 1
                        format_event(event_num, event)
                        
                        # Break on end signal
                        if event.get('type') == 'end':
                            break
                    
                    except json.JSONDecodeError as e:
                        print(f"{colorize('Error parsing JSON:', 'red')} {e}")
                        print(f"Raw data: {data}")
        
        print("\n" + "=" * 80)
        print(colorize("✅ Stream complete!", "green"))
        print("=" * 80 + "\n")
        
        # Summary
        print(colorize("KEY TAKEAWAYS:", "bold"))
        print("  1. statusUpdate events → ❌ NO parts, just state")
        print("  2. agent_parts events  → ✅ HAS parts with content")
        print("  3. artifactUpdate      → ✅ HAS content")
        print()
    
    except requests.exceptions.ConnectionError:
        print(colorize("❌ Error: Could not connect to server", "red"))
        print("Make sure the server is running: python3 stream_server.py")
        sys.exit(1)
    
    except requests.exceptions.Timeout:
        print(colorize("❌ Error: Connection timed out", "red"))
        sys.exit(1)
    
    except KeyboardInterrupt:
        print(colorize("\n\n⚠️  Interrupted by user", "yellow"))
        sys.exit(0)
    
    except Exception as e:
        print(colorize(f"❌ Error: {e}", "red"))
        sys.exit(1)


if __name__ == "__main__":
    # Get query from command line or use default
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Analyze the latest market trends"
    
    # Build URL
    url = f"http://localhost:8000/stream?query={requests.utils.quote(query)}"
    
    # Stream events
    stream_events(url)
