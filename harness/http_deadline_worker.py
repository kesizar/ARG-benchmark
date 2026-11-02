"""One isolated HTTP request. Request data is read from stdin, never argv."""
import base64
import json
import sys

import httpx


def main() -> None:
    request = json.load(sys.stdin)
    try:
        seconds = request['timeout']
        timeout = httpx.Timeout(seconds, connect=min(20, seconds))
        with httpx.Client(timeout=timeout, trust_env=request['trust_env']) as client:
            response = client.post(request['url'], **request['kwargs'])
        # httpx has already decoded response.content; avoid decoding it twice.
        headers = {key: value for key, value in response.headers.items()
                   if key.lower() not in {'content-encoding', 'content-length', 'transfer-encoding'}}
        result = {'status': response.status_code, 'headers': headers,
                  'body': base64.b64encode(response.content).decode('ascii')}
    except httpx.TransportError as exc:
        # Provider errors and request headers may contain credentials: send only type.
        result = {'transport_error': type(exc).__name__}
    json.dump(result, sys.stdout)


if __name__ == '__main__':
    main()
