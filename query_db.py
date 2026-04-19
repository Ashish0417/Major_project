from pymongo import MongoClient
db = MongoClient().travel_planner
print('CONVERSATIONS:', db.conversations.count_documents({}))
c = db.conversations.find_one()
if c:
    prompt = c.get('response', '')
    print('First conv len:', len(prompt), 'Preview:', prompt[:200])
