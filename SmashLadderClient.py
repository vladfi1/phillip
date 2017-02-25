import asyncio
import json
import requests # pip install requests
import websockets # pip install websockets
from enum import IntEnum

class Characters(IntEnum):
    bowser = 43
    captain_falcon = 48
    donkey_kong = 49
    dr_mario = 58
    falco = 59
    fox = 50
    ganondorf = 60
    ice_climbers = 44
    jigglypuff = 61
    kirby = 51
    link = 52
    luigi = 62
    mario = 53
    marth = 63
    mewtwo = 64
    mr_game_and_watch = 65
    ness = 54
    peach = 45
    pichu = 66
    pikachu = 55
    random = 69
    roy = 67
    samus = 56
    sheik = 46
    yoshi = 57
    young_link = 68
    zelda = 47
    unknown = 0

class Stages(IntEnum):
    yoshis_story = 43
    fountain_of_dreams = 44
    battlefield = 45
    final_destination = 46
    dream_land = 47
    pokemon_stadium = 48

class Actions(IntEnum):
    player_1_strike_stage = 1
    player_2_strike_stage = 2
    player_1_pick_character = 3
    player_2_pick_character = 4
    players_blind_pick_characters = 5
    players_play_game = 6
    player_1_pick_stage = 7
    player_2_pick_stage = 8
    game_over = 9
    dispute = 10
    # I don't know what 11 and 12 are used for, but they're in the SmashLadder source code.
    # Maybe they're for Smash 4 or something. I don't know if the ruleset is different.
    player_1_ban_stage = 11
    player_2_ban_stage = 12
    # Nice.
    play_rps = 13

class GameResult(IntEnum):
    lose = 1
    win = 2
    cancel = 3
    finished = 4
    disputed = 5

class Feedback(IntEnum):
    positive = 1
    neutral = 0
    negative = -1

