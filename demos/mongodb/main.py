"""Local teaching API: python -m uvicorn demos.mongodb.main:app --port 8002."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from pymongo import MongoClient, ReturnDocument


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One pooled client per process, closed during shutdown.
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017'), serverSelectionTimeoutMS=3000)
    try:
        client.admin.command('ping')
        db_name = os.getenv('MONGODB_DATABASE', 'portfolio_bootcamp_demo')
        app.state.projects = client[db_name].projects
        yield
    finally:
        client.close()


app = FastAPI(title='MongoDB Portfolio Demo · Local Only', lifespan=lifespan)


class ProjectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    title: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    stars: int = Field(default=0, ge=0)
    technologies: list[str] = Field(default_factory=list, max_length=20)


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    title: str = Field(min_length=1, max_length=100)
    stars: int = Field(ge=0)


def object_id(value: str):
    if not ObjectId.is_valid(value):
        raise HTTPException(400, 'Invalid project ID')
    return ObjectId(value)


def serialize(document):
    return {**document, '_id': str(document['_id'])}


@app.get('/projects')
def list_projects(q: str = Query(default='', max_length=100), technology: str | None = None):
    # Accept typed values, never a raw MongoDB filter from the browser.
    criteria = {}
    if technology:
        criteria['technologies'] = technology  # array membership
    documents = app.state.projects.find(criteria).sort('created_at', -1).limit(100)
    return [serialize(doc) for doc in documents if q.lower() in doc['title'].lower()]


@app.post('/projects', status_code=201)
def create_project(project: ProjectInput):
    document = {**project.model_dump(), 'created_at': datetime.now(timezone.utc)}
    result = app.state.projects.insert_one(document)
    document['_id'] = result.inserted_id
    return serialize(document)


@app.patch('/projects/{project_id}')
def update_project(project_id: str, project: ProjectUpdate):
    document = app.state.projects.find_one_and_update(
        {'_id': object_id(project_id)}, {'$set': project.model_dump()},
        return_document=ReturnDocument.AFTER,
    )
    if not document:
        raise HTTPException(404, 'Project not found')
    return serialize(document)


@app.delete('/projects/{project_id}', status_code=204)
def delete_project(project_id: str):
    result = app.state.projects.delete_one({'_id': object_id(project_id)})
    if not result.deleted_count:
        raise HTTPException(404, 'Project not found')
