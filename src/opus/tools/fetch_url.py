"""Built-in fetch tool for retrieving web content"""

import asyncio
import logging
from typing import Dict, Any
from urllib.parse import urlparse

import httpx
import html2text

logger = logging.getLogger(__name__)

# Security: Blocked domains to prevent SSRF attacks
BLOCKED_DOMAINS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.169.254",  # AWS metadata endpoint
    "metadata.google.internal",  # GCP metadata endpoint
]

# Maximum content size to fetch (100 KB like Claude Code)
MAX_CONTENT_SIZE = 100_000

# Request timeout in seconds
DEFAULT_TIMEOUT = 10


def is_safe_url(url: str) -> tuple[bool, str]:
    """
    Validate that a URL is safe to fetch.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        parsed = urlparse(url)

        # Must be http or https
        if parsed.scheme not in ["http", "https"]:
            return False, f"Only http and https schemes are allowed, got: {parsed.scheme}"

        # Must have a hostname
        if not parsed.hostname:
            return False, "URL must have a hostname"

        # Block private/internal domains
        hostname_lower = parsed.hostname.lower()
        for blocked in BLOCKED_DOMAINS:
            if hostname_lower == blocked or hostname_lower.endswith(f".{blocked}"):
                return False, f"Access to {parsed.hostname} is blocked for security reasons"

        # Block private IP ranges (basic check)
        if parsed.hostname.startswith("10.") or \
           parsed.hostname.startswith("192.168.") or \
           parsed.hostname.startswith("172."):
            return False, "Access to private IP addresses is blocked"

        return True, ""

    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


async def fetch_url_content(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Fetch content from a URL and convert to markdown.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Dict with content and metadata
    """
    # Validate URL safety
    is_safe, error_msg = is_safe_url(url)
    if not is_safe:
        return {
            "error": error_msg,
            "url": url,
        }

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(timeout),
        ) as client:
            logger.info(f"Fetching URL: {url}")

            # Make request
            response = await client.get(url)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type:
                return {
                    "error": f"Unsupported content type: {content_type}. Only HTML and plain text are supported.",
                    "url": url,
                    "content_type": content_type,
                }

            # Get content
            content = response.text

            # Check size
            if len(content) > MAX_CONTENT_SIZE:
                logger.warning(f"Content size ({len(content)} bytes) exceeds limit, truncating")
                content = content[:MAX_CONTENT_SIZE]

            # Convert HTML to markdown if needed
            if "text/html" in content_type:
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                h.ignore_emphasis = False
                h.body_width = 0  # Don't wrap lines
                markdown_content = h.handle(content)
            else:
                markdown_content = content

            # Trim whitespace
            markdown_content = markdown_content.strip()

            logger.info(f"Successfully fetched {len(markdown_content)} characters from {url}")

            return {
                "content": markdown_content,
                "url": url,
                "status_code": response.status_code,
                "content_type": content_type,
                "size": len(markdown_content),
            }

    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
            "url": url,
            "status_code": e.response.status_code,
        }

    except httpx.TimeoutException:
        return {
            "error": f"Request timed out after {timeout} seconds",
            "url": url,
        }

    except httpx.RequestError as e:
        return {
            "error": f"Request failed: {str(e)}",
            "url": url,
        }

    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "url": url,
        }


async def execute_fetch(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the fetch tool.

    Args:
        args: Tool arguments containing 'url'

    Returns:
        Result dict with content or error
    """
    url = args.get("url")

    if not url:
        return {"error": "Missing required parameter: url"}

    result = await fetch_url_content(url)

    # Format output for display
    if "error" in result:
        output = f"Error fetching {url}:\n{result['error']}"
    else:
        output = result["content"]

    return {
        "output": output,
        "metadata": {
            "url": result.get("url"),
            "status_code": result.get("status_code"),
            "size": result.get("size"),
        }
    }


# Tool definition for loader
FETCH_URL_TOOL_DEFINITION = {
    "name": "fetch_url",
    "description": "Fetch and read content from a URL. Use this to access web pages, documentation, API references, or any web content. Returns the content as markdown text.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch content from (must be http or https)"
            }
        },
        "required": ["url"]
    },
}
