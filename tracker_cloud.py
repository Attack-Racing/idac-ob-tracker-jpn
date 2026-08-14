import requests
import time
import json
import os
import subprocess
from datetime import datetime, timedelta

# ============================================================
# SETTINGS
# ============================================================

RANKING_URL = (
    "https://initiald.sega.jp/inidac/json/ranking/v1/"
    "roundPoint/rp_round-76_area-all.json"
)

ACTIVE_MINUTES = 30
REFRESH_SECONDS = 60

WEBSITE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_FILE = os.path.join(
    WEBSITE_DIR,
    "data.json"
)

GITHUB_DIR = WEBSITE_DIR

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cache-Control": "no-cache"
}

# ============================================================
# ONLINE BATTLE RANK IDs
# ============================================================

ONLINE_RANKS = {
    "dcb98f86f149cf71d3707a1592072e781508dd5785ba6ef82abb079722176702": "Clear Green",

    "dcb98f86f149cf71d3707a1592072e7838f0811140c24238820dff2b82602a85": "Ruby",

    "dcb98f86f149cf71d3707a1592072e786401fd58eb36b5000ac46b76b01cbba6": "Clear Red",

    "dcb98f86f149cf71d3707a1592072e78b49ea4af21de42fa72062961ba565479": "Clear Blue",

    "dcb98f86f149cf71d3707a1592072e78b6e12126e2a1e4802ed8674342c946c2": "Emerald",

    "dcb98f86f149cf71d3707a1592072e78f41e679a54f693d3574f499da9559173": "Sapphire",
}

# ============================================================
# RANK ORDER
# ============================================================

RANK_ORDER = {
    "Pride": 7,
    "Ruby": 6,
    "Sapphire": 5,
    "Emerald": 4,
    "Clear Blue": 3,
    "Clear Red": 2,
    "Clear Green": 1,
    "Unknown Online Rank": 0,
}

RANKS = [
    "Pride",
    "Ruby",
    "Sapphire",
    "Emerald",
    "Clear Blue",
    "Clear Red",
    "Clear Green",
    "Unknown Online Rank",
]

# ============================================================
# DOWNLOAD RANKING
# ============================================================

