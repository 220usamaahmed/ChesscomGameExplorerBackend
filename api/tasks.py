from __future__ import absolute_import, unicode_literals

from celery import shared_task
from celery_progress.backend import ProgressRecorder

import urllib.request
import json
import datetime
import io
import chess.pgn


MAX_DEPTH = 8


def get_archive_links(username):
    link = f"https://api.chess.com/pub/player/{username}/games/archives"

    try:
        with urllib.request.urlopen(link) as url:
            data = json.loads(url.read().decode())
            return data["archives"]
    except urllib.error.HTTPError as exception:
        # TODO: Error logging
        print(exception)


def download_games(archive_links):
    try:
        for archive_link in archive_links:
            year, month = archive_link.split('/')[-2:]
            period = f"{datetime.datetime.strptime(month, '%m').strftime('%b')} {year}"
            with urllib.request.urlopen(archive_link) as url:
                data = json.loads(url.read().decode())
            yield period, data['games']
    except urllib.error.HTTPError as exception:
            # TODO: Error logging
            print(exception)


def update_game_tree(tree, game, result):
    current_node = tree
    
    for i, move in enumerate(game.mainline_moves()):
        if i > MAX_DEPTH: break
        move = str(move)
        if move in current_node['next_moves']:
            current_node['next_moves'][move]['w'] += 1 if result == +1 else 0
            current_node['next_moves'][move]['l'] += 1 if result == -1 else 0
            current_node['next_moves'][move]['d'] += 1 if result == 0 else 0
        else:
            current_node['next_moves'][move] = {
                'w': 1 if result == +1 else 0,
                'l': 1 if result == -1 else 0,
                'd': 1 if result == 0 else 0,
                'next_moves': {}
            }
        current_node = current_node['next_moves'][move]


@shared_task(bind=True)
def generate_game_trees(self, username):
    progress_recorder = ProgressRecorder(self)

    tree_white = {'next_moves': {}}
    tree_black = {'next_moves': {}}
    game_trees = { 'white': tree_white, 'black': tree_black }

    archive_links = get_archive_links(username)
    for i, (period, games_data) in enumerate(download_games(archive_links)):
        for game_data in games_data:
            game = chess.pgn.read_game(io.StringIO(game_data['pgn']))
            if game_data['white']['username'].lower() == username:
                if game_data['white']['result'] == 'win':
                    # I won as white
                    update_game_tree(tree_white, game, +1)
                elif game_data['black']['result'] == 'win':
                    # I lost as white
                    update_game_tree(tree_white, game, -1)
                else:
                    # I drew as white
                    update_game_tree(tree_white, game, 0)
            else:
                if game_data['black']['result'] == 'win':
                    # I won as black
                    update_game_tree(tree_black, game, +1)
                elif game_data['white']['result'] == 'win':
                    # I lost as black
                    update_game_tree(tree_black, game, -1)
                else:
                    # I drew as black
                    update_game_tree(tree_black, game, 0)

        progress_recorder.set_progress(i + 1, len(archive_links), description=f"Downloading games from {period}")
    
    return game_trees