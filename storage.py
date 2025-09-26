import json

def load_json(fname):
    try:
        with open(fname,"r") as f:
            return set(json.load(f))
    except:
        return set()

def save_json(fname, data_set):
    with open(fname,"w") as f:
        json.dump(list(data_set), f)
