import datetime
import os
import time

import flask
import humanize
import psutil
import qbittorrentapi
import requests

app = flask.Flask(__name__)
DISKS = os.environ.get("DISKS", "/root")
JELLYFIN = os.environ.get("JELLYFIN")
QBITTORRENT = os.environ.get("QBITTORRENT")


@app.route("/", methods=["GET"])
def get() -> flask.Response:
    status = _build_table("Status", _get_status())
    containers = _build_table("Containers", _get_containers())
    streams = _build_table("Streams", _get_streams())
    downloads = _build_table("Downloads", _get_downloads())
    content = status + containers + streams + downloads
    response = flask.jsonify({"content": content})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def _build_table(name, content):
    if not content:
        return ""
    result = f'<div class="message-container"><h3>{name}</h3><table class="{name}">'
    for row in content:
        key, value = row
        result += f"<tr><td>{key}</td><td>{value}</td></tr>"
    result += "</table></div>"
    return result


def _get_containers():
    with open("stats_lock", "w") as stats_lock:
        stats_lock.write("1")
    if not os.path.isfile("stats"):
        return []
    
    results = []
    with open("stats") as stats:
        for line in stats.readlines():
            parts = line.split(" / ")[0].split(",")
            name = parts[0] if len(parts[0]) < 12 else parts[0][:9] + "..."
            values = f"{parts[1]}  {parts[2]}"
            results.append((name, values))
    return results


def _get_downloads():
    if QBITTORRENT is None:
        return []
    results = []
    user, password, host, port = QBITTORRENT.replace("@", ":").split(":")
    qbt_client = qbittorrentapi.Client(host=host, port=port, username=user, password=password)
    qbt_client.auth_log_in()
    for torrent in qbt_client.torrents_info()[:5]:
        name = torrent["name"] if len(torrent["name"]) < 15 else torrent["name"][:12] + "..."
        total_size = humanize.naturalsize(torrent["total_size"], gnu=True)
        dlspeed = humanize.naturalsize(torrent["dlspeed"], gnu=True)
        progress = round(torrent["progress"]*100)
        seeders = f"{torrent['num_seeds']} ({torrent['num_complete']})"
        state = "▶️" if torrent["state"] == "downloading" else "⏹️"
        state = f"{state} | {progress}% | {dlspeed} | {total_size} | {seeders}"
        results = [(name, state)]
    return results


def _get_status():
    cpu = f"{psutil.cpu_percent()}%"
    ram = f"{psutil.virtual_memory().percent}%"
    disks = [(disk, f"{humanize.naturalsize(psutil.disk_usage(disk).free, gnu=True)} free") for disk in DISKS.split(",")]
    return [
        ("Uptime", _get_uptime()),
        ("CPU", cpu),
        ("RAM", ram),
    ] + disks


def _get_streams():
    if JELLYFIN is None:
        return []
    streams = requests.get(JELLYFIN).json()
    results = []
    for stream in streams[:5]:
        if not "NowPlayingItem" in stream:
            continue
        user = stream["UserName"]
        name = stream["NowPlayingItem"]["Name"]
        name = name if len(name) < 20 else name[:17] + "..."
        transcoding = "🔥" if stream["PlayState"]["PlayMethod"] == "Transcode" else "➡️"
        playing = "⏹️" if stream["PlayState"]["IsPaused"] else "▶️"
        media = f"{playing} {transcoding} {user}"
        results.append((name, media))
    return results


def _get_uptime():
    uptime = ""
    uptime_td = datetime.timedelta(seconds=round(time.time() - psutil.boot_time()))
    weeks, days = divmod(uptime_td.days, 7)
    if weeks:
        uptime += f"{weeks}w"
    if days:
        uptime += f"{days}d"
    hours, remainder = divmod(uptime_td.seconds, 3600)
    if hours:
        uptime += f"{hours}h"
    minutes, _ = divmod(remainder, 60)
    if minutes:
        uptime += f"{minutes}m"
    return uptime
