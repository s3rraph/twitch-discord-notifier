import requests
import os
from dotenv import load_dotenv
import asyncio
import time

# Load environment variables
load_dotenv()

TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_SECRET = os.getenv('TWITCH_SECRET')
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
GAME_NAME = os.getenv('GAME_NAME')

# Dictionary to track streams and their last seen timestamp
tracked_streams = {}

def get_twitch_token():
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, params=params)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()['access_token']

def get_game_id(game_name):
    token = get_twitch_token()
    url = 'https://api.twitch.tv/helix/games'
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    params = {'name': game_name}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    if data['data']:
        return data['data'][0]['id']
    return None

def get_streams(game_id, max_streams=100):
    token = get_twitch_token()
    url = 'https://api.twitch.tv/helix/streams'
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    params = {'game_id': game_id, 'first': 100}
    
    all_streams = []
    while len(all_streams) < max_streams:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        streams = data.get('data', [])
        all_streams.extend(streams)

        if len(streams) < params['first'] or len(all_streams) >= max_streams:
            break

        cursor = data.get('pagination', {}).get('cursor')
        if not cursor:
            break
        params['after'] = cursor

    return all_streams[:max_streams]

def post_to_discord(message):
    data = {
        "content": message,
        "username": "Twitch Stream Notifier"
    }    
    
    response = requests.post(WEBHOOK_URL, json=data)
    response.raise_for_status()  # Raise an error for bad responses
    
async def check_streams():
    game_id = get_game_id(GAME_NAME)
    if not game_id:
        print(f"Could not find game with name: {GAME_NAME}")
        return


    
    # Initialization step: Populate tracked_streams with current streams using usernames
    initCount=3
    print("Starting in") # Wait before checking for new streams    
    for x in range(initCount):
        print(initCount-x)
        await asyncio.sleep(1) 
        initial_streams = get_streams(game_id, max_streams=200)
        current_time = time.time()
        new_streams = [stream['user_name'] for stream in initial_streams if stream['user_name'].lower() not in tracked_streams]
        print(new_streams)
        for stream in initial_streams:
            tracked_streams[stream['user_name'].lower()] = current_time  # Use lowercased usernames for consistency
            
        
        
    print(f"Found {len(tracked_streams)} preexisting streams")    
    print("Initialization complete")
    
    
    
    while True:
        current_time=time.time()
        streams = get_streams(game_id, max_streams=200)
        current_usernames = [stream['user_name'].lower() for stream in streams]  # Lowercase for consistency
        new_streams = [stream for stream in streams if stream['user_name'].lower() not in tracked_streams]
        
        print(f"Checking for new streams... ( Existing : {len(tracked_streams)} , New : {len(new_streams)} )")
        
        # Update tracked_streams with the current streams
        for username in current_usernames:
            if username in tracked_streams:
                tracked_streams[username] = current_time

        # Cleanup old streams that are no longer broadcasting
        cleanup_streams(3600)
        
        # Add new streams to be tracked and send discord notification
        if new_streams:
            new_usernames = [stream['user_name'].lower() for stream in new_streams]  # Lowercase for consistency
            print(f" Adding new streams: {', '.join(new_usernames)}")
        for stream in new_streams:
            message = f"New stream found: {stream['title']} by {stream['user_name']}. Watch at https://www.twitch.tv/{stream['user_name']}"
            post_to_discord(message)
            tracked_streams[stream['user_name'].lower()] = current_time  # Ensure new streams are marked with the current time
            
        await asyncio.sleep(60)  # Wait before checking for new streams
        

def cleanup_streams(age_limit=3600):
    """Remove streams that have not been seen for more than age_limit seconds and log their names."""
    global tracked_streams
    current_time = time.time()
    streams_to_remove = [username for username, timestamp in tracked_streams.items() if current_time - timestamp > age_limit]
    
    # Log the usernames of streams being removed
    if streams_to_remove:
        print(f" Removing streams that are no longer active: {', '.join(streams_to_remove)}")
    
    # Update the tracked_streams by excluding the ones to be removed
    tracked_streams = {username: timestamp for username, timestamp in tracked_streams.items() if current_time - timestamp <= age_limit}



if __name__ == "__main__":
    asyncio.run(check_streams())
