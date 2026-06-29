from zanao_monitor.models import DemandMatch, Post
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


def test_notification_state_records_scan_runs_and_matches(tmp_path):
    db_path = tmp_path / "state.db"
    state = NotificationState(db_path)
    post = Post(
        source="zanao-mini",
        post_id="p1",
        title="求题库",
        content="求这门课题库答案",
        author="alice",
        created_at=1710000000,
    )
    match = DemandMatch(
        post=post,
        category="course_resource",
        intent="request",
        keywords=("题库", "答案"),
        score=1.0,
    )

    run_id = state.record_scan_run(
        scanned_count=10,
        matched_count=1,
        sent_count=0,
        skipped_duplicate_count=0,
        dry_run=True,
        source="zanao-mini",
    )
    state.record_scan_match(run_id=run_id, match=match, status="preview")

    runs = state.list_recent_scan_runs(limit=5)
    matches = state.list_recent_scan_matches(limit=5)

    assert runs[0].run_id == run_id
    assert runs[0].scanned_count == 10
    assert runs[0].dry_run is True
    assert matches[0].run_id == run_id
    assert matches[0].post_id == "p1"
    assert matches[0].title == "求题库"
    assert matches[0].category == "course_resource"
    assert matches[0].status == "preview"
