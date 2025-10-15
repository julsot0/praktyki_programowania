import re
from collections import Counter

def is_palindrome(text: str) -> bool:
    if text == text[::-1]:
        return True
    return False

def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("Podano złą wartość")
    elif n == 0:
        return 0
    elif n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def count_vowels(text: str) -> int:
    vowels = "aeiouyąęó"
    count = 0
    for char in text.lower():
        if char in vowels:
            count += 1
    return count

def calculate_discount(price: float, discount: float) -> float:
    if not (0 <= discount <= 1):
        raise ValueError("Wartość zniżki od 0 do 1")
    if price < 0:
        raise ValueError("Cena nie może być ujemna")
    return price * (1 - discount)

def flatten_list(nested_list: list) -> list:
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result

def word_frequencies(text: str) -> dict:
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    return dict(Counter(words))

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True