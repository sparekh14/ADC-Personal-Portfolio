-- In sqlite3: .read demos/sqlite/schema.sql
-- Then: .read demos/sqlite/lesson.sql
-- Disposable classroom data only. Start with a fresh demo DB before recording.
INSERT INTO projects (id, title, category, stars) VALUES
    (1, 'My Portfolio', 'Full stack', 0),
    (2, 'Study Cards', 'AI', 3);
SELECT * FROM projects;
SELECT title, stars FROM projects WHERE stars >= 1 ORDER BY stars DESC;
UPDATE projects SET stars = 5 WHERE id = 1;
INSERT INTO notes (project_id, body) VALUES (1, 'Add a live GitHub explorer');
SELECT projects.title, notes.body
FROM projects JOIN notes ON projects.id = notes.project_id;
-- Run DELETE manually at the end so persistence can be shown first:
-- DELETE FROM projects WHERE id = 1;
