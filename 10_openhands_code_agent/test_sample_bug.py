import sample_bug


def test_calculate_total():
    assert sample_bug.calculate_total([10, 20, 30]) == 60


def test_is_even():
    assert sample_bug.is_even(4) is True
    assert sample_bug.is_even(3) is False


def test_get_first_word():
    assert sample_bug.get_first_word("hello world") == "hello"
