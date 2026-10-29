// mongosh --file demos/mongodb/lesson.js
// Dedicated, disposable classroom database. This does not drop existing data.
const demo = db.getSiblingDB('portfolio_bootcamp_demo');
const result = demo.projects.insertOne({
  title: 'My Portfolio',
  category: 'Full stack',
  stars: 0,
  technologies: ['React', 'FastAPI'],
  notes: [{ body: 'Add a live GitHub explorer' }],
  created_at: new Date(),
});
const id = result.insertedId;
print('New document ID:', id);
printjson(demo.projects.findOne({ _id: id }));
printjson(demo.projects.find({ technologies: 'React' }).toArray());
demo.projects.updateOne({ _id: id }, { $set: { stars: 5 } });
printjson(demo.projects.findOne({ _id: id }));
// Stop here to demonstrate persistence. Delete this exact document afterward:
// demo.projects.deleteOne({ _id: id });
