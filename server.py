"""
MemoMCP - 本地长期记忆 MCP Server
让任意支持 MCP 的 AI 客户端拥有持久化记忆能力
"""
import sqlite3
import time
from mcp.server.fastmcp import FastMCP

DB = "memo.db"
mcp = FastMCP("memomcp")

def db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tags TEXT DEFAULT '',
            created_at REAL NOT NULL
        )
    """)
    return conn

@mcp.tool()
def remember(content: str, tags: str = "") -> str:
    """记住一件事。content 为记忆内容，tags 为逗号分隔的标签。"""
    conn = db()
    conn.execute("INSERT INTO memo (content, tags, created_at) VALUES (?,?,?)",
                 (content, tags, time.time()))
    conn.commit()
    conn.close()
    return f"已记住：{content}"

@mcp.tool()
def recall(keyword: str, limit: int = 5) -> str:
    """按关键词检索记忆，返回最相关的若干条。"""
    conn = db()
    rows = conn.execute(
        "SELECT id, content, tags, created_at FROM memo "
        "WHERE content LIKE ? OR tags LIKE ? ORDER BY created_at DESC LIMIT ?",
        (f"%{keyword}%", f"%{keyword}%", limit)
    ).fetchall()
    conn.close()
    if not rows:
        return f"没有找到与「{keyword}」相关的记忆。"
    out = []
    for rid, content, tags, ts in rows:
        day = time.strftime("%Y-%m-%d", time.localtime(ts))
        out.append(f"#{rid} [{day}] {content}  (标签: {tags or '无'})")
    return "\n".join(out)

@mcp.tool()
def recent(days: int = 7) -> str:
    """查看最近 N 天记录的记忆，用于回顾进度。"""
    since = time.time() - days * 86400
    conn = db()
    rows = conn.execute(
        "SELECT content, tags, created_at FROM memo WHERE created_at >= ? "
        "ORDER BY created_at DESC", (since,)
    ).fetchall()
    conn.close()
    if not rows:
        return f"最近 {days} 天没有记录。"
    return "\n".join(
        f"- {c}（{t or '无标签'}）" for c, t, _ in rows
    )

if __name__ == "__main__":
    mcp.run()