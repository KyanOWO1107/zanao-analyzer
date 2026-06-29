import pytest

from zanao_monitor.config import ConfigError, ZanaoMiniConfig, load_zanao_mini_config


def test_load_zanao_mini_config_reads_required_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            (
                "ZANAO_BASE_URL=https://api.x.zanao.com",
                "ZANAO_SCHOOL_ALIAS=demo",
                "ZANAO_USER_TOKEN=token",
                "ZANAO_API_SALT=salt",
                "ZANAO_SC_VERSION=4.5.6",
                "ZANAO_SC_PLATFORM=windows",
                "ZANAO_SC_APPID=wx-demo",
                "ZANAO_USER_AGENT=ua",
                "ZANAO_REFERER=https://servicewechat.com/wx-demo/1/page-frame.html",
            )
        ),
        encoding="utf-8",
    )

    config = load_zanao_mini_config(env_path)

    assert config == ZanaoMiniConfig(
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


def test_load_zanao_mini_config_reports_missing_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("ZANAO_BASE_URL=https://api.x.zanao.com\n", encoding="utf-8")

    with pytest.raises(ConfigError) as error:
        load_zanao_mini_config(env_path)

    assert "ZANAO_USER_TOKEN" in str(error.value)
    assert "ZANAO_API_SALT" in str(error.value)

