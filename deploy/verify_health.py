"""Wait for the source hash used by the existing /health endpoint."""

import json
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def verify(url: str, expected_hash: str, *, timeout: float = 90) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            request = Request(url, headers={"Cache-Control": "no-cache"})
            with urlopen(request, timeout=3) as response:
                payload = json.loads(response.read(4096))
            if (isinstance(payload, dict) and payload.get("status") == "ok"
                    and payload.get("hash") == expected_hash):
                return
        except (URLError, TimeoutError, OSError, ValueError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("Health check did not return the expected source hash.")
        time.sleep(2)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m deploy.verify_health URL SOURCE_HASH")
    try:
        verify(sys.argv[1], sys.argv[2])
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    print("Health status and source hash verified.")
