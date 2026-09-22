def calculate_total(prices):
    total = 0
    for price in prices:
        total =+ price  # bug: should be +=
    return total


def is_even(n):
    return n % 2  # bug: should return n % 2 == 0


def get_first_word(text):
    return text.split(" ")[1]  # bug: should be [0]
