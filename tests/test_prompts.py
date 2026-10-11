from lifelog_coach import prompts


def test_build_judge_prompt_includes_content():
    p = prompts.build_judge_prompt("hello-log")
    assert "hello-log" in p


def test_build_review_prompt_includes_content():
    p = prompts.build_review_prompt("week-data")
    assert "week-data" in p
