import os
from pymongo import MongoClient

def run():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["secop"]
    col = db["contratos-electronicos"]

    # Let's see if we have any data to test with
    print("Count:", col.estimated_document_count())

run()
