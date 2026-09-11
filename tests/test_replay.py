import time

from brain.replay import Challenge, ChallengeResponse


def test_challenge_is_exact_single_use_and_tolerates_punctuation() -> None:
    challenge = ChallengeResponse()
    challenge._challenge = Challenge("blue river 42", time.monotonic() + 1)
    assert challenge.verify("Blue river 42!")
    assert not challenge.verify("blue river 42")


def test_expired_or_different_challenge_is_rejected() -> None:
    challenge = ChallengeResponse()
    challenge._challenge = Challenge("blue river 42", time.monotonic() - 1)
    assert not challenge.verify("blue river 42")
    challenge._challenge = Challenge("blue river 42", time.monotonic() + 1)
    assert not challenge.verify("blue river 43")
