#!/usr/bin/env python3
import asyncio
import hashlib
import math
import os
import random
import string

from lib.quiz_api import (
    default_team_name,
    normalize_team_id,
    parse_known_teams,
    register_team_online,
    resolve_team_id,
)

HOST = "0.0.0.0"  # TODO: ogni team deve configurare questo valore con l'IP pubblico del proprio server
PORT = int(os.environ.get("TEAM_SERVER_PORT", "5000"))

KNOWN_TEAMS = parse_known_teams(
    os.environ.get("KNOWN_TEAMS", "teamA,teamB,teamC,teamD,teamE,teamF")
)

RAW_TEAM_ID = os.environ.get("TEAM_ID", "1")
TEAM_ID = ""

TEAM_NAME = os.environ.get(
    "TEAM_NAME",
    default_team_name(normalize_team_id(RAW_TEAM_ID, KNOWN_TEAMS), KNOWN_TEAMS),
)
FLAG = os.environ.get("FLAG", "lab-secret")
VALIDATOR_URL = "http://130.136.3.32:8000"
SESSION_TIMEOUT_SECONDS = 300


def compute_team_flag(team_id: str, step: int) -> str:
    data = f"{team_id}:{step}:{FLAG}".encode()
    return hashlib.md5(data).hexdigest()


async def send_line(writer: asyncio.StreamWriter, line: str) -> None:
    writer.write((line + "\n").encode())
    await writer.drain()


async def read_line(reader: asyncio.StreamReader) -> str:
    data = await reader.readline()
    if not data:
        return ""
    return data.decode(errors="replace").rstrip("\r\n")


async def check(writer: asyncio.StreamWriter, ok: bool):
    if ok:
        await send_line(writer, "ok")
    else:
        await send_line(writer, "wrong")
        raise Exception("wrong answer")


MAXNUM = 2**16


