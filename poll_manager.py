import json
import time

def create_poll(question, options, polls_file):
    polls = load_json(polls_file)
    poll_id = str(int(time.time()))  # Use timestamp as unique poll ID
    polls[poll_id] = {
        "question": question,
        "options": options,
        "votes": {str(i+1): [] for i in range(len(options))},
        "active": True
    }
    save_json(polls_file, polls)
    return poll_id

def vote_in_poll(poll_id, user, vote, polls_file):
    polls = load_json(polls_file)
    if poll_id not in polls or not polls[poll_id]["active"]:
        return
    # Prevent double voting
    for voters in polls[poll_id]["votes"].values():
        if user in voters:
            voters.remove(user)  # Remove previous vote
    polls[poll_id]["votes"][str(vote)].append(user)
    save_json(polls_file, polls)

def get_poll_results(poll_id, polls_file):
    polls = load_json(polls_file)
    if poll_id not in polls:
        return "❌ Poll not found."
    poll = polls[poll_id]
    results = f"📊 Poll Results: {poll['question']}\n"
    for i, option in enumerate(poll["options"], 1):
        votes = len(poll["votes"][str(i)])
        results += f"{i}. {option}: {votes} vote(s)\n"
    results += f"Status: {'Active' if poll['active'] else 'Closed'}"
    return results

def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)