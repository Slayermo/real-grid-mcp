import uvicorn

# --- THE MONKEY PATCH ---
# This intercepts the background web engine before FastMCP loads
# and forces it to trust Render's secure HTTPS proxy!
original_config_init = uvicorn.Config.__init__
def patched_config_init(self, *args, **kwargs):
    kwargs["proxy_headers"] = True
    kwargs["forwarded_allow_ips"] = "*"
    original_config_init(self, *args, **kwargs)
uvicorn.Config.__init__ = patched_config_init
# ------------------------

from fastmcp import FastMCP
import os
import psycopg2

# 1. Initialize the MCP Server
mcp = FastMCP("Grid_Database")

# 2. Give the AI a tool to run
@mcp.tool()
def log_vote(track_name: str, rating: str, user_handle: str) -> str:
    """Saves a track rating (Fire or Trash) to the Supabase database."""
    db_url = os.environ.get("DATABASE_URL")
    try:
        # Connect to Supabase
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Insert the data
        cur.execute(
            'INSERT INTO "Votes" ("UserHandle", "TrackName", "Rating") VALUES (%s, %s, %s)',
            (user_handle, track_name, rating)
        )
        conn.commit()
        
        # Close connections
        cur.close()
        conn.close()
        return f"Success! Logged {rating} for {track_name} by {user_handle}."
    except Exception as e:
        return f"Database error: {str(e)}"

if __name__ == "__main__":
    # 3. Start the server using SSE for the internet
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
