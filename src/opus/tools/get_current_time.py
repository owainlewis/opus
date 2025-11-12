"""Built-in tool for getting the current time"""

from datetime import datetime, timezone
from typing import Dict, Any
import zoneinfo


async def execute_get_current_time(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the get_current_time tool.

    Args:
        args: Tool arguments with optional 'format' and 'timezone'

    Returns:
        Result dict with current time in requested format
    """
    # Get requested format (default to 'all')
    requested_format = args.get("format", "all")

    # Get timezone (default to UTC)
    tz_name = args.get("timezone", "UTC")

    try:
        if tz_name == "UTC":
            tz = timezone.utc
        else:
            tz = zoneinfo.ZoneInfo(tz_name)
    except zoneinfo.ZoneInfoNotFoundError:
        return {
            "output": f"Error: Unknown timezone '{tz_name}'. Use 'UTC' or a valid IANA timezone name (e.g., 'America/New_York', 'Europe/London').",
            "metadata": {"error": f"Invalid timezone: {tz_name}"}
        }

    # Get current time in requested timezone
    now = datetime.now(tz)
    now_utc = datetime.now(timezone.utc)

    # Format based on request
    if requested_format == "unix":
        output = str(int(now_utc.timestamp()))
    elif requested_format == "iso8601":
        output = now.isoformat()
    elif requested_format == "human":
        output = now.strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')
    elif requested_format == "date":
        output = now.strftime('%Y-%m-%d')
    elif requested_format == "time":
        output = now.strftime('%H:%M:%S')
    else:  # 'all' or any other value defaults to all formats
        output_lines = [
            "Current Time:",
            "",
            f"ISO 8601:          {now.isoformat()}",
            f"Unix Timestamp:    {int(now_utc.timestamp())}",
            f"Human Readable:    {now.strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}",
            f"Date:              {now.strftime('%Y-%m-%d')}",
            f"Time:              {now.strftime('%H:%M:%S')}",
            f"Timezone:          {tz_name}",
        ]
        output = "\n".join(output_lines)

    return {
        "output": output,
        "metadata": {
            "iso8601": now.isoformat(),
            "unix_timestamp": int(now_utc.timestamp()),
            "timezone": tz_name,
            "format": requested_format,
        }
    }


# Tool definition for loader
GET_CURRENT_TIME_TOOL_DEFINITION = {
    "name": "get_current_time",
    "description": "Get the current date and time. Returns the current time in various formats. Use this when you need accurate timestamps for time-sensitive operations like filtering logs by time range, calculating relative times (e.g., 'last hour'), or scheduling tasks. For log queries, use format='unix' to get a Unix timestamp suitable for time-based filtering.",
    "parameters": {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "Output format: 'all' (default, shows all formats), 'unix' (Unix timestamp in seconds), 'iso8601' (ISO 8601 format), 'human' (human-readable), 'date' (YYYY-MM-DD), or 'time' (HH:MM:SS)",
                "enum": ["all", "unix", "iso8601", "human", "date", "time"]
            },
            "timezone": {
                "type": "string",
                "description": "Timezone name (default: 'UTC'). Use IANA timezone names like 'America/New_York', 'Europe/London', etc. For operations and log queries, UTC is recommended."
            }
        },
        "required": []
    },
}
