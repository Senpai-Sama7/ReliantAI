#!/usr/bin/env python3
"""Web UI for Intelligent Storage System (Async Edition)"""

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from typing import Optional

# Import async db
from db import init_pool, close_pool, get_conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler for startup/shutdown."""
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="Intelligent Storage Browser", lifespan=lifespan)


CATEGORY_EXTENSIONS = {
    "code": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs", ".go", ".rb", ".php"],
    "document": [".pdf", ".doc", ".txt", ".md", ".docx"],
    "image": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"],
    "audio": [".mp3", ".wav", ".flac", ".ogg", ".m4a"],
    "video": [".mp4", ".mkv", ".avi", ".mov", ".webm"],
    "data": [".csv", ".json", ".xml", ".yaml", ".yml", ".parquet", ".toml"],
}


def classify_extension(extension: Optional[str]) -> str:
    ext = (extension or "").lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if ext in extensions:
            return category
    return "other"


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Intelligent Storage Browser</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; margin-bottom: 5px; }
        .subtitle { color: #666; margin-bottom: 20px; }
        .search-box { width: 100%; padding: 15px; font-size: 16px; border: 2px solid #ddd; border-radius: 8px; margin-bottom: 20px; box-sizing: border-box; }
        .search-box:focus { outline: none; border-color: #4CAF50; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 32px; font-weight: bold; color: #4CAF50; }
        .stat-label { color: #666; margin-top: 5px; }
        .filters { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .filter-btn { padding: 8px 16px; border: 1px solid #ddd; background: white; border-radius: 20px; cursor: pointer; transition: all 0.2s; }
        .filter-btn:hover, .filter-btn.active { background: #4CAF50; color: white; border-color: #4CAF50; }
        .file-list { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .file-item { padding: 15px 20px; border-bottom: 1px solid #eee; display: flex; align-items: start; gap: 15px; transition: background 0.2s; }
        .file-item:hover { background: #f9f9f9; }
        .file-icon { font-size: 24px; width: 40px; text-align: center; }
        .file-info { flex: 1; }
        .file-name { font-weight: 500; color: #333; margin-bottom: 4px; word-break: break-all; }
        .file-path { color: #666; font-size: 12px; margin-bottom: 4px; }
        .file-meta { display: flex; gap: 15px; font-size: 12px; color: #888; }
        .file-size { background: #e3f2fd; padding: 2px 8px; border-radius: 4px; }
        .file-ext { background: #fff3e0; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; }
        .preview { margin-top: 8px; padding: 10px; background: #f5f5f5; border-radius: 4px; font-family: monospace; font-size: 12px; color: #555; max-height: 100px; overflow: hidden; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .pagination { display: flex; justify-content: center; gap: 10px; margin-top: 20px; }
        .page-btn { padding: 8px 16px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; }
        .page-btn:hover { background: #f0f0f0; }
        .page-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        #results { min-height: 200px; }
    </style>
</head>
<body>
    <h1>🔍 Intelligent Storage Browser</h1>
    <p class="subtitle">Browse and search indexed files</p>
    
    <div class="stats" id="stats"></div>
    
    <input type="text" class="search-box" id="search" placeholder="Search files by name, content, or path..." onkeyup="debounceSearch()">
    
    <div class="filters">
        <button class="filter-btn active" onclick="filterBy('all')">All</button>
        <button class="filter-btn" onclick="filterBy('code')">Code</button>
        <button class="filter-btn" onclick="filterBy('document')">Documents</button>
        <button class="filter-btn" onclick="filterBy('image')">Images</button>
        <button class="filter-btn" onclick="filterBy('audio')">Audio</button>
        <button class="filter-btn" onclick="filterBy('video')">Video</button>
        <button class="filter-btn" onclick="filterBy('data')">Data</button>
    </div>
    
    <div class="file-list" id="results">
        <div class="loading">Loading files...</div>
    </div>
    
    <div class="pagination" id="pagination"></div>

    <script>
        let currentPage = 1;
        let currentFilter = 'all';
        let searchTimeout;
        
        const fileIcons = {
            code: '💻', document: '📄', image: '🖼️', audio: '🎵', 
            video: '🎬', data: '📊', config: '⚙️', archive: '📦',
            binary: '⚡', other: '📁'
        };
        
        const extColors = {
            '.py': '#3776ab', '.js': '#f7df1e', '.ts': '#3178c6', '.java': '#007396',
            '.cpp': '#00599c', '.c': '#555555', '.rs': '#dea584', '.go': '#00add8',
            '.rb': '#cc342d', '.php': '#777bb4', '.html': '#e34c26', '.css': '#264de4'
        };
        
        async function loadStats() {
            const res = await fetch('/api/stats');
            const stats = await res.json();
            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${stats.total_files.toLocaleString()}</div>
                    <div class="stat-label">Total Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.total_size}</div>
                    <div class="stat-label">Total Size</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.embedded.toLocaleString()}</div>
                    <div class="stat-label">Files with Embeddings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.top_extension}</div>
                    <div class="stat-label">Most Common Type</div>
                </div>
            `;
        }
        
        async function searchFiles(page = 1) {
            currentPage = page;
            const query = document.getElementById('search').value;
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
            
            let url = `/api/files?page=${page}&limit=20`;
            if (query) url += `&q=${encodeURIComponent(query)}`;
            if (currentFilter !== 'all') url += `&category=${currentFilter}`;
            
            const res = await fetch(url);
            const data = await res.json();
            
            if (data.files.length === 0) {
                resultsDiv.innerHTML = '<div class="loading">No files found</div>';
                document.getElementById('pagination').innerHTML = '';
                return;
            }
            
            resultsDiv.innerHTML = data.files.map(f => `
                <div class="file-item">
                    <div class="file-icon">${fileIcons[f.category] || '📁'}</div>
                    <div class="file-info">
                        <div class="file-name">${escapeHtml(f.name)}</div>
                        <div class="file-path">${escapeHtml(f.path)}</div>
                        <div class="file-meta">
                            <span class="file-size">${formatBytes(f.size_bytes)}</span>
                            <span class="file-ext">${f.extension || 'no ext'}</span>
                            ${f.mime_type ? `<span>${f.mime_type}</span>` : ''}
                        </div>
                        ${f.preview ? `<div class="preview">${escapeHtml(f.preview.substring(0, 200))}${f.preview.length > 200 ? '...' : ''}</div>` : ''}
                    </div>
                </div>
            `).join('');
            
            const totalPages = Math.ceil(data.total / 20);
            document.getElementById('pagination').innerHTML = `
                <button class="page-btn" onclick="searchFiles(${page - 1})" ${page <= 1 ? 'disabled' : ''}>← Previous</button>
                <span style="padding: 8px;">Page ${page} of ${totalPages}</span>
                <button class="page-btn" onclick="searchFiles(${page + 1})" ${page >= totalPages ? 'disabled' : ''}>Next →</button>
            `;
        }
        
        function filterBy(category) {
            currentFilter = category;
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.toggle('active', btn.textContent.toLowerCase().includes(category) || (category === 'all' && btn.textContent === 'All'));
            });
            searchFiles(1);
        }
        
        function debounceSearch() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => searchFiles(1), 300);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        // Initial load
        loadStats();
        searchFiles(1);
    </script>
</body>
</html>
    """


