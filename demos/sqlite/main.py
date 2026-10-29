"""Local teaching API: python -m uvicorn demos.sqlite.main:app --port 8001."""
from contextlib import asynccontextmanager, contextmanager
import os
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

DB_PATH = Path(os.getenv('SQLITE_DEMO_PATH', str(Path(__file__).with_name('portfolio.db'))))
SCHEMA = Path(__file__).with_name('schema.sql').read_text()


@contextmanager
def connection():
    # A fresh connection per operation; parameter binding is used for values.
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    try:
        with db:  # commits on success, rolls back on failure
            yield db
    finally:
        db.close()


def initialize():
    with connection() as db:
        db.executescript(SCHEMA)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize()
    yield


app = FastAPI(title='SQLite Portfolio Demo · Local Only', lifespan=lifespan)


class ProjectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    title: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    stars: int = Field(default=0, ge=0)


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    title: str = Field(min_length=1, max_length=100)
    stars: int = Field(ge=0)


class NoteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    body: str = Field(min_length=1, max_length=500)


@app.get('/projects')
def list_projects(q: str = Query(default='', max_length=100)):
    with connection() as db:
        rows = db.execute(
            'SELECT id, title, category, stars FROM projects WHERE title LIKE ? ORDER BY id',
            (f'%{q}%',),
        ).fetchall()
        return [dict(row) for row in rows]


@app.post('/projects', status_code=201)
def create_project(project: ProjectInput):
    with connection() as db:
        cursor = db.execute('INSERT INTO projects (title, category, stars) VALUES (?, ?, ?)',
                            (project.title, project.category, project.stars))
        return {'id': cursor.lastrowid, **project.model_dump()}


@app.patch('/projects/{project_id}')
def update_project(project_id: int, project: ProjectUpdate):
    with connection() as db:
        cursor = db.execute('UPDATE projects SET title = ?, stars = ? WHERE id = ?',
                            (project.title, project.stars, project_id))
        if cursor.rowcount == 0:
            raise HTTPException(404, 'Project not found')
        return dict(db.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone())


@app.delete('/projects/{project_id}', status_code=204)
def delete_project(project_id: int):
    with connection() as db:
        if db.execute('DELETE FROM projects WHERE id = ?', (project_id,)).rowcount == 0:
            raise HTTPException(404, 'Project not found')


@app.post('/projects/{project_id}/notes', status_code=201)
def create_note(project_id: int, note: NoteInput):
    with connection() as db:
        if not db.execute('SELECT 1 FROM projects WHERE id = ?', (project_id,)).fetchone():
            raise HTTPException(404, 'Project not found')
        cursor = db.execute('INSERT INTO notes (project_id, body) VALUES (?, ?)', (project_id, note.body))
        return {'id': cursor.lastrowid, 'project_id': project_id, 'body': note.body}


@app.get('/project-notes')
def project_notes():
    with connection() as db:
        return [dict(row) for row in db.execute('''
            SELECT projects.title, notes.body
            FROM projects JOIN notes ON projects.id = notes.project_id
            ORDER BY notes.id
        ''').fetchall()]
