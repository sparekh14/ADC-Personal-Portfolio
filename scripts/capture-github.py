"""Refresh the public, explicitly labeled fallback snapshot. Run from repo root."""
import asyncio
import json
from pathlib import Path
import httpx
from backend.main import GithubService

async def main():
    async with httpx.AsyncClient(headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'samarth-portfolio'}, timeout=15) as client:
        feed = await GithubService(client).get_feed()
        if feed.source != 'live':
            raise SystemExit('No live response; existing snapshot left unchanged.')
        feed.source = 'snapshot'
        feed.message = 'Saved public GitHub data; the live backend is unavailable.'
        path = Path('public/github-snapshot.json')
        path.write_text(json.dumps(feed.model_dump(), indent=2) + '\n')
        print(f'Saved {len(feed.repositories)} public repositories to {path}')

asyncio.run(main())
