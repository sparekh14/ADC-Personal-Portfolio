import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import GithubService, app

RAW = {'id': 1, 'name': 'example', 'description': 'A project', 'html_url': 'https://github.com/sparekh14/example', 'language': 'Python', 'stargazers_count': 2, 'updated_at': '2026-10-29T12:00:00Z', 'topics': ['api'], 'fork': False, 'archived': False, 'private': False}


@pytest.fixture
def snapshot(tmp_path):
    path = tmp_path / 'snapshot.json'
    path.write_text(json.dumps({'repositories': [], 'source': 'snapshot', 'fetched_at': '2026-10-29T12:00:00Z', 'message': None}))
    return path


def test_live_cache_and_concurrent_requests(snapshot):
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(200, json=[RAW, {**RAW, 'id': 2, 'fork': True}, {**RAW, 'id': 3, 'archived': True}])
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            service = GithubService(client, snapshot)
            responses = await asyncio.gather(*(service.get_feed() for _ in range(5)))
            assert len(calls) == 1
            assert [item.source for item in responses] == ['live', 'cache', 'cache', 'cache', 'cache']
            assert len(responses[0].repositories) == 1
            assert responses[0].repositories[0].stars == 2
    asyncio.run(run())


@pytest.mark.parametrize('status', [403, 429, 500])
def test_upstream_failures_use_snapshot_and_cooldown(status, snapshot):
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(status)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            service = GithubService(client, snapshot)
            assert (await service.get_feed()).source == 'snapshot'
            assert (await service.get_feed()).source == 'snapshot'
            assert len(calls) == 1
    asyncio.run(run())


def test_timeout_uses_snapshot(snapshot):
    def handle(request):
        raise httpx.ReadTimeout('Timeout', request=request)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            assert (await GithubService(client, snapshot).get_feed()).source == 'snapshot'
    asyncio.run(run())


def test_stale_cache_is_retained(snapshot):
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(200, json=[RAW]) if len(calls) == 1 else httpx.Response(500)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            service = GithubService(client, snapshot)
            first = await service.get_feed()
            service.expires = 0
            fallback = await service.get_feed()
            assert fallback.source == 'cache'
            assert fallback.fetched_at == first.fetched_at
            assert fallback.message
    asyncio.run(run())


def test_missing_snapshot_returns_503(tmp_path):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(500))) as client:
            with pytest.raises(HTTPException) as error:
                await GithubService(client, tmp_path / 'missing.json').get_feed()
            assert error.value.status_code == 503
    asyncio.run(run())


def test_health_and_cors():
    with TestClient(app) as client:
        assert client.get('/health').json() == {'status': 'ok'}
        response = client.get('/health', headers={'Origin': 'http://localhost:5173'})
        assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'
        assert 'access-control-allow-origin' not in client.get('/health', headers={'Origin': 'https://unrelated.example'}).headers
