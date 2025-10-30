import hmac
import hashlib
import urllib.parse
from typing import Dict, Any, List, Tuple

def parse_pairs(init_data: str) -> List[Tuple[str, str]]:
    return urllib.parse.parse_qsl(init_data, keep_blank_values=True)

def parse_init_data_for_app(init_data: str) -> Dict[str, Any]:
    d = dict(parse_pairs(init_data))
    try:
        import json
        if "user" in d:
            d["user"] = json.loads(d["user"])
    except Exception:
        pass
    return d

def data_check_string(init_data: str) -> str:
    pairs = [
        f"{k}={v}"
        for k, v in sorted(parse_pairs(init_data), key=lambda kv: kv[0])
        if k != "hash"
    ]
    return "\n".join(pairs)

def verify_init_data(init_data: str, bot_token: str) -> bool:
    m = dict(parse_pairs(init_data))
    received_hash = m.get("hash")
    if not received_hash:
        return False

    dcs = data_check_string(init_data)

    secret_key = hmac.new(key=b"WebAppData",
                          msg=bot_token.encode("utf-8"),
                          digestmod=hashlib.sha256).digest()

    expected = hmac.new(key=secret_key,
                        msg=dcs.encode("utf-8"),
                        digestmod=hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, received_hash)