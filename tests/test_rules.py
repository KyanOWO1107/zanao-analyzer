from zanao_monitor.models import Post
from zanao_monitor.rules import classify_post


def test_classifies_exam_paper_requests():
    post = Post(
        source="sample",
        post_id="p1",
        title="求往年真题",
        content="有没有高数 A 期末真题和答案，感谢",
        author="alice",
        created_at=1710000000,
    )

    match = classify_post(post)

    assert match is not None
    assert match.category == "exam_paper"
    assert "真题" in match.keywords


def test_classifies_course_resource_requests():
    post = Post(
        source="sample",
        post_id="p2",
        title="求复习资料和题库",
        content="有没有这门课的课件、题库、实验报告和答案",
        author="bob",
        created_at=1710000300,
    )

    match = classify_post(post)

    assert match is not None
    assert match.category == "course_resource"
    assert "题库" in match.keywords


def test_classifies_answer_requests_with_resource_context():
    post = Post(
        source="sample",
        post_id="p8",
        title="求题库答案",
        content="有没有这门课的习题答案或者资料",
        author="heidi",
        created_at=1710002100,
    )

    match = classify_post(post)

    assert match is not None
    assert match.category == "course_resource"


def test_classifies_course_project_requests():
    post = Post(
        source="sample",
        post_id="p4",
        title="求软件课设参考",
        content="想看看往年课设报告，课程设计代码也可以",
        author="dave",
        created_at=1710000900,
    )

    match = classify_post(post)

    assert match is not None
    assert match.category == "course_project"
    assert "课设" in match.keywords


def test_classifies_textbook_selling():
    post = Post(
        source="sample",
        post_id="p5",
        title="出二手教材",
        content="出高数教材和大物课本，二手书便宜出",
        author="erin",
        created_at=1710001200,
    )

    match = classify_post(post)

    assert match is not None
    assert match.category == "textbook"
    assert match.intent == "sell"


def test_ignores_general_second_hand_items():
    post = Post(
        source="sample",
        post_id="p6",
        title="出二手显示器",
        content="24 寸显示器，毕业出，价格可聊",
        author="frank",
        created_at=1710001500,
    )

    assert classify_post(post) is None


def test_ignores_ride_share_posts_for_current_scope():
    post = Post(
        source="sample",
        post_id="p7",
        title="拼车太原南",
        content="明早有拼车的吗",
        author="grace",
        created_at=1710001800,
    )

    assert classify_post(post) is None


def test_ignores_exam_discussion_with_answer_word_only():
    post = Post(
        source="sample",
        post_id="p9",
        title="清考求助",
        content="考完一对答案错了好多，不知道会不会挂",
        author="ivan",
        created_at=1710002400,
    )

    assert classify_post(post) is None


def test_ignores_course_project_discussion_without_resource_intent():
    post = Post(
        source="sample",
        post_id="p10",
        title="大二软件课设容易挂吗",
        content="老师会不会卡课设成绩",
        author="judy",
        created_at=1710002700,
    )

    assert classify_post(post) is None


def test_ignores_unrelated_posts():
    post = Post(
        source="sample",
        post_id="p3",
        title="今天食堂不错",
        content="晚饭窗口排队有点久，但是味道还行",
        author="carol",
        created_at=1710000600,
    )

    assert classify_post(post) is None
