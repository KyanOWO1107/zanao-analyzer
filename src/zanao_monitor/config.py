from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ZanaoMiniConfig:
    base_url: str
    school_alias: str
    user_token: str
    api_salt: str
    sc_version: str
    sc_platform: str
    sc_appid: str
    user_agent: str
    referer: str


REQUIRED_ZANAO_MINI_FIELDS: tuple[str, ...] = (
    "ZANAO_BASE_URL",
    "ZANAO_SCHOOL_ALIAS",
    "ZANAO_USER_TOKEN",
    "ZANAO_API_SALT",
    "ZANAO_SC_VERSION",
    "ZANAO_SC_PLATFORM",
    "ZANAO_SC_APPID",
    "ZANAO_USER_AGENT",
    "ZANAO_REFERER",
)


def read_env_file(env_path: str | Path) -> dict[str, str]:
    path = Path(env_path)
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_zanao_mini_config(env_path: str | Path = ".env") -> ZanaoMiniConfig:
    values = read_env_file(env_path)
    missing = [name for name in REQUIRED_ZANAO_MINI_FIELDS if not values.get(name)]
    if missing:
        raise ConfigError("Missing required Zanao mini config values: " + ", ".join(missing))

    return ZanaoMiniConfig(
        base_url=values["ZANAO_BASE_URL"].rstrip("/"),
        school_alias=values["ZANAO_SCHOOL_ALIAS"],
        user_token=values["ZANAO_USER_TOKEN"],
        api_salt=values["ZANAO_API_SALT"],
        sc_version=values["ZANAO_SC_VERSION"],
        sc_platform=values["ZANAO_SC_PLATFORM"],
        sc_appid=values["ZANAO_SC_APPID"],
        user_agent=values["ZANAO_USER_AGENT"],
        referer=values["ZANAO_REFERER"],
    )
