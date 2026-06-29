import random
import time
from collections.abc import Callable
from typing import Protocol

import requests

from zanao_monitor.config import ZanaoMiniConfig
from zanao_monitor.models import Post
from zanao_monitor.signing import make_x_sc_ah


class ResponseLike(Protocol):
    def raise_for_status(self) -> None:
        ...

    def json(self) -> dict:
        ...


class SessionLike(Protocol):
    def post(self, url: str, headers: dict[str, str], data: dict[str, str], timeout: int) -> ResponseLike:
        ...


def generate_nd(length: int = 20) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def parse_thread_list_response(payload: dict, limit: int) -> list[Post]:
    errno = payload.get("errno")
    if errno != 0:
        errmsg = str(payload.get("errmsg", "unknown error"))
        raise RuntimeError(f"Zanao API returned errno={errno}: {errmsg}")

    data = payload.get("data", {})
    if not isinstance(data, dict):
        raise RuntimeError("Zanao API response missing data object")
    raw_items = data.get("list", [])
    if not isinstance(raw_items, list):
        raise RuntimeError("Zanao API response data.list is not a list")

    posts: list[Post] = []
    for item in raw_items[:limit]:
        if not isinstance(item, dict):
            continue
        posts.append(
            Post(
                source="zanao-mini",
                post_id=str(item.get("thread_id", "")),
                title=str(item.get("title") or ""),
                content=str(item.get("content") or ""),
                author=str(item.get("nickname") or ""),
                created_at=int(item.get("p_time") or 0),
            )
        )
    return posts


class ZanaoMiniClient:
    def __init__(
        self,
        config: ZanaoMiniConfig,
        session: SessionLike | None = None,
        nd_factory: Callable[[], str] = generate_nd,
        td_factory: Callable[[], int] | None = None,
        timeout_seconds: int = 15,
    ):
        self.config = config
        self.session = requests.Session() if session is None else session
        self.nd_factory = nd_factory
        self.td_factory = td_factory or (lambda: int(time.time()))
        self.timeout_seconds = timeout_seconds

    def _headers(self, nd: str, td: int) -> dict[str, str]:
        return {
            "X-Sc-Od": self.config.user_token,
            "X-Sc-Td": str(td),
            "X-Sc-Alias": self.config.school_alias,
            "X-Sc-Wf": "",
            "X-Sc-Nd": nd,
            "xweb_xhr": "1",
            "X-Sc-Appid": self.config.sc_appid,
            "X-Sc-Platform": self.config.sc_platform,
            "X-Sc-Cloud": "0",
            "X-Sc-Nwt": "wifi",
            "X-Sc-Version": self.config.sc_version,
            "User-Agent": self.config.user_agent,
            "X-Sc-Ah": make_x_sc_ah(self.config.school_alias, nd, str(td), self.config.api_salt),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": self.config.referer,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def fetch_thread_list(self, limit: int, from_time: int = 0) -> list[Post]:
        nd = self.nd_factory()
        td = self.td_factory()
        response = self.session.post(
            f"{self.config.base_url}/thread/v2/list",
            headers=self._headers(nd, td),
            data={
                "from_time": str(from_time),
                "with_comment": "true",
                "with_reply": "true",
                "cate_id": "latest",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return parse_thread_list_response(response.json(), limit=limit)
