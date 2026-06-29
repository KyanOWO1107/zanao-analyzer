from zanao_monitor.config import ZanaoMiniConfig
from zanao_monitor.zanao_client import ZanaoMiniClient, parse_thread_list_response


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self, payload: dict):
        self.payload = payload
        self.last_url = ""
        self.last_headers: dict[str, str] = {}
        self.last_data: dict[str, str] = {}

    def post(self, url: str, headers: dict[str, str], data: dict[str, str], timeout: int) -> FakeResponse:
        self.last_url = url
        self.last_headers = headers
        self.last_data = data
        return FakeResponse(self.payload)


def make_config() -> ZanaoMiniConfig:
    return ZanaoMiniConfig(
        base_url="https://api.x.zanao.com",
        school_alias="demo",
        user_token="token",
        api_salt="salt",
        sc_version="4.5.6",
        sc_platform="windows",
        sc_appid="wx-demo",
        user_agent="ua",
        referer="https://servicewechat.com/wx-demo/1/page-frame.html",
    )


def test_fetch_thread_list_posts_to_mini_program_endpoint():
    session = FakeSession({"errno": 0, "errmsg": "", "data": {"list": []}})
    client = ZanaoMiniClient(config=make_config(), session=session, nd_factory=lambda: "123", td_factory=lambda: 456)

    posts = client.fetch_thread_list(limit=10)

    assert posts == []
    assert session.last_url == "https://api.x.zanao.com/thread/v2/list"
    assert session.last_data == {
        "from_time": "0",
        "with_comment": "true",
        "with_reply": "true",
        "cate_id": "latest",
    }
    assert session.last_headers["X-Sc-Od"] == "token"
    assert session.last_headers["X-Sc-Alias"] == "demo"
    assert session.last_headers["X-Sc-Nd"] == "123"
    assert session.last_headers["X-Sc-Td"] == "456"
    assert session.last_headers["X-Sc-Ah"] == "979ae5ac5893e6a09aa9ce94c77b7e38"


def test_parse_thread_list_response_maps_items_to_posts():
    posts = parse_thread_list_response(
        {
            "errno": 0,
            "errmsg": "",
            "data": {
                "list": [
                    {
                        "thread_id": "p1",
                        "title": "求真题",
                        "content": "求高数真题",
                        "nickname": "alice",
                        "p_time": "1710000000",
                    }
                ]
            },
        },
        limit=5,
    )

    assert len(posts) == 1
    assert posts[0].source == "zanao-mini"
    assert posts[0].post_id == "p1"
    assert posts[0].title == "求真题"
    assert posts[0].content == "求高数真题"
    assert posts[0].author == "alice"
    assert posts[0].created_at == 1710000000


def test_parse_thread_list_response_raises_for_api_error():
    try:
        parse_thread_list_response({"errno": 401, "errmsg": "bad token"}, limit=5)
    except RuntimeError as error:
        assert "bad token" in str(error)
    else:
        raise AssertionError("expected RuntimeError")
