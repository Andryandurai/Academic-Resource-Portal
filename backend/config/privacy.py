"""A minimal, real privacy policy for the WhatsApp bot.

Meta requires a reachable Privacy Policy URL before an app can be switched
from Development to Live mode. Served directly by Django (not the SPA) so it
renders without JavaScript for Meta's own fetcher, and so it exists whether or
not the frontend has been built at all.
"""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse

_HTML = """<!doctype html>
<meta charset="utf-8">
<title>Privacy Policy — REC Academic Resource Bot</title>
<body style="font:16px/1.6 system-ui;max-width:38rem;margin:6vh auto;padding:0 1.5rem;color:#1a1a1a">
<h1>Privacy Policy</h1>
<p><strong>REC Academic Resource Bot</strong> is a student project that lets
students retrieve academic notes, reference links and YouTube videos over
WhatsApp. It is not an official Rajalakshmi Engineering College service.</p>

<h2>What is collected</h2>
<ul>
  <li>Your WhatsApp phone number, so the bot can reply to you.</li>
  <li>Your chosen department and semester, so results match your curriculum.</li>
  <li>The text of messages you send the bot, only to interpret what you are
      asking for (e.g. a subject name, a unit number).</li>
</ul>

<h2>What is not done</h2>
<ul>
  <li>No advertising, tracking, or sale of data to any third party.</li>
  <li>No messages are sent to you unless you message the bot first.</li>
</ul>

<h2>Third parties involved</h2>
<ul>
  <li><strong>Meta / WhatsApp Cloud API</strong> — transports every message
      between you and the bot, under Meta's own privacy policy.</li>
  <li><strong>Groq</strong> (optional) — a free-tier LLM used only to help
      parse an ambiguous message into a subject name; no student identity is
      sent to it, only the message text.</li>
</ul>

<h2>Data retention</h2>
<p>Your phone number, chosen department/semester and current conversation
state are stored only to make the bot usable across messages. There is no
use of this data beyond operating the bot.</p>

<h2>Contact</h2>
<p>This is a student project; there is no formal support channel.</p>
</body>
"""


def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse(_HTML, content_type="text/html; charset=utf-8")
