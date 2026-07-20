from app.routing.agents.complexity import score_complexity


def test_short_simple_prompt_scores_low():
    assert score_complexity("hi") <= 0.2


def test_multistep_prompt_scores_higher():
    simple = score_complexity("tell me a fact")
    multistep = score_complexity("First do X, then do Y, and finally summarize the result")
    assert multistep > simple


def test_code_block_increases_complexity():
    without_code = score_complexity("explain sorting algorithms")
    with_code = score_complexity("explain this: ```def sort(x): return sorted(x)```")
    assert with_code > without_code


def test_score_bounded_between_0_and_1():
    long_prompt = "word " * 5000
    score = score_complexity(long_prompt)
    assert 0.0 <= score <= 1.0
