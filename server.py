#!/usr/bin/env python3
"""Movie Engine - Door Server (Render par chalega).

Kaam: app se job lena (film ka title/saal/Drive link), job id dena,
status batana. Asal video Kaggle engine banata hai (Step 4 me judega).
Sirf Python standard library - koi dependency nahi.
"""
import json
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

JOBS = {}  # job_id -> job dict (memory me; Render restart par saaf)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json_body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, json.dumps({"ok": True, "service": "movie-engine-door",
                                         "time": now(), "jobs": len(JOBS)}))
        elif path == "/":
            rows = "".join(
                f"<tr><td>{j['id']}</td><td>{j['title']} ({j['year']})</td>"
                f"<td>{j['status']}</td><td>{j['created']}</td></tr>"
                for j in JOBS.values()) or "<tr><td colspan=4>Abhi koi job nahi</td></tr>"
            html = f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Movie Engine Door</title></head><body style="font-family:sans-serif">
<h2>🎬 Movie Engine — Door Server LIVE</h2>
<p>Server chal raha hai. App yahi se judegi. Time: {now()}</p>
<table border=1 cellpadding=6 style="border-collapse:collapse">
<tr><th>Job ID</th><th>Film</th><th>Status</th><th>Time</th></tr>{rows}</table>
</body></html>"""
            self._send(200, html, "text/html; charset=utf-8")
        elif path == "/jobs":
            self._send(200, json.dumps(list(JOBS.values())))
        elif path.startswith("/jobs/"):
            job = JOBS.get(path.split("/")[2])
            if job:
                self._send(200, json.dumps(job))
            else:
                self._send(404, json.dumps({"ok": False, "error": "job not found"}))
        else:
            self._send(404, json.dumps({"ok": False, "error": "not found"}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/jobs":
            data = self._json_body()
            title = str(data.get("title") or "").strip()
            year = str(data.get("year") or "").strip()
            link = str(data.get("drive_link") or "").strip()
            if not title or not year:
                self._send(400, json.dumps({"ok": False,
                                            "error": "title aur year zaroori hai"}))
                return
            job_id = uuid.uuid4().hex[:8]
            JOBS[job_id] = {"id": job_id, "title": title, "year": year,
                            "drive_link": link, "status": "received",
                            "created": now(), "video_url": ""}
            self._send(200, json.dumps({"ok": True, "job_id": job_id,
                                        "status": "received"}))
        else:
            self._send(404, json.dumps({"ok": False, "error": "not found"}))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
