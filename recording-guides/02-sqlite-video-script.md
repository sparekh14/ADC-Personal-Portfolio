# Video 2 — Give your portfolio a memory with SQLite

**Audience:** ADC students who have built React components, used state, and seen a FastAPI endpoint.  
**Target:** 18–22 minutes including typing and pauses.  
**Result:** understand relational data; execute SQL CRUD and a join; call a FastAPI endpoint that persists portfolio projects.  
**Decision:** use SQLite for this first recording. It runs inside Python without provisioning a database server. Briefly position Postgres at the end.

The sample projects and star counts below are classroom data, not claims about Samarth's real GitHub projects.

## Before recording

- Open this repository in your editor. Use a large terminal/editor font and hide unrelated tabs.
- Have `demos/sqlite/schema.sql`, `lesson.sql`, and `main.py` ready.
- Use Python 3.12+ and the project virtual environment. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

- Verify the SQLite CLI with `sqlite3 --version`. Python's `sqlite3` module is independent of the CLI. If students lack the CLI, they can still complete the FastAPI portion with Python alone.
- Use a fresh teaching filename, such as `demos/sqlite/recording-take-1.db`. Choose a new take number if it exists. Do not open a personal or production database.
- For the API, use a separate fresh database so the prepared inserts do not conflict:

```bash
SQLITE_DEMO_PATH=demos/sqlite/api-take-1.db python -m uvicorn demos.sqlite.main:app --port 8001
```

