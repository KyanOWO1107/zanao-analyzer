from zanao_monitor.state import NotificationState


def test_notification_state_tracks_sent_posts(tmp_path):
    db_path = tmp_path / "state.db"
    state = NotificationState(db_path)

    assert not state.was_sent("sample", "p1")

    state.mark_sent("sample", "p1", "exam_paper")

    assert state.was_sent("sample", "p1")


def test_notification_state_persists_between_instances(tmp_path):
    db_path = tmp_path / "state.db"
    first = NotificationState(db_path)
    first.mark_sent("sample", "p1", "exam_paper")

    second = NotificationState(db_path)

    assert second.was_sent("sample", "p1")

