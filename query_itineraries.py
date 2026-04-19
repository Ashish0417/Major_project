from pymongo import MongoClient
db = MongoClient().travel_planner
it = db.itineraries.find_one()
if it:
    print("KEYS:", it.keys())
    print("DAILY:", "yes" if 'daily_schedules' in it else "no")
    if 'daily_schedules' in it and it['daily_schedules']:
        print("FIRST DAY KEYS:", it['daily_schedules'][0].keys() if isinstance(it['daily_schedules'][0], dict) else "Not dict")
