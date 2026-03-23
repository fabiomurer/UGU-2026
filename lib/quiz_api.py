import asyncio
import json
import urllib.error
import urllib.request
from urllib import parse, request


def _get_json(url: str) -> dict:
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def _post_json(url: str, payload: dict) -> dict:
    req = request.Request(
        url,
        method="POST",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def get_question(base_url: str, team: str, step: int) -> str:
    query = parse.urlencode({"team": team, "step": step})
    url = f"{base_url.rstrip('/')}/api/quiz/question?{query}"
    data = _get_json(url)
    return data["question"]


def get_team_id(base_url: str, team_name: str) -> str:
    query = parse.urlencode({"name": team_name})
    url = f"{base_url.rstrip('/')}/api/team/id?{query}"
    data = _get_json(url)
    return str(data["id"])


def get_team_name(base_url: str, team_id: str) -> str:
    query = parse.urlencode({"id": team_id})
    url = f"{base_url.rstrip('/')}/api/team/name?{query}"
    data = _get_json(url)
    return str(data["name"])


def parse_known_teams(known_teams_raw: str) -> list[str]:
    return [t.strip() for t in known_teams_raw.split(",") if t.strip()]


def normalize_team_id(raw_team_id: str, known_teams: list[str]) -> str:
    value = str(raw_team_id).strip()
    if value.isdigit():
        return value

    for index, team_name in enumerate(known_teams, start=1):
        if value.lower() == team_name.lower():
            return str(index)

    raise ValueError(
        f"Invalid TEAM_ID '{raw_team_id}'. Use numeric id (e.g. 1) or one of: {', '.join(known_teams)}"
    )


def default_team_name(team_id: str, known_teams: list[str]) -> str:
    if team_id.isdigit() and 1 <= int(team_id) <= len(known_teams):
        return known_teams[int(team_id) - 1]
    return f"team{team_id}"


async def resolve_team_id(
    validator_url: str,
    team_name: str,
    raw_team_id: str,
    known_teams: list[str],
) -> str:
    normalized_team_name = team_name.strip()
    if normalized_team_name:
        if validator_url:
            try:
                return await asyncio.to_thread(
                    get_team_id, validator_url, normalized_team_name
                )
            except Exception as err:
                print(
                    f"[!] Could not resolve TEAM_ID from validator for '{normalized_team_name}': {err}"
                )

        return normalize_team_id(normalized_team_name, known_teams)

    return normalize_team_id(raw_team_id, known_teams)


def is_correct_answer(base_url: str, team: str, step: int, answer: str) -> bool:
    url = f"{base_url.rstrip('/')}/api/quiz/validate"
    data = _post_json(url, {"team": team, "step": step, "answer": answer})
    return bool(data.get("ok"))


async def register_team_online(VALIDATOR_URL: str, TEAM_ID: str, status: str) -> None:
    if not VALIDATOR_URL:
        return

    endpoint = f"{VALIDATOR_URL.rstrip('/')}/api/team/online"
    payload = json.dumps({"team": TEAM_ID, "status": status}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _send() -> None:
        with urllib.request.urlopen(req, timeout=4):
            pass

    try:
        await asyncio.to_thread(_send)
        print(f"[+] Registered online on validator: {endpoint}")
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        print(f"[!] Could not register online on validator: {err}")