def download_ranking():

    print("Downloading Initial D ranking...")

    response = requests.get(
        RANKING_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if "records" not in data:

        raise Exception(
            "Could not find 'records' in JSON"
        )

    return data["records"]

# ============================================================
# GET PLAYER RANK
# ============================================================

def get_rank(player):

    # Pride players have a prideId
    if player.get("prideId"):

        return "Pride"

    rank_id = player.get(
        "onlineBattleRankId",
        ""
    )

    return ONLINE_RANKS.get(
        rank_id,
        "Unknown Online Rank"
    )

# ============================================================
# GET ACTIVITY STATUS
# ============================================================

def get_activity_status(update_time, now):

    age_seconds = (
        now - update_time
    ).total_seconds()

    age_minutes = age_seconds / 60

    if age_minutes < 15:

        return "green"

    elif age_minutes <= 30:

        return "yellow"

    else:

        return None

# ============================================================
# BUILD ACTIVE PLAYER DATA
# ============================================================

def get_active_players(records):

    now = datetime.now()

    rank_players = {

        rank: []

        for rank in RANKS

    }

    for player in records:

        update_string = player.get(
            "updateDate"
        )

        if not update_string:

            continue

        try:

            update_time = datetime.strptime(
                update_string,
                "%Y/%m/%d %H:%M:%S"
            )

        except ValueError:

            continue

        status = get_activity_status(
            update_time,
            now
        )

        # Older than 30 minutes
        # completely remove from website
        if status is None:

            continue

        rank = get_rank(player)

        try:

            point = int(
                player.get(
                    "point",
                    0
                )
            )

        except:

            point = 0

        player_data = {

            "name": player.get(
                "name",
                "UNKNOWN"
            ),

            "rank": rank,

            "point": point,

            "car": player.get(
                "carname",
                "?"
            ),

            "shop": player.get(
                "shopname",
                "?"
            ),

            "update": update_string,

            "status": status,

            "ageSeconds": int(
                (
                    now - update_time
                ).total_seconds()
            )

        }

        rank_players[rank].append(
            player_data
        )

    # ========================================================
    # SORT
    # ========================================================

    for rank in rank_players:

        rank_players[rank].sort(

            key=lambda player:
            player["point"],

            reverse=True

        )

    return rank_players

# ============================================================
# WRITE WEBSITE DATA
# ============================================================

def write_website_data(rank_players):

    now = datetime.now()

    total = sum(
        len(players)
        for players in rank_players.values()
    )

    data = {

        "trackerTime":
            now.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "activeSince":
            (
                now -
                timedelta(
                    minutes=ACTIVE_MINUTES
                )
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "total": total,

        "ranks": rank_players

    }

    os.makedirs(
        WEBSITE_DIR,
        exist_ok=True
    )

    temp_file = DATA_FILE + ".tmp"

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        temp_file,
        DATA_FILE
    )

def update_github():
    try:
        github_data = os.path.join(
            GITHUB_DIR,
            "data.json"
        )

        subprocess.run(
            ["cp", DATA_FILE, github_data],
            check=True
        )

        subprocess.run(
            ["git", "add", "data.json"],
            cwd=GITHUB_DIR,
            check=True
        )

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=GITHUB_DIR,
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            return

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "Update active player data"
            ],
            cwd=GITHUB_DIR,
            check=True
        )

        subprocess.run(
            ["git", "push"],
            cwd=GITHUB_DIR,
            check=True
        )

        print("GitHub updated successfully.")

    except Exception as e:
        print("GitHub update failed:", e)

# ============================================================
# PRINT TERMINAL
# ============================================================

def print_terminal(rank_players):

    now = datetime.now()

    print()
    print("=" * 78)

    print(
        "INITIAL D THE ARCADE - "
        "LIVE ACTIVE PLAYER TRACKER"
    )

    print("=" * 78)

    print(
        "Tracker time:",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        "Showing players active within "
        "the last 30 minutes"
    )

    print()

    for rank in RANKS:

        players = rank_players[rank]

        print("-" * 78)

        print(
            f"### {rank} ({len(players)})"
        )

        print("-" * 78)

        if not players:

            print(
                "  No players"
            )

            continue

        for number, player in enumerate(
            players,
            start=1
        ):

            if player["status"] == "green":

                icon = "🟢"

            else:

                icon = "🟡"

            age_seconds = player[
                "ageSeconds"
            ]

            minutes = age_seconds // 60

            seconds = age_seconds % 60

            print(
                f"{number:3}. "
                f"{icon} "
                f"{player['name']} | "
                f"{player['point']:,} RP | "
                f"{player['car']} | "
                f"{player['shop']} | "
                f"{minutes}m {seconds}s ago"
            )

    print()

    print("=" * 78)

    print(
        "TOTAL SHOWN:",
        sum(
            len(players)
            for players
            in rank_players.values()
        )
    )

    print("=" * 78)

# ============================================================
# MAIN LOOP
# ============================================================

print()
print("=" * 78)
print(
    "INITIAL D THE ARCADE - "
    "LIVE ACTIVE PLAYER TRACKER"
)
print("=" * 78)
print(
    "🟢 <15 min = RECENTLY ACTIVE"
)
print(
    "🟡 15–30 min = POSSIBLY ACTIVE"
)
print(
    "Players older than 30 min are removed."
)
print("=" * 78)

try:

    records = download_ranking()

    rank_players = get_active_players(
        records
    )

    write_website_data(
        rank_players
    )

    print_terminal(
        rank_players
    )

    print()

    update_github()

except Exception as e:

    print(
        "Tracker failed:",
        e
    )
