from fastapi.testclient import TestClient
from demos.sqlite import main


def test_sqlite_crud_relationships_persistence_and_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DB_PATH', tmp_path / 'test.db')
    with TestClient(main.app) as client:
        created = client.post('/projects', json={'title': "Samarth's Portfolio", 'category': 'Full stack'} )
        assert created.status_code == 201
        project_id = created.json()['id']
        assert client.get('/projects', params={'q': "Samarth's"}).json()[0]['id'] == project_id
        # SQL-looking input stays a value; it cannot change the query.
        assert client.get('/projects', params={'q': "' OR 1=1 --"}).json() == []
        assert client.post('/projects', json={'title': '   ', 'category': 'Demo'}).status_code == 422
        assert client.patch(f'/projects/{project_id}', json={'title': 'Portfolio v2', 'stars': 5}).json()['stars'] == 5
        assert client.post(f'/projects/{project_id}/notes', json={'body': 'Live GitHub explorer'}).status_code == 201
        assert client.get('/project-notes').json() == [{'title': 'Portfolio v2', 'body': 'Live GitHub explorer'}]
    with TestClient(main.app) as client:
        assert len(client.get('/projects').json()) == 1
        assert client.delete(f'/projects/{project_id}').status_code == 204
        assert client.get('/project-notes').json() == []
        assert client.delete(f'/projects/{project_id}').status_code == 404
        assert client.patch('/projects/99999', json={'title': 'Missing', 'stars': 0}).status_code == 404
