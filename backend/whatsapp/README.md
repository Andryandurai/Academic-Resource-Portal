# WhatsApp bot

Students never see the website. They message one WhatsApp number and the bot
sends back unit notes (a PDF), reference links, or YouTube videos, pulled from
the same `Subject`/`Resource` tables the admin portal writes to. Zero cost:
every piece is free, described below.

## How it stays free

**Meta WhatsApp Cloud API**: since November 2024, replying to a message a
user sent you first ("service conversation") is free and unlimited. This bot
never messages a student first — it only replies — so it never falls into a
billed category (a "template"/marketing message). Meta could change this in
the future; nothing else here depends on it.

**Groq (the LLM)**: used only to clean up a messy subject phrase like "umm
data structuresss pls" into "data structures". Optional — leave
`GROQ_API_KEY` blank and the bot uses a regex-based extractor instead, which
already handles the exact form the spec calls out ("unit 1 data structures
notes") with no network call. Groq's free tier is generous and needs no card.

**Hosting**: your choice, but Render/Railway/Fly free tiers *sleep* an idle
service — a webhook arriving while it's asleep is missed or timed out.
**Oracle Cloud's Always Free tier** gives a small VM that never sleeps and
never expires, at $0. That's what "always on" free hosting means here.

## 1. Try it with zero signup (dry run)

`WHATSAPP_DRY_RUN` defaults to on whenever `DEBUG=1` (the normal `runserver`
setup) and no real credentials are set. In that mode nothing is sent to Meta —
every "send" is logged and kept in memory, readable back over HTTP. This lets
you build and demo the entire conversation before creating any Meta account.

```bash
cd backend
python manage.py runserver

# Simulate an incoming WhatsApp message:
curl -X POST http://127.0.0.1:8000/api/whatsapp/dev/simulate/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "919876543210", "text": "hi"}'

# Answer the department/semester prompts the same way:
curl -X POST http://127.0.0.1:8000/api/whatsapp/dev/simulate/ \
  -d '{"phone": "919876543210", "text": "AI&DS"}' -H "Content-Type: application/json"
curl -X POST http://127.0.0.1:8000/api/whatsapp/dev/simulate/ \
  -d '{"phone": "919876543210", "text": "2"}' -H "Content-Type: application/json"

# Then ask for something:
curl -X POST http://127.0.0.1:8000/api/whatsapp/dev/simulate/ \
  -d '{"phone": "919876543210", "text": "unit 1 data structures notes"}' \
  -H "Content-Type: application/json"

# See everything the bot has "sent" so far:
curl http://127.0.0.1:8000/api/whatsapp/dev/outbox/
```

Both `dev/` endpoints return `404` whenever `WHATSAPP_DRY_RUN=0`, so they can
never be reachable on a real deployment by accident.

## 2. Get free Meta WhatsApp Cloud API credentials

1. Create a free account at <https://developers.facebook.com/> (a personal
   Facebook account is enough to start).
2. **My Apps → Create App → type "Business"** → give it any name.
3. On the app dashboard, add the **WhatsApp** product.
4. Meta gives you, for free, immediately:
   - A **test phone number** (Meta's own, not yours) and a **Phone number
     ID**.
   - A **temporary access token** (valid ~24 hours — fine for testing; see
     step 5 for a token that doesn't expire).
   - The ability to message up to **5 verified recipient numbers** with no
     business verification at all — add your own phone under "To" on the
     dashboard's test page and verify it with the SMS code Meta sends.
5. For a token that doesn't expire and a number every student can reach,
   Meta's dashboard walks you through **Business verification** (still free,
   takes a few days) and letting you either keep the free test number's
   permanent form or register your own phone number for WhatsApp Business.
   Until then, the 5-recipient test setup is enough to build and demo the
   whole thing.
6. Copy three values into `backend/.env`:
   ```
   WHATSAPP_ACCESS_TOKEN="<the token from the dashboard>"
   WHATSAPP_PHONE_NUMBER_ID="<the Phone number ID>"
   WHATSAPP_DRY_RUN="0"
   ```

## 3. Expose your webhook and register it

Meta needs to reach your server over HTTPS. **Cloudflare Tunnel** is free, and
needs no account for a quick one-off tunnel:

```bash
# Windows/macOS/Linux, free, no signup for a temporary tunnel:
cloudflared tunnel --url http://localhost:8000
```

This prints a `https://<random>.trycloudflare.com` URL. (For a stable
long-term URL, `cloudflared tunnel login` + a named tunnel — still free, and
what you'd want on the Oracle VM where you'd otherwise use its public IP with
a real domain and Let's Encrypt.)

1. Pick any random string for `WHATSAPP_VERIFY_TOKEN` and put it in
   `backend/.env`.
2. In the Meta dashboard: **WhatsApp → Configuration → Webhook → Edit**.
   - Callback URL: `https://<your-tunnel>/api/whatsapp/webhook/`
   - Verify token: the same string as `WHATSAPP_VERIFY_TOKEN`.
   - Click **Verify and save** — Django answers Meta's challenge
     automatically (`whatsapp/views.py:webhook_verify`).
3. Click **Manage** next to the webhook and subscribe to the **messages**
   field. Without this, Meta never calls your webhook at all.
4. Optional but recommended once you're off dry-run: copy the app's **App
   secret** (App settings → Basic) into `WHATSAPP_APP_SECRET` in `.env`. This
   makes the webhook verify Meta's signature on every request, so nobody who
   guesses your webhook URL can inject fake messages.

Restart `runserver` after editing `.env` (it's loaded once at process start).

## 4. Optional: a free-tier LLM for messier phrasing

Only needed for sentences the regex extractor can't cleanly parse. Get a free
key at <https://console.groq.com/keys> (no card required) and set:

```
GROQ_API_KEY="gsk_..."
```

If unset, or if a request fails or is rate-limited, the bot silently falls
back to the regex extractor — it never goes down over this.

## 5. Publishing content

Nothing changes for administrators except one new field. In **Upload
Resource** on the website, a **Content kind** selector now offers:

- **Notes** — a file upload, exactly as before.
- **Reference link** — a URL (any web page).
- **YouTube video** — a URL, checked against the actual `youtube.com` /
  `youtu.be` hosts.

Whatever category (Unit 1–5, CAT 1/2, Semester Exam) and kind an admin
publishes is immediately what the bot can answer with — there is nothing else
to sync.

## 6. Testing for real

Message your Meta test number from one of the 5 verified recipient phones.
The bot walks through department → semester once, then answers anything, e.g.:

- `"data structures"` → asks which unit/category, then which kind.
- `"unit 1 data structures notes"` → sends the PDF directly.
- `"cat 2 reference links dbms"` → sends the reference links directly.
- `"menu"` → shows your current department/semester and a reminder.
- `"change department"` → resets and asks again.

## Limits worth knowing

- A student must message first; the bot can never open a conversation (by
  design — that's also what keeps every reply free).
- WhatsApp interactive lists cap at 10 rows total and buttons at 3 — already
  respected (`meta_client.MAX_LIST_ROWS`/`MAX_BUTTONS`); a semester with more
  than 5 "did you mean" subject matches is truncated to the closest 5.
- Uploaded notes still go through the same `REC_MAX_UPLOAD_MB` size limit and
  file-signature validation as the website — nothing new to configure.
