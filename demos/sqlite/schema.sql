PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 100),
    category TEXT NOT NULL,
    stars INTEGER NOT NULL DEFAULT 0 CHECK(stars >= 0)
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    body TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notes_project_id ON notes(project_id);
