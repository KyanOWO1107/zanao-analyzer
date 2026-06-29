from collections.abc import Iterable

from zanao_monitor.models import DemandMatch, Post


Rule = tuple[str, str, tuple[str, ...]]


RESOURCE_CONTEXT_KEYWORDS: tuple[str, ...] = (
    "参考",
    "资料",
    "题库",
    "课件",
    "实验报告",
    "真题",
    "往年题",
    "试卷",
    "教材",
    "课本",
    "二手书",
    "代码",
    "报告",
    "习题",
    "作业",
    "求答案",
    "答案资料",
    "答案解析",
)


COURSE_PROJECT_ARTIFACT_KEYWORDS: tuple[str, ...] = (
    "课设报告",
    "课程设计代码",
    "代码",
    "报告",
    "参考",
    "资料",
)


RULES: tuple[Rule, ...] = (
    ("exam_paper", "request", ("真题", "往年题", "期末题", "往年卷", "试卷")),
    ("course_resource", "request", ("资料", "复习资料", "题库", "课件", "实验报告", "答案", "习题答案")),
    ("course_project", "request", ("课设", "课程设计", "课设报告", "课程设计代码")),
    ("textbook", "sell", ("二手书", "二手教材", "教材", "课本", "教科书")),
    ("ebook", "request", ("电子教材", "电子书", "教材pdf", "pdf教材", "PDF教材")),
)


def _has_resource_context(text: str) -> bool:
    return any(keyword in text for keyword in RESOURCE_CONTEXT_KEYWORDS)


def _filter_contextual_keywords(category: str, text: str, matched: tuple[str, ...]) -> tuple[str, ...]:
    if category == "course_resource" and matched == ("答案",) and "对答案" in text:
        return ()

    if category == "course_resource" and matched == ("答案",) and not _has_resource_context(text):
        return ()

    if category == "course_project":
        has_artifact = any(keyword in text for keyword in COURSE_PROJECT_ARTIFACT_KEYWORDS)
        if not has_artifact:
            return ()

    return matched


def classify_post(post: Post, rules: Iterable[Rule] = RULES) -> DemandMatch | None:
    text = f"{post.title}\n{post.content}"
    lowered = text.lower()

    for category, intent, keywords in rules:
        matched = tuple(keyword for keyword in keywords if keyword.lower() in lowered)
        matched = _filter_contextual_keywords(category, text, matched)
        if matched:
            score = min(1.0, 0.6 + len(matched) * 0.2)
            return DemandMatch(
                post=post,
                category=category,
                intent=intent,
                keywords=matched,
                score=score,
            )

    return None
