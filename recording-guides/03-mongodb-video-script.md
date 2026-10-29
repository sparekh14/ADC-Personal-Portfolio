# Video 3 — Store portfolio projects as MongoDB documents

**Audience:** ADC students who know React state, a FastAPI route, and basic SQL CRUD from the previous video.  
**Target:** 18–22 minutes including typing and pauses.  
**Result:** connect to MongoDB, explain documents/collections/ObjectIds, demonstrate CRUD and array queries, then return data through FastAPI.

The project names and star counts here are disposable classroom examples. This demo does not write to the public portfolio or GitHub.

## Before recording

Your machine has `mongod` and `mongosh` installed. Use a dedicated new local data directory and port so the recording does not depend on an existing service. Keep this terminal running:

```bash
mkdir -p /tmp/adc-mongo-recording-data
mongod --dbpath /tmp/adc-mongo-recording-data --bind_ip 127.0.0.1 --port 27018
```

In a second terminal:

```bash
mongosh mongodb://127.0.0.1:27018
```

If `/tmp/adc-mongo-recording-data` already contains a previous take, choose a new directory or intentionally reuse that disposable data. `/tmp` is temporary and may be cleared by the OS; use a normal project-local folder for a lasting application.

**Alternative for students with Docker:**

```bash
docker compose -f demos/compose.yaml up -d
mongosh mongodb://127.0.0.1:27017
```

The Docker example uses a named volume. `docker compose ... down` preserves it; adding `-v` removes the demo volume. Show the native route in this recording because it is already installed on your machine; students can choose Docker or Atlas.

From the repository root, prepare the API:

```bash
source .venv/bin/activate
python -m pip install -r demos/mongodb/requirements.txt
MONGODB_URI=mongodb://127.0.0.1:27018 python -m uvicorn demos.mongodb.main:app --port 8002
```

