# Lesson 18 – URL Opening

LunaEngine provides small, safe helpers for opening a user-facing link and fetching HTTP data. Both live in `lunaengine.utils.url`.

## Opening a link
```python
from lunaengine.utils.url import open_url

if not open_url("https://example.com/leaderboard"):
    print("The platform could not open the browser")
```

`open_url()` returns `True` when the platform browser accepts the request and `False` otherwise. It accepts `http://`, `https://`, and `mailto:` links. It rejects `file://`, `javascript:`, empty values, and malformed HTTP(S) URLs.

## Fetching data
```python
from lunaengine.utils.url import fetch_url

players = fetch_url("https://example.com/leaderboard.json", parse="json")
if isinstance(players, dict):
    print(players.get("top_player"))
```

`fetch_url(url, timeout=5.0, parse="auto")` is a **blocking** call and returns bytes, text, decoded JSON, or `None`. `parse` can be `"bytes"`, `"text"`, `"json"`, or `"auto"`. Auto mode uses the response content type: JSON content types are decoded as JSON, text content types as text, and other content as bytes. A failed JSON parse returns `None`, not the original text. Network errors, invalid URLs, timeouts, and non-2xx responses also return `None`.

A real game can put leaderboard fetching behind an explicit opt-in flag so offline builds do not make a request:
```python
if ENABLE_ONLINE_LEADERBOARD:
    leaderboard = fetch_url(LEADERBOARD_URL, parse="json")
else:
    leaderboard = None
```

Do not build URLs from untrusted input without validation. `open_url()` rejects `file://` and `javascript:` schemes, while `fetch_url()` permits only HTTP and HTTPS. Since fetching blocks the game loop, use a worker or background task for anything slower than a tiny request.
