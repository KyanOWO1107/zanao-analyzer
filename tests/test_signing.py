import hashlib

from zanao_monitor.signing import make_x_sc_ah


def test_make_x_sc_ah_uses_alias_nd_td_and_salt():
    sign = make_x_sc_ah(
        school_alias="demo_school",
        nd="12345678901234567890",
        td="1700000000",
        api_salt="demo_salt_for_test",
    )

    expected = hashlib.md5("demo_school_12345678901234567890_1700000000_demo_salt_for_test".encode()).hexdigest()
    assert sign == expected
