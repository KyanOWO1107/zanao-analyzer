import hashlib


def make_x_sc_ah(school_alias: str, nd: str, td: str, api_salt: str) -> str:
    sign_text = f"{school_alias}_{nd}_{td}_{api_salt}"
    return hashlib.md5(sign_text.encode("utf-8")).hexdigest()

