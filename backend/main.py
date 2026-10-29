"""Run from the repo root: python -m uvicorn backend.main:app --reload."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import time
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)
SNAPSHOT = Path(__file__).resolve().parents[1] / 'public' / 'github-snapshot.json'
GITHUB_URL = 'https://api.github.com/users/sparekh14/repos'
CACHE_SECONDS = 300


class Repository(BaseModel):
    id: int
    name: str
    description: str | None
    url: str
    language: str | None
    stars: int
    updated_at: str
    topics: list[str]


class GithubFeed(BaseModel):
    repositories: list[Repository]
    source: Literal['live', 'cache', 'snapshot']
    fetched_at: str
    message: str | None = None


class GithubService:
    def __init__(self, client: httpx.AsyncClient, snapshot: Path = SNAPSHOT):
        self.client = client
        self.snapshot = snapshot
        self.cached: GithubFeed | None = None
        self.expires = 0.0
        self.retry_after = 0.0
        self.lock = asyncio.Lock()

    def fallback(self) -> GithubFeed:
        if self.cached:
            return self.cached.model_copy(update={
                'source': 'cache',
                'message': 'GitHub is unavailable; serving the last successful response.',
            })
        try:
            saved = GithubFeed.model_validate_json(self.snapshot.read_text())
            return saved.model_copy(update={
                'source': 'snapshot',
                'message': 'GitHub is unavailable; serving a saved snapshot.',
            })
        except (OSError, ValueError, ValidationError) as exc:
            raise HTTPException(503, 'GitHub is unavailable. Please try again later.') from exc

    async def get_feed(self) -> GithubFeed:
        async with self.lock:
            now = time.monotonic()
            if self.cached and now < self.expires:
                return self.cached.model_copy(update={'source': 'cache'})
            if now < self.retry_after:
                return self.fallback()
            try:
                # A fixed upstream prevents this endpoint becoming an open proxy.
                # Pagination keeps this complete even if the account exceeds 100 repos.
                repositories = []
                for page in range(1, 11):
                    response = await self.client.get(GITHUB_URL, params={
                        'per_page': 100, 'page': page, 'sort': 'updated', 'type': 'owner',
                    })
                    response.raise_for_status()
                    batch = response.json()
                    if not isinstance(batch, list):
                        raise ValueError('Unexpected GitHub response')
                    for repo in batch:
                        if repo.get('fork') or repo.get('archived') or repo.get('private'):
                            continue
                        repositories.append(Repository(
                            id=repo['id'], name=repo['name'], description=repo.get('description'),
                            url=repo['html_url'], language=repo.get('language'),
                            stars=repo['stargazers_count'], updated_at=repo['updated_at'],
                            topics=repo.get('topics', []),
                        ))
                    if len(batch) < 100:
                        break
                feed = GithubFeed(
                    repositories=repositories, source='live',
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                )
                self.cached = feed
                self.expires = time.monotonic() + CACHE_SECONDS
                self.retry_after = 0
                return feed
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                # Log the exception type only: never log headers or tokens.
                logger.warning('GitHub request failed: %s', type(exc).__name__)
                self.retry_after = time.monotonic() + 60
                return self.fallback()


@asynccontextmanager
async def lifespan(app: FastAPI):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'samarth-portfolio'}
    token = os.getenv('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        app.state.github = GithubService(client)
        yield


app = FastAPI(title='Samarth Parekh · Portfolio API', version='1.0.0', lifespan=lifespan)
origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
app.add_middleware(
    CORSMiddleware, allow_origins=[origin.strip() for origin in origins if origin.strip()],
    allow_methods=['GET'], allow_headers=['Accept', 'Content-Type'],
)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/api/github', response_model=GithubFeed)
async def github_repositories():
    return await app.state.github.get_feed()