class SmashLadderClient():
    base_url = "https://www.smashladder.com/"
    socket_url = "wss://www.smashladder.com/?type=3&version=9.11.4&userlist_visible=false"

    def __init__(self):
        self.cookies = None
        self.current_search = None
        self.last_match = None
        self.current_match = None
        self.user_id = None

    def on_logged_in(self):
        return

    def on_connected(self):
        return

    def on_challenged(self, challenges):
        return

    def on_game_updated(self, match):
        return

    def on_game_ended(self, match):
        return
    
    def on_match_chat_recieved(self, message, match_id):
        return

    def on_search_created(self, match):
        return

    def on_socket_updated(self):
        return

    def process_message(self, input):
        if "searches" in input:
            for id in [key for key in input["searches"] if key != "all_entries"]:
                # Check if the current search has been removed.
                if ("is_removed" in input["searches"][id]) and (input["searches"][id]["is_removed"] == 1):
                    if self.current_search == id:
                        self.current_search = None
                else:
                    self.on_search_created(input["searches"][id])

        if "open_challenges" in input:
            for id in input["open_challenges"]:
                if id != "all_entries":
                    self.on_challenged(input["open_challenges"][id])

        if "current_matches" in input:
            # This dictionary will never contain more than one match (and the all_entries key).
            # ...Unless the Smash Ladder bugs out. That's not our fault.
            for id in input["current_matches"]:
                if id != "all_entries":
                    # Check if the input contains chat, but also make sure it contains only chat.
                    # If it contains match data, then it's the message sent when a client reconnects for the first time.
                    # Not checking for this would result in previously-sent messages being processed again.
                    if ("chat" in input["current_matches"][id]) and not ("id" in input["current_matches"][id]):
                        chat = input["current_matches"][id]["chat"]["chat_messages"]

                        # If the type is list, then the message only contains "<player> is typing..." data.
                        if type(chat) is dict:
                            message = chat[list(chat.keys())[0]]
                            if str(message["player"]["id"]) != self.user_id:
                                # Chat messages don't contain any match data, so we have to manually send the ID.
                                self.on_match_chat_recieved(message["message"], id)

                    if "end_phase" in input["current_matches"][id]:
                        if input["current_matches"][id]["end_phase"] == 0:
                            self.current_match = id

                            self.on_game_updated(input["current_matches"][id])

                        else:
                            if id != self.last_match:
                                self.on_game_ended(input["current_matches"][id])

                                self.finish_match(id)

                                self.last_match = self.current_match
                                self.current_match = None
        
        self.on_socket_updated()

    def log_in(self, username, password):
        data = {
            "username": username,
            "password": password,
            "remember": "0",
            "json": "1"
        }
        response = self.post("log-in", data=data)
        if not response.json()["success"]:
            raise ValueError(response.json()["error"])

        # The reponse, if successful, will have cookies as headers which can be used for authentication.
        # This includes the user's ID (lad_sock_user_id) and authentication hash (lad_sock_hash).
        self.cookies = response.cookies.get_dict()
        self.user_id = self.cookies["lad_sock_user_id"]
        self.on_logged_in()
        asyncio.get_event_loop().run_until_complete(self.start_socket())
        
    async def start_socket(self):
        # The websocket requires authentication.
        header = [("Cookie", "lad_sock_user_id={0}; lad_sock_hash={1}".format(self.cookies["lad_sock_user_id"], self.cookies["lad_sock_hash"]))]
        async with websockets.connect(SmashLadderClient.socket_url, extra_headers=header) as client:
            self.on_connected()

            # Process current match and finish any pre-existing match.
            data = {"is_in_ladder": "1", "match_only_mode": "1"}
            response = self.post("matchmaking/get_user_going", data=data).json()
            self.process_message(response)

            while True:
                message = await client.recv()
                self.process_message(json.loads(str(message)))

    def send_private_message_to_user(self, user_id, message):
        data = {
            "chat_room_id": "",
            "to_user_id": user_id,
            "message": message,
        }
        self.post("matchmaking/send_chat", data=data)

    def challenge_search(self, match):
        data = {
            "challenge_player_id": match["player1"]["id"],
            "match_id": match["id"]
        }
        self.post("matchmaking/challenge_search", data=data)

    def create_search(self, game_count, title):
        data = {
            "team_size": 1,
            "game_id": 2, # Game ID 2 is Melee.
            "match_count": game_count, # Possible values are 5, 3, and 0 (infinite).
            "title": title,
            "ranked": 0
        }
        response = self.post("matchmaking/begin_matchmaking", data=data).json()
        if "searches" in response:
            searches = response["searches"]
            self.current_search = list(searches.values())[0]["id"]

    def cancel_search(self, search_id):
        data = {
            "match_id": search_id
        }
        self.post("matchmaking/end_matchmaking", data=data)

    def send_chat(self, match_id, message):
        data = {
            "chat_room_id": "",
            "match_id": match_id,
            "message": message,
        }
        self.post("matchmaking/send_chat", data=data)

    def select_stage(self, match_id, stage):
        data = {
            "match_id": match_id,
            "stage_id": stage
        }
        self.post("matchmaking/select_stage", data=data)

    def select_character(self, match_id, character):
        data = {
            "match_id": match_id,
            "character_id": character
        }
        self.post("matchmaking/select_character", data=data)

    def report_match(self, match_id, result):
        # Confusingly, reporting who won is not absolute (in contrast to every other match player reference).
        data = {
            "match_id": match_id,
            "won": result
        }
        self.post("matchmaking/report_match", data=data)

    def update_match_feedback(self, match_id, feedback_text, attitude, connection):
        data = {
            "match_id": match_id,
            "feedback": feedback_text,
            "salt_feedback": attitude, # -1, 0, 1
            "connection_feedback": connection, # -1, 0, 1
            "version": "2"
        }
        self.post("matchmaking/update_feedback", data=data)

    def finish_match(self, match_id):
        data = {
            "match_id": match_id
        }
        self.post("matchmaking/finished_chatting_with_match", data=data)

    def reply_to_challenge(self, challenge_id, accepted):
        data = {
            "match_id": challenge_id,
            "accept": ("1" if accepted else "0"),
            "host_code": ""
        }
        self.post("matchmaking/reply_to_match", data=data)
        if accepted:
            self.current_match = challenge_id
    
    def post(self, url, data=None):
        return requests.post(SmashLadderClient.base_url + url, data=data, cookies=self.cookies)

