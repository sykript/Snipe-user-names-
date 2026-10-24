#!/usr/bin/env python3
"""Roblox username checker for Termux — terminal only, no browser or API key."""
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://auth.roblox.com/v1/usernames/validate"

def check_username(username):
    username = username.strip()
    if not (3 <= len(username) <= 20):
        return username, "INVALID", "Username must be 3–20 characters."
    if not all(c.isalnum() or c == "_" for c in username):
        return username, "INVALID", "Only letters, numbers, and underscores are accepted by this checker."

    params = urllib.parse.urlencode({
        "request.username": username,
        "request.birthday": "2000-01-01",
        "request.context": "Signup",
    })
    req = urllib.request.Request(
        API + "?" + params,
        headers={
            "User-Agent": "Mozilla/5.0 (Android; Termux) RobloxUsernameChecker/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8", "replace"))
        code = data.get("code")
        message = str(data.get("message", ""))
        if code == 0:
            return username, "POSSIBLY AVAILABLE", "Roblox validation returned code 0; not reserved."
        if code == 1:
            return username, "TAKEN", message or "Roblox says this username is already in use."
        if code in (2, 3, 4, 5, 6):
            return username, "INVALID / RESTRICTED", message or f"Roblox validation code {code}."
        return username, "UNKNOWN", f"Unexpected API response: {data}"
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return username, "RATE LIMITED", "Wait a while before trying again."
        return username, "UNKNOWN", f"HTTP {e.code}; Roblox may be blocking the request."
    except Exception as e:
        return username, "UNKNOWN", f"{type(e).__name__}: {e}"

def main():
    print("\n=== ROBLOX USERNAME SNIPER (TERMUX CLI) ===")
    print("Paste usernames one per line. Press Enter on an empty line to start checking.")
    print("No API key, browser, or Roblox login required.\n")
    names = []
    while True:
        try:
            line = input("name> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return
        if not line:
            break
        # Also allow several names pasted in one line separated by spaces or commas.
        names.extend(x.strip() for x in line.replace(",", " ").split() if x.strip())

    names = list(dict.fromkeys(names))
    if not names:
        print("No usernames entered.")
        return

    results = []
    for i, name in enumerate(names, 1):
        print(f"[{i}/{len(names)}] Checking {name} ...", end=" ", flush=True)
        result = check_username(name)
        results.append(result)
        print(f"{result[1]} — {result[2]}")
        if i < len(names):
            time.sleep(1.5)  # gentle delay to reduce rate-limit risk

    filename = "roblox_username_results.csv"
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "status", "details"])
            writer.writerows(results)
        print(f"\nSaved results to: {filename}")
    except OSError as e:
        print(f"\nCouldn't save CSV: {e}")

    print("\nNote: results are a snapshot, not a reservation. A 404 profile page does not prove availability or a ban.")

if __name__ == "__main__":
    main()