@app.get("/api/stats")
async def get_stats():
    async with get_conn() as conn:
        total_files = await conn.fetchval("SELECT COUNT(*) as total FROM files")
        embedded = await conn.fetchval(
            "SELECT COUNT(*) as embedded FROM file_embeddings"
        )

        top_ext_row = await conn.fetchrow(
            "SELECT extension, COUNT(*) as count FROM files WHERE extension IS NOT NULL GROUP BY extension ORDER BY count DESC LIMIT 1"
        )
        top_ext = top_ext_row["extension"] if top_ext_row else "none"

        total_size = (
            await conn.fetchval("SELECT SUM(size_bytes) as total FROM files") or 0
        )

        # Format size
        if total_size > 1099511627776:
            size_str = f"{total_size / 1099511627776:.1f} TB"
        elif total_size > 1073741824:
            size_str = f"{total_size / 1073741824:.1f} GB"
        else:
            size_str = f"{total_size / 1048576:.1f} MB"

        return {
            "total_files": total_files,
            "embedded": embedded,
            "top_extension": top_ext,
            "total_size": size_str,
        }


@app.get("/api/files")
async def get_files(
    q: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    async with get_conn() as conn:
        offset = (page - 1) * limit

        # Build query
        conditions = []
        params = []
        param_idx = 0

        if q:
            normalized_q = " ".join(q.strip().split())
            if normalized_q:
                param_idx += 1
                conditions.append(
                    f"(name ILIKE ${param_idx} OR path ILIKE ${param_idx} OR content_preview ILIKE ${param_idx})"
                )
                params.append(f"%{normalized_q}%")

        if category and category != "all":
            category_values = CATEGORY_EXTENSIONS.get(category.lower())
            if category_values:
                param_idx += 1
                conditions.append(f"extension = ANY(${param_idx})")
                params.append(category_values)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Count total
        count_query = f"SELECT COUNT(*) as total FROM files {where_clause}"
        total = await conn.fetchval(count_query, *params)

        # Get files
        query = f"""
            SELECT f.id, f.path, f.name, f.extension, f.size_bytes, f.mime_type, 
                   f.content_preview as preview
            FROM files f
            {where_clause}
            ORDER BY f.indexed_at DESC
            LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}
        """
        params.extend([limit, offset])
        rows = await conn.fetch(query, *params)

        # Add categories
        files = []
        for row in rows:
            f = dict(row)
            f["category"] = classify_extension(f.get("extension"))
            files.append(f)

        return {"files": files, "total": total, "page": page, "limit": limit}


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Intelligent Storage Browser...")
    print("📍 Open http://localhost:8080 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8080)
