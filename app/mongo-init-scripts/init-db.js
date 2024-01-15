// initialization of the database
db = db.getSiblingDB('projectDb');

// Adding indexes for quicker lookups
db.projects.createIndex({ "project_id": 1 });
db.documents.createIndex({ "document_id": 1 });
db.annotations.createIndex({ "annotation_id": 1 });
db.annotations.createIndex({ "document_id": 1 });

// attack flow projects initialization
db.createCollection("projects");
db.createCollection("documents");
db.createCollection("annotations");

// test for data base connection
db.users.insert({
    type: "admin",
    name: "admin"
});