Have `demos/mongodb/lesson.js`, `main.py`, and [Swagger UI](http://127.0.0.1:8002/docs) ready. This is a local teaching API; it is separate from the public read-only portfolio backend.

## 0:00–1:30 — Connect the lesson to the portfolio

**Show:** one project card and its corresponding JSON in the editor.

**Say:**

“In the SQL video, we stored a project as a row in a table. Now imagine that project also has a list of technologies and a few notes. That's already close to the JavaScript objects we've been using in React.

“MongoDB lets us store documents with fields, arrays, and nested objects. We'll use the same basic project idea so we can focus on what changes in the data model.

“We're still using the same overall architecture: the browser asks FastAPI, FastAPI talks to the database, and the API returns JSON. Switching databases doesn't mean giving the browser our database password.”

## 1:30–4:00 — Database, collection, document

**In mongosh:**

```javascript
use portfolio_bootcamp_demo
```

**Say:**

“MongoDB organizes collections inside a database. A collection groups documents, such as our projects. A document describes one project.

“Those concepts are roughly comparable to a database, a table, and a row, but the structure isn't identical. A document can contain an array or an embedded object. MongoDB stores BSON, a binary format with more types than ordinary JSON. ObjectId and dates are two examples we'll see.

“MongoDB has a flexible schema. That doesn't mean our application has no structure or that every shape is useful. We'll still validate incoming data with Pydantic. MongoDB also supports collection-level schema validation.”

**Show but don't insert yet:**

```javascript
{
  title: 'My Portfolio',
  category: 'Full stack',
  stars: 0,
  technologies: ['React', 'FastAPI'],
  notes: [{ body: 'Add a live GitHub explorer' }]
}
```

“The technologies are an array of strings. Notes is an array of objects. For a few notes we normally read with the project, embedding can be convenient. We wouldn't put an unbounded stream of comments inside a single project document.”

## 4:00–6:00 — Create a document and inspect the id

**Type in mongosh:**

```javascript
const result = db.projects.insertOne({
  title: 'My Portfolio',
  category: 'Full stack',
  stars: 0,
  technologies: ['React', 'FastAPI'],
  notes: [{ body: 'Add a live GitHub explorer' }],
  created_at: new Date()
});
const projectId = result.insertedId;
result
```

**Say:**

“We didn't create a table first. MongoDB creates the collection on the first insert if it doesn't exist.

“Every document has an `_id`. If we don't provide it, the driver normally generates an ObjectId. The inserted id tells us exactly which document this operation created. We'll keep it so our update and delete target one known document.”

```javascript
db.projects.findOne({ _id: projectId })
```

**Point out:** the actual generated id, array brackets, nested notes, and date value. Avoid implying ObjectId is just an auto-incrementing SQL integer or a plain string internally.

## 6:00–9:00 — Read, filter, project fields

```javascript
db.projects.find({})
db.projects.find({ category: 'Full stack' })
db.projects.find({ technologies: 'React' })
db.projects.find({ stars: { $gte: 1 } })
```

**Say:**

“The object we pass to find is a filter. An empty filter matches every document. Category equality matches a field value. For the technologies array, this query matches documents containing React.

“`$gte` means greater than or equal. Our project starts at zero, so the last query shouldn't return it yet. That empty result is expected.”

```javascript
db.projects.find(
  { category: 'Full stack' },
  { title: 1, technologies: 1, _id: 0 }
)
```

“The second object is a projection. It controls which fields come back. Here I only want title and technologies, so I explicitly leave out `_id`.”

**Pause prompt:** “Add another project whose technologies include Python. Write a query that returns Python projects.”

**If the collection is from an earlier take:** explain that extra records are previous demo data; use the stored `projectId` to keep this walkthrough precise. Do not drop a database to make the screen look tidy.

## 9:00–11:00 — Update and the meaning of `$set`

```javascript
db.projects.updateOne(
  { _id: projectId },
  { $set: { stars: 5 } }
)
db.projects.findOne({ _id: projectId })
```

**Say:**

“The first object identifies the document. The second describes the update. `$set` changes the named field while keeping the other fields.

“Look at `matchedCount` and `modifiedCount`. If nothing matched, we may have used the wrong id. If it matched but didn't modify, the field might already have that value.”

```javascript
db.projects.updateOne(
  { _id: projectId },
  { $addToSet: { technologies: 'MongoDB' } }
)
```

“`$addToSet` adds an array value if it isn't already present. `$push` would append without that same duplicate check. These operations are useful because we can change part of a document without reading it into Python and rewriting the whole thing.”

**Briefly show:** `find({ stars: { $gte: 1 } })` now returns the document.

## 11:00–13:00 — Modeling and indexes

**Say:**

“In SQL we separated notes and joined them to projects. Here we embedded a few notes directly. Neither layout wins for every situation. Start with how you read and update the data.

“If a project always loads a small amount of related data, embedding may make that read simple. If the related data grows without a useful bound, is shared across many records, or has its own lifecycle, separate collections and references may fit better. MongoDB also has aggregation and `$lookup`; saying MongoDB can't join data would be inaccurate.

“MongoDB isn't automatically faster because it's NoSQL. Query design, indexes, workload, and data shape all matter.”

**Optional 30-second index demonstration:**

```javascript
db.projects.createIndex({ category: 1 })
db.projects.getIndexes()
```

“This index can help category lookups as the collection grows. In our tiny demo, a database may still choose a collection scan. Indexes cost storage and write work; don't index every field by default.”

## 13:00–17:00 — Connect FastAPI with PyMongo

**Show:** `demos/mongodb/main.py`.

**Say:**

“PyMongo is the Python driver. MongoDB is the database. FastAPI is our HTTP layer. Each has a different job.

“We create one MongoClient for the API process, reuse its connection pool, and close it at shutdown. The startup ping catches a stopped database or a bad connection string before we record requests.”

**Point to:** `MONGODB_URI`, the selected database, and `app.state.projects`.

“The URI comes from the server environment. In our local demo it contains a localhost address. An Atlas connection string can contain credentials, so keep it out of React, browser code, recordings, and git.”

**Show the input model:**

“Pydantic gives our API an expected shape even though the database supports flexible documents. Title, category, stars, and technologies have deliberate types and limits.”

**Trace create:**

```python
result = app.state.projects.insert_one(document)
```

“This resembles insertOne in the shell, using Python's naming convention. Before returning the record, we convert ObjectId to a string because ordinary JSON doesn't have an ObjectId type.”

**Trace lookup/update:**

```python
{'_id': ObjectId(project_id)}
```

“The URL carries a string. The stored `_id` is an ObjectId. We validate the string, then convert it. Searching for an ObjectId using a plain string won't match the same way.”

**Swagger sequence on port 8002:**

1. POST `/projects`:

```json
{"title":"API Portfolio","category":"Full stack","stars":0,"technologies":["React","FastAPI","MongoDB"]}
```

2. Show **201**; copy the actual `_id`.
3. GET `/projects` with `technology=React`. Point out the array-membership filter in Python.
4. PATCH `/projects/{project_id}`:

```json
{"title":"API Portfolio v2","stars":5}
```

5. Show that technologies remain; `$set` didn't replace the document.
6. Try an invalid ObjectId once and show **400**. A valid but nonexistent id produces **404**. Invalid bodies produce **422**.

**Say:**

“We build database filters from validated values. We do not accept an arbitrary MongoDB query object from the browser and pass it straight to the driver.”

## 17:00–19:00 — Persistence and delete

**Do:** stop only the FastAPI server, restart it with the same URI, and GET again.

**Say:**

“The API process restarted, but MongoDB is still running and the project is still there. The data belongs to the database. Stopping MongoDB and restarting it with the same data directory also preserves committed data; choosing a different data directory gives us a different database.”

**Then:** DELETE the API-created id in Swagger. Show **204**, then GET to confirm it is gone. The earlier shell-created project can still exist; explain that it is a different document.

**In mongosh, delete only the shell-created record:**

```javascript
db.projects.deleteOne({ _id: projectId })
```

“Delete uses a filter too. An empty filter with deleteMany would remove every document in the collection, so that's not a command we need for this lesson.”

## 19:00–21:00 — Compare and give students a concrete task

**Say:**

“SQLite gave us tables, rows, constraints, SQL queries, and a join. MongoDB gave us collections, documents, nested data, and document queries. Both support persistent storage, indexes, and ways to enforce data structure.

“Choose based on your relationships, query patterns, consistency needs, and deployment constraints. Don't choose MongoDB just because React uses JavaScript, and don't assume SQL databases can't store JSON.

“Your challenge is to create two projects with technologies arrays, query for one technology, update a field, restart FastAPI to prove persistence, and delete the exact document you created. Explain one reason you'd embed data and one reason you'd store references instead.”

**Closing:**

“The architecture stays familiar: a request comes in, our backend performs a database operation, and JSON comes back. You now have two ways to give your application a memory.”

## Recovery notes

- Connection refused / server-selection timeout: keep `mongod` running and check the URI's port. The recording uses **27018**; Docker defaults to **27017**.
- API startup error: confirm `MONGODB_URI` is set in the same terminal launching uvicorn. A shell variable in another terminal isn't automatically inherited.
- Update matched zero: check collection/database, id, and ObjectId conversion.
- `projectId` undefined after reopening mongosh: shell variables do not persist. Find your demo by title, inspect the result, then save its actual `_id` again.
- Atlas option: create a database user, allow the current IP, and set the URI in the backend environment. Do those account/setup steps off-camera; do not expose passwords or broaden access to all IPs just to finish a recording.
- Keep this unauthenticated write API local. A public write API needs authentication, authorization, and appropriate abuse controls before deployment.

## Source notes

Verified against official [mongosh CRUD documentation](https://www.mongodb.com/docs/mongodb-shell/crud/), [PyMongo inserts](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/insert/), and [MongoDB data modeling](https://www.mongodb.com/docs/manual/data-modeling/). The supplied videos were not available in the request; this script follows the topic list and ADC curriculum context.
