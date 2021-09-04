import datetime
import os
import time

import flask
import humanize
import psutil
import qbittorrentapi
import requests

app = flask.Flask(__name__)
JELLYFIN = os.environ['JELLYFIN']
QBITTORRENT = os.environ['QBITTORRENT']


@app.route('/', methods=['GET'])
def get() -> flask.Response:
    status = _build_table("Status", _get_status())
    containers = _build_table("Containers", _get_containers())
    streams = _build_table("Streams", _get_streams())
    downloads = _build_table("Downloads", _get_downloads())
    content = status + containers + streams + downloads
    response = flask.jsonify({'content': content})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def _build_table(name, content):
    result = f'<div class="message-container"><h3>{name}</h3><table class="{name}">'
    for row in content:
        key, value = row
        result += f"<tr><td>{key}</td><td>{value}</td></tr>"
    result += "</table></div>"
    return result


def _get_containers():
    with open("stats_lock", "w") as stats_lock:
        stats_lock.write("1")
    results = []
    with open("stats") as stats:
        for line in stats.readlines():
            parts = line.split(" / ")[0].split(",")
            name = parts[0] if len(parts[0]) < 12 else parts[0][:9] + "..."
            values = f"{parts[1]}  {parts[2]}"
            results.append((name, values))
    return results


def _get_downloads():
    results = []
    user, password, host, port = QBITTORRENT.replace("@", ":").split(":")
    qbt_client = qbittorrentapi.Client(host=host, port=port, username=user, password=password)
    qbt_client.auth_log_in()
    for torrent in qbt_client.torrents_info():
        name = torrent["name"] if len(torrent["name"]) < 15 else torrent["name"][:12] + "..."
        total_size = humanize.naturalsize(torrent["total_size"], gnu=True)
        dlspeed = humanize.naturalsize(torrent["dlspeed"], gnu=True)
        progress = round(torrent["progress"]*100)
        seeders = f"{torrent['num_seeds']} ({torrent['num_complete']})"
        state = "▶️" if torrent['state'] == "downloading" else "⏹️"
        state = f"{state} | {progress}% | {dlspeed} | {total_size} | {seeders}"
        results = [(name, state)]
    return results


def _get_status():
    cpu = f"{psutil.cpu_percent()}%"
    ram = f"{psutil.virtual_memory().percent}%"
    root = f"{humanize.naturalsize(psutil.disk_usage('/').free, gnu=True)} free"
    data = f"{humanize.naturalsize(psutil.disk_usage('/data').free, gnu=True)} free"
    return [
        ("Uptime", _get_uptime()),
        ("CPU", cpu),
        ("RAM", ram),
        ("/root", root),
        ("/data", data),
    ]


def _get_streams():
    streams = requests.get(JELLYFIN).json()
    results = []
    for stream in streams:
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