async def step1(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    x = random.randint(0, MAXNUM)
    y = random.randint(0, MAXNUM)
    expected_ans = x * y

    await send_line(writer, f"{x} * {y} ?")

    ans = int((await read_line(reader)).strip())

    await check(writer, expected_ans == ans)


async def step2(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    x = random.randint(0, MAXNUM)
    await send_line(writer, f"guess the number? [ 0, {MAXNUM} ]")

    # loop di tentativi
    for _ in range(int(math.log(MAXNUM, 2) + 1)):
        guessed_x = int(((await read_line(reader)).strip()))

        if guessed_x < x:
            await send_line(writer, "higher")
        elif guessed_x > x:
            await send_line(writer, "lower")
        else:
            await check(writer, True)
            return

    await send_line(writer, "too many attempts")
    await check(writer, False)


async def step3(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # Genera un secret casuale di 8 byte
    secret = os.urandom(8)
    await send_line(
        writer, "XOR oracle: send 'enc <hex_msg>' or 'secret <hex_secret>' (8 bytes)"
    )

    while True:
        line = (await read_line(reader)).strip()
        if line.startswith("enc "):
            msg_hex = line[4:]
            try:
                msg = bytes.fromhex(msg_hex)

                # Previene l'exploit con zeri: rifiuta il messaggio se contiene byte nulli
                if b"\x00" in msg:
                    await send_line(writer, "no zeros allowed!")
                    continue

                # Esegue lo XOR tra il messaggio e il secret
                res = bytes([msg[i] ^ secret[i % len(secret)] for i in range(len(msg))])
                await send_line(writer, res.hex())
            except ValueError:
                await send_line(writer, "invalid hex")

        elif line.startswith("secret "):
            guess_hex = line[7:]
            if guess_hex == secret.hex():
                await check(writer, True)
                return
            else:
                await check(writer, False)
                return
        else:
            await send_line(writer, "unknown command")


def text_to_brainfuck(text):
    """
    Generates Brainfuck code that prints the given text.
    """
    code = []

    # We will use cell 0 as a temporary iterator for loops
    # and cell 1 as the current printing cell.
    # The pointer starts at cell 0.

    current_value = 0

    # Initialize pointer at cell 1 for the first character
    code.append(">")

    for char in text:
        target = ord(char)
        diff = target - current_value

        # If the difference is small (e.g., < 10), just do linear + or -
        # If it's large, use a loop to get close.
        if abs(diff) < 10:
            if diff > 0:
                code.append("+" * diff)
            elif diff < 0:
                code.append("-" * (-diff))
        else:
            # We need to add 'diff' to the current cell.
            # We find factors to create a loop: counter * step + remainder = diff

            # Simple heuristic: try to find a factor close to sqrt(diff)
            # We look for the best 'counter' size (roughly sqrt of diff)
            best_counter = 0
            best_step = 0
            best_remainder = diff

            # We iterate to find a combination that produces the shortest code
            # We search for a divisor between 2 and 20 (arbitrary optimization range)
            shortest_len = 1000  # arbitrary large number

            # Decide direction of loop (add or subtract)
            sign = 1 if diff > 0 else -1
            abs_diff = abs(diff)

            for counter in range(2, 20):
                step = abs_diff // counter
                remainder = abs_diff % counter

                # Approximate length of code generated by this combination
                # Code structure: < [->+<] > .
                # Length ~= counter + 5 (loop overhead) + step + remainder
                this_len = counter + step + remainder

                if this_len < shortest_len:
                    shortest_len = this_len
                    best_counter = counter
                    best_step = step * sign
                    best_remainder = remainder * sign

            # Generate the loop code
            # 1. Move to cell 0 (iterator)
            code.append("<")
            # 2. Set the counter
            code.append("+" * best_counter)
            # 3. Loop start
            code.append("[")
            # 4. Decrement counter
            code.append("-")
            # 5. Move to cell 1 (data)
            code.append(">")
            # 6. Add/Sub step
            if best_step > 0:
                code.append("+" * best_step)
            else:
                code.append("-" * (-best_step))
            # 7. Move back to cell 0
            code.append("<")
            # 8. Loop end
            code.append("]")
            # 9. Move back to cell 1
            code.append(">")

            # 10. Add/Sub remainder
            if best_remainder > 0:
                code.append("+" * best_remainder)
            elif best_remainder < 0:
                code.append("-" * (-best_remainder))

        code.append(".")
        current_value = target

    return "".join(code)


def randomword(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


async def step4(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    secret = randomword(8)
    bfsecret = text_to_brainfuck(secret)

    await send_line(writer, "Can you tell me what this brainfuck program outputs?")
    await send_line(writer, bfsecret)

    guessed = (await read_line(reader)).strip()

    await check(writer, secret == guessed)


async def send_flag(writer: asyncio.StreamWriter, team_id: str, step: int):
    flag = compute_team_flag(team_id, step)
    await send_line(writer, f"flag: {flag}")


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    async def timeout():
        await asyncio.sleep(SESSION_TIMEOUT_SECONDS)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    timeout_task = asyncio.create_task(timeout())
    try:
        await send_line(writer, f"Welcome to the quiz! Team: {TEAM_ID}")

        # Step 1
        await step1(reader, writer)
        await send_flag(writer, TEAM_ID, 1)

        # Step 2
        await step2(reader, writer)
        await send_flag(writer, TEAM_ID, 2)

        # Step 3
        await step3(reader, writer)
        await send_flag(writer, TEAM_ID, 3)

        # Step 4
        await step4(reader, writer)
        await send_flag(writer, TEAM_ID, 4)

        await send_line(writer, "Congratulations! You've completed the quiz.")
        return
    finally:
        timeout_task.cancel()
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    global TEAM_ID
    TEAM_ID = await resolve_team_id(VALIDATOR_URL, TEAM_NAME, RAW_TEAM_ID, KNOWN_TEAMS)

    await register_team_online(VALIDATOR_URL, TEAM_ID, "online")
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    print(f"[+] Team server {TEAM_NAME} (ID {TEAM_ID}) listening on {addrs}")

    try:
        async with server:
            await server.serve_forever()
    finally:
        server.close()
        await server.wait_closed()
        await register_team_online(VALIDATOR_URL, TEAM_ID, "offline")


if __name__ == "__main__":
    asyncio.run(main())
