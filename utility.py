import ujson
import json
from colorama import Fore

def load_data(user_id: int) -> dict:
    try: #if we have file for user, we load data
        user_file = open("users/" + str(user_id) + ".json", "r")
        user_data = ujson.load(user_file)
        user_file.close()
        return user_data
    except: # if not we create new file
        data = [{
            "records": 1, 
            "user_id": user_id, 
            "exchange_currency": "", 
            "period": 0, 
            "username": ""
            }]
        dump_data(user_data=data)
        
        print(Fore.GREEN, "File for new user ({0}) was create".format(str(user_id)))
        


def dump_data(user_data):
    try:
        with open("users/" + str(user_data[-1]["user_id"]) + ".json", "w") as file:
            json.dump(user_data, file)   
    except:
        print(Fore.RED, "Some problem. Try again")
        