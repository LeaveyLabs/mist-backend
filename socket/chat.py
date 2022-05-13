import asyncio
from ntpath import join
from time import time
from tracemalloc import start

import websockets
import json
import requests
from decouple import config

# two-dimensional, two conversation participants
CONVERSATION_BETWEEN = {}
REQUESTS_URL = "http://localhost:8000/api/messages/"

def process_convo_init_json(convo_init_json):
    try:
        valid_convo_init_obj = json.loads(convo_init_json)
        assert valid_convo_init_obj["type"] == "init"
        assert valid_convo_init_obj["from_user"] != None
        assert valid_convo_init_obj["to_user"] != None
        return valid_convo_init_obj, None
    except json.decoder.JSONDecodeError as e:
        return None, e
    except KeyError as e:
        return None, e

def process_message_json(message_json):
    try:
        valid_message_obj = json.loads(message_json)
        assert valid_message_obj["type"] == "message"
        assert valid_message_obj["from_user"] != None
        assert valid_message_obj["to_user"] != None
        assert valid_message_obj["text"] != None
        return valid_message_obj, None
    except json.decoder.JSONDecodeError as e:
        return None, e
    except KeyError as e:
        return None, e

async def error(websocket, message):
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))

async def execute_conversation(websocket, connected):
    """
    Receive and process messages from a user.

    """
    async for message in websocket:
        # Load JSON of the event
        valid_message_obj, e = process_message_json(message)
        # If improperly formatted, throw back error
        if not valid_message_obj:
            await error(websocket,
            "Improperly formatted message... JSON Error: {}".format(e))
        else: 
            valid_message_obj["timestamp"] = time()
            # Post to database
            r = requests.post(REQUESTS_URL, data=valid_message_obj)
            print(r.text)
            # Broadcast to all connected sockets
            websockets.broadcast(connected, json.dumps(valid_message_obj))

async def start_conversation(websocket, user1, user2):
    if user1 not in CONVERSATION_BETWEEN: CONVERSATION_BETWEEN[user1] = {}
    try:
        CONVERSATION_BETWEEN[user1][user2] = {websocket}
        await websocket.send("Beginning conversation between {} and {}".format(user1, user2))
        await execute_conversation(websocket, CONVERSATION_BETWEEN[user1][user2])
    finally:
        del CONVERSATION_BETWEEN[user1][user2]

async def join_conversation(websocket, user1, user2):
    try:
        CONVERSATION_BETWEEN[user1][user2].add(websocket)
        await websocket.send("Joining conversation between {} and {}".format(user1, user2))
        await execute_conversation(websocket, CONVERSATION_BETWEEN[user1][user2])
    finally:
        CONVERSATION_BETWEEN[user1][user2].remove(websocket)

async def handler(websocket):
    """
    Handle a connection and dispatch it according to who is connecting.

    """
    convo_init_json = await websocket.recv()
    valid_convo_init_obj, e = process_convo_init_json(convo_init_json)
    # Only process valid conversation initalization requests
    if not valid_convo_init_obj:
        await error(websocket, "Could not instantiate conversation... JSON Error: {}".format(e))
        return
    
    # To standardize the socket indexing, 
    # the user earlier in the alphabet will be the first layer
    # the user later in the alphabet will be the second layer
    users = [valid_convo_init_obj["from_user"], valid_convo_init_obj["to_user"]]
    users.sort()
    user1, user2 = users
    
    # Either start or join a conversation
    conversation_started = (user1 in CONVERSATION_BETWEEN and 
                            user2 in CONVERSATION_BETWEEN[user1] and 
                            CONVERSATION_BETWEEN[user1][user2])
    if conversation_started: await join_conversation(websocket, user1, user2)
    else: await start_conversation(websocket, user1, user2)

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())