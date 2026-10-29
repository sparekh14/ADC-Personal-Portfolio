"""Opt in with MONGODB_TEST_URI pointing to a local disposable MongoDB server."""
import os
import uuid

from fastapi.testclient import TestClient
from pymongo import MongoClient
import pytest

from demos.mongodb import main


@pytest.mark.skipif(not os.getenv('MONGODB_TEST_URI'), reason='Local MongoDB integration server not configured')
def test_mongodb_crud_persistence_and_validation(monkeypatch):
    uri = os.environ['MONGODB_TEST_URI']
    database = 'portfolio_bootcamp_test_' + uuid.uuid4().hex
    monkeypatch.setenv('MONGODB_URI', uri)
    monkeypatch.setenv('MONGODB_DATABASE', database)
    try:
        with TestClient(main.app) as client:
            created = client.post('/projects', json={'title': 'My Portfolio', 'category': 'Full stack', 'technologies': ['React', 'FastAPI']})
            assert created.status_code == 201
            project_id = created.json()['_id']
            assert len(project_id) == 24
            assert len(client.get('/projects', params={'technology': 'React'}).json()) == 1
            assert client.get('/projects', params={'technology': 'Unknown'}).json() == []
            assert client.patch(f'/projects/{project_id}', json={'title': 'Portfolio v2', 'stars': 5}).json()['stars'] == 5
            assert client.post('/projects', json={'title': ' ', 'category': 'Demo'}).status_code == 422
            assert client.delete('/projects/not-an-objectid').status_code == 400
        with TestClient(main.app) as client:
            assert len(client.get('/projects').json()) == 1
            assert client.delete(f'/projects/{project_id}').status_code == 204
            assert client.delete(f'/projects/{project_id}').status_code == 404
    finally:
        with MongoClient(uri) as client:
            client.drop_database(database)  # only the unique DB created in this test
