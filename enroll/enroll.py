import verification
import pymongo
import datetime

CONNECTION_STRING = "mongodb://localhost:27017"
client = pymongo.MongoClient(CONNECTION_STRING)
dbname = client['dbms_miniproject']
collection_name = dbname["voter"]

first_name = input("Enter first name: ")
last_name = input("Enter last name: ")
aadhaar_no = int(input("Enter Aadhaar number: "))
dob = datetime.datetime.fromisoformat(input("Enter DOB (YYYY-MM-DD): "))
template = verification.get_template()

voter = {
    'aadhaar_no' : aadhaar_no,
    'first_name' : first_name,
    'last_name' : last_name,
    'dob' : datetime.datetime.fromisoformat(dob.isoformat()),
    'template' : template
}
    
collection_name.insert_one(voter)
