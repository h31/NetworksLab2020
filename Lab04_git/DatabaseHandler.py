from bson import json_util
from pymongo import MongoClient

client = MongoClient('localhost', 27017)

db = client['ParkingService']
col = db['Collection0']


def addToDB(data):
    return col.insert_one(data).inserted_id


def getFromDB(elements, multiple=False):
    if multiple:
        results = col.find(elements)
        return [r for r in results]
    else:
        return col.find_one(elements)


def parseJSON(data):
    return json_util.dumps(data)
