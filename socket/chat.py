import asyncio
from time import time

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

async def begin_conversation(websocket, connected):
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

async def handler(websocket):
    """
    Handle a connection and dispatch it according to who is connecting.

    """
    convo_init_json = await websocket.recv()
    valid_convo_init_obj, e = process_convo_init_json(convo_init_json)
    if not valid_convo_init_obj:
        await error(websocket,
        "Could not instantiate conversation... JSON Error: {}".format(e))
        return

    user1 = valid_convo_init_obj["from_user"]
    user2 = valid_convo_init_obj["to_user"]

    user1_started_conversation = user1 in CONVERSATION_BETWEEN and user2 in CONVERSATION_BETWEEN[user1]
    user2_started_conversation = user2 in CONVERSATION_BETWEEN and user1 in CONVERSATION_BETWEEN[user2]

    # Do not let user1 start the conversation again if they've already started the conversation.
    if user1_started_conversation:
        await error(websocket,
        "Conversation has already been started.")
        return

    # Either start a new conversation or join user2's conversation.
    if not user2_started_conversation:
        CONVERSATION_BETWEEN[user1] = {}
        CONVERSATION_BETWEEN[user1][user2] = {websocket}
        await websocket.send("Beginning conversation from {} to {}".format(user1, user2))
        await begin_conversation(websocket, CONVERSATION_BETWEEN[user1][user2])
    
    elif user2_started_conversation:
        CONVERSATION_BETWEEN[user2][user1].add(websocket)
        await websocket.send("Beginning conversation from {} to {}".format(user1, user2))
        await begin_conversation(websocket, CONVERSATION_BETWEEN[user2][user1])

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())