class TestSmashLadderClient(SmashLadderClient):
    def on_logged_in(self):
        print("Logged in.")

    def on_connected(self):
        # Cancel any already-existing searches.
        response = self.post("matchmaking/retrieve_match_searches").json()
        # Every response dictionary contains an "all_entries" key. We need to filter that out.
        for id in [key for key in response["searches"] if key != "all_entries"]:
            if str(response["searches"][id]["player1"]["id"]) == self.user_id:
                self.cancel_search(id)
        
        print("Connected.")

    def on_game_updated(self, match):
        # The "game" property stores actual game info.
        game = match["game"]

        # The following spaghetti finds the first player whose ID is not our own.
        other_character = game["players"][[key for key in game["players"] if key != self.user_id][0]]["character"]
        # 1 if host, 2 if challenger.
        player_index = str(list(game["players"].keys()).index(str(self.user_id)) + 1)

        if (game["current_action"] == Actions.player_1_strike_stage) or (game["current_action"] == Actions.player_2_strike_stage):
            # These are ordered from least-liked to most-liked.
            # Confusion may arise with select_stage; it is used for both striking and selecting.
            if str(Stages.battlefield) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.battlefield)
            elif str(Stages.dream_land) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.dream_land)
            elif str(Stages.final_destination) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.final_destination)
            elif str(Stages.fountain_of_dreams) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.fountain_of_dreams)
            elif str(Stages.pokemon_stadium) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.pokemon_stadium)
            elif str(Stages.yoshis_story) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.yoshis_story)

        elif (game["current_action"] == Actions.player_1_pick_character) or (game["current_action"] == Actions.player_2_pick_character):
            self.select_character(match["id"], Characters.captain_falcon)

        elif game["current_action"] == Actions.players_blind_pick_characters:
            self.select_character(match["id"], Characters.captain_falcon)

        elif game["current_action"] == Actions.players_play_game: # Playing game.
            # Check for external condition here.
            # An async await operation is not needed, as SmashLadder reminds the web socket to report the score approximately twice every second.

            # Make sure we haven't reported the match already (again, SmashLadder causes this to happen twice per second).
            if game["teams"][player_index]["match_report"] == None:
                self.report_match(match["id"], GameResult.lose)

        elif (game["current_action"] == Actions.player_1_pick_stage) or (game["current_action"] == Actions.player_2_pick_stage):
            # These are ordered from most-liked to least-liked.
            if str(Stages.battlefield) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.battlefield)
            elif str(Stages.dream_land) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.dream_land)
            elif str(Stages.final_destination) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.final_destination)
            elif str(Stages.fountain_of_dreams) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.fountain_of_dreams)
            elif str(Stages.pokemon_stadium) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.pokemon_stadium)
            elif str(Stages.yoshis_story) in game["visible_stages"]:
                self.select_stage(match["id"], Stages.yoshis_story)

    def on_game_ended(self, match):
        self.send_chat(match["id"], "Good games, probably.")
        self.update_match_feedback(match["id"], "", Feedback.neutral, Feedback.neutral)
        print("Match completed.")
    
    def on_match_chat_recieved(self, message, match_id):
        if message.upper() == "!PING":
            self.send_chat(match_id, "Pong!")
        elif message.upper().startswith("!ECHO"):
            self.send_chat(match_id, message[6:])

    def on_search_created(self, search):
        if self.current_match == None:
            # Plays Melee?
            if "2" in search["player1"]["preferred_builds"]:
                # TODO: Check location.
                correct_player = search["player1"]["id"] == 149091 # TODO Remove.
                is_melee = search["ladder_id"] == 2
                is_not_infinite = search["match_count"] != 0
                is_not_ranked = not search["is_ranked"]
                can_use_faster_melee = search["player1"]["preferred_builds"]["2"][0]["active"] == 1

                if correct_player and is_melee and is_not_infinite and is_not_ranked and can_use_faster_melee:
                    self.challenge_search(search)
                    print("Challenged search created by {0} ({1}).".format(search["player1"]["username"], search["player1"]["id"]))


# I made a file globals.py on my PYTHONPATH for things like this
from globals import smashladder, dolphin_iso_path

TestSmashLadderClient().log_in(smashladder['username'], smashladder['password'])