- Open [Swagger UI](http://127.0.0.1:8001/docs). This write-enabled API is a local teaching demo and is separate from the public portfolio backend.

## 0:00–1:30 — Start with the problem

**Show:** the React portfolio and its project filter. Then show the SQLite demo's empty GET response in Swagger.

**Say:**

“Right now, React can remember things while our page is running. If I change some state, the screen updates. But React state is not a shared database. It doesn't automatically save a new project so that somebody else can load it tomorrow.

“Hardcoding projects is completely fine for a personal portfolio. Today we're learning what changes when the data needs to be stored and updated independently of the frontend.

“We'll give a small portfolio API a memory. We'll store projects in SQLite, read them back, update one, and prove the data survives restarting the server.”

**Point out:** the production portfolio uses GitHub as an external data source; this recording is a separate persistence lesson, not a requirement to put every portfolio section in a database.

## 1:30–3:30 — The request path and the relational model

**Show:** say or draw `React → FastAPI → SQLite file`, then reverse it for the response.

**Say:**

“The browser asks our API for data. FastAPI decides which query to run. SQLite reads a file on the backend machine, and our API sends JSON back to the browser. The browser never opens the database file directly.

“SQLite is the database engine. SQL is the language we use to ask questions about relational data. PostgreSQL is another database engine that also speaks SQL, with differences in syntax and behavior.

“A table groups records with named columns. In our projects table, each row is one project. The id identifies the row. The title and category describe it. Stars is just a demo number we'll update.

“A primary key identifies one record. A foreign key links a record to another table. We'll use that when we attach notes to projects.”

**Check:** “If I have five projects, how many rows do I have? Five. Adding another project normally adds a row; it doesn't add another title column.”

## 3:30–6:00 — Create the database and schema

**Type from the repo root:**

```bash
sqlite3 demos/sqlite/recording-take-1.db
```

**Then type in the SQLite prompt:**

```sql
.headers on
.mode column
.read demos/sqlite/schema.sql
.tables
.schema projects
```

**Show:** `schema.sql`. Highlight only the projects table first.

**Say:**

“Connecting to a filename creates the file if it doesn't exist. Our table definition names each column. `NOT NULL` means a value must be present. `DEFAULT 0` provides a starting value. This check rejects negative star counts.

“`INTEGER PRIMARY KEY` gives us an identifier that SQLite can generate when we leave it out of an insert. We shouldn't use the project title as an id: titles can change, and two people can choose the same title.

“`IF NOT EXISTS` makes initial startup repeatable. It does not migrate an existing table when we change its definition. Schema changes in a real application need a deliberate migration.”

**Point out:** notes and its index will be explained shortly. Do not teach every SQL datatype here. SQLite has flexible typing; declarations such as `INTEGER` do not imply PostgreSQL's exact type rules.

## 6:00–9:30 — CRUD, one operation at a time

**Type each block separately.** Do not run the entire lesson file at once during the explanation.

```sql
INSERT INTO projects (title, category, stars)
VALUES ('My Portfolio', 'Full stack', 0);

INSERT INTO projects (title, category, stars)
VALUES ('Study Cards', 'AI', 3);

SELECT * FROM projects;
```

**Say:**

“Create means insert a record. Read means select records. SQL keywords are conventionally uppercase here to make them easy to spot; that isn't what makes the query work.”

```sql
SELECT title, stars
FROM projects
WHERE stars >= 1
ORDER BY stars DESC;
```

**Say:**

“This reads like a question: give me the title and stars for projects with at least one star, highest first. `WHERE` filters rows. `ORDER BY` controls the order. Without an order, don't rely on a particular result order.”

**Expected:** only Study Cards, with 3 stars.

```sql
UPDATE projects SET stars = 5 WHERE id = 1;
SELECT * FROM projects WHERE id = 1;
```

**Say:**

“Update changes an existing row. Watch the `WHERE`: leaving it out updates every row. Before a large update, I can run a select with the same condition to see exactly what I intend to change.”

**Expected:** My Portfolio now has 5 stars.

**Preview deletion without running it yet:**

```sql
-- We'll run this at the end:
-- DELETE FROM projects WHERE id = 1;
```

“Delete removes matching rows. We'll wait until after our persistence check so there's still something to reload.”

## 9:30–12:00 — Relationships and one useful join

**Show:** the notes table in `schema.sql`.

**Say:**

“A project can have multiple notes. Rather than repeating the project's title in every note, each note stores a project id. That foreign key refers back to projects.

“SQLite foreign-key enforcement must be enabled on each connection. That's why you see `PRAGMA foreign_keys = ON` both in our schema session and in the Python connection helper.”

```sql
INSERT INTO notes (project_id, body)
VALUES (1, 'Add a live GitHub explorer');

SELECT projects.title, notes.body
FROM projects
JOIN notes ON projects.id = notes.project_id;
```

**Expected:** My Portfolio beside Add a live GitHub explorer.

**Say:**

“`JOIN` combines matching rows so I can show a project title next to its note. We stored the relationship once, then asked the database to follow it.

“`ON DELETE CASCADE` says that deleting a project also deletes its notes. That's an explicit choice for this demo. Another application might choose to reject the deletion instead.

“The index on project id helps SQLite find a project's notes efficiently as the table grows. Indexes can help reads, but they also take space and add work to writes.”

**Pause prompt:** “Add a note to Study Cards, then rerun the join. Which id should that note store?”

## 12:00–16:00 — Connect the database to FastAPI

**Switch to:** `demos/sqlite/main.py`. Stop on each relevant function instead of scrolling through the entire file.

**Say:**

“Our API receives ordinary HTTP requests and translates them into database operations. The database is behind the API. Let's trace one request.”

**Show `ProjectInput`:**

“Pydantic validates the request body: the title can't be blank, and stars can't be negative. This is application validation. Database constraints provide another layer of checks.”

**Show `connection()`:**

“We open a connection, enable foreign keys, and give it to the route. This context commits successful writes and rolls back a failing operation. The finally block closes the connection. Connections shouldn't be left open indefinitely.”

**Show `create_project()`:**

```python
cursor = db.execute(
    'INSERT INTO projects (title, category, stars) VALUES (?, ?, ?)',
    (project.title, project.category, project.stars),
)
```

“The question marks are placeholders. We pass the values separately so the driver treats a title as data. Don't build SQL by pasting user input into a query string. A title containing an apostrophe should be stored as a title, not change the SQL program.”

**Swagger sequence, on port 8001:**

1. `POST /projects`, Try it out, use:

```json
{"title":"Samarth's Portfolio","category":"Full stack","stars":0}
```

2. Execute. Point to **201**, the generated `id`, and the JSON body. Copy the actual id; do not assume it is 1.
3. `GET /projects`, Execute. Explain **200** and the list of records.
4. Set `q` to `Samarth`. Execute again and trace the `LIKE ?` query.
5. `PATCH /projects/{project_id}`, paste that id and:

```json
{"title":"Portfolio v2","stars":5}
```

6. Try a negative stars value once. Show **422** and explain validation, then restore the valid value.

**Say:**

“In React, a fetch to our own `/projects` endpoint would receive this same JSON. We would place the result in state and map the list into cards. A refresh should load the saved records from the API.”

## 16:00–18:00 — Prove persistence and finish CRUD

**Do:** stop the API with Ctrl+C, restart using the exact same `SQLITE_DEMO_PATH`, and execute GET again.

**Say:**

“The Python process stopped. Its in-memory variables are gone. But the project is still here because it was committed to the database file. This is the difference we wanted to demonstrate.”

**Then:** DELETE the exact API project id using Swagger. Show **204** and then GET returning an empty list in the fresh API database. Repeat DELETE once to show **404**.

**Return to CLI:**

```sql
.quit
```

Reopen the same CLI database filename and run `SELECT * FROM projects;`. Then delete id 1 and show its note disappeared too. Keep the CLI and API filenames visibly distinct.

## 18:00–20:00 — SQLite versus Postgres, and the assignment

**Say:**

“SQLite is a real database and a good fit for local tools, small applications, and this lesson. It runs in the application process and stores data in a file. Multiple readers can work concurrently, but SQLite serializes writes.

“Postgres runs as a separate database server. It's often a better fit when many application instances need to share a database or when the workload and database features call for it. It adds setup: a server, users, credentials, and a connection string.

“The ideas we learned carry over: tables, primary keys, joins, transactions, and parameterized queries. Moving to Postgres still requires checking SQL differences and migrating the data. It's not always a one-line switch.

“Your challenge is to store two projects, read them through FastAPI, update one, and restart the server to prove the data persists. If you're comfortable with that, add a related table and a join.”

**Closing:**

“In the MongoDB video, we'll use similar portfolio data to explore a different data model: documents, arrays, and nested objects.”

## Recovery notes

- `no such table`: run the schema or let the API's startup initialize the correct file. Print the configured path if you opened the wrong database.
- Data disappeared: check that both runs used the same `SQLITE_DEMO_PATH`; an in-memory database or different filename is a different database.
- `UNIQUE constraint failed` using `lesson.sql`: it deliberately uses ids 1 and 2. Choose a fresh demo filename for a new take.
- `database is locked`: finish/commit an open write transaction in the other process. Do not delete the database file while it is open.
- API import error: launch from the repository root with the virtual environment activated.

## Source notes

Verified against the official [Python sqlite3 documentation](https://docs.python.org/3/library/sqlite3.html), [SQLite foreign-key documentation](https://www.sqlite.org/foreignkeys.html), and [SQLite's appropriate-use guidance](https://www.sqlite.org/whentouse.html). The supplied videos were not available in the request; this script follows the topic list and existing ADC curriculum context.
