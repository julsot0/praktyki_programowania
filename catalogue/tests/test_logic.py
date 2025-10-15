import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import *

def test_is_palindrome():
    assert is_palindrome("kajak") is True
def test_is_palindrome1():
    assert is_palindrome("test") is False
def test_is_palindrome2():
    assert is_palindrome("") is True
def test_is_palindrome3():
    assert is_palindrome("a") is True

def test_fibonacci():
    assert fibonacci(0) == 0
def test_fibonacci1():
    assert fibonacci(1) == 1
def test_fibonacci2():
    assert fibonacci(5) == 5
def test_fibonacci_negative():
    with pytest.raises(ValueError):
        fibonacci(-1)

def test_count_vowels():
    assert count_vowels("Python") == 2
def test_count_vowels1():
    assert count_vowels("AEIOUY") == 6
def test_count_vowels2():
    assert count_vowels("bcd") == 0
def test_count_vowels3():
    assert count_vowels("") == 0
def test_count_vowels4():
    assert count_vowels("Próba żółwia") == 5

def test_calculate_discount_valid():
    assert calculate_discount(100, 0.2) == 80.0
def test_calculate_discount_invalid():
    assert calculate_discount(50, 0) == 50.0
def test_calculate_discount_invalid2():
    assert calculate_discount(200, 1) == 0.0

def test_calculate_discount_invalid3():
    with pytest.raises(ValueError):
        calculate_discount(100, -0.1)
    with pytest.raises(ValueError):
        calculate_discount(100, 1.5)

def test_flatten_list():
    assert flatten_list([1, 2, 3]) == [1, 2, 3]
def flatten_list_1():
    assert flatten_list([1, [2, 3], [4, [5]]]) == [1, 2, 3, 4, 5]
def test_flatten_list2():
    assert flatten_list([]) == []
def test_flatten_list3():
    assert flatten_list([[[1]]]) == [1]
def test_flatten_list4():
    assert flatten_list([1, [2, [3, [4]]]]) == [1, 2, 3, 4]

def test_word_frequencies():
    assert word_frequencies("To be or not to be") == {"to": 2, "be": 2, "or": 1, "not": 1}
def test_word_frequencies1():
    assert word_frequencies("Hello, hello!") == {"hello": 2}
def test_word_frequencies2():
    assert word_frequencies("") == {}
def test_word_frequencies3():
    assert word_frequencies("Python Python python") == {"python": 3}
def test_word_frequencies4():
    assert word_frequencies("Ala ma kota, a kot ma Ale.") == {"ala": 1, "ma": 2, "kota": 1, "a": 1, "kot": 1, "ale": 1}

def test_is_prime():
    assert is_prime(2) == True
def test_is_prime1():
    assert is_prime(3) == True
def test_is_prime2():
    assert is_prime(4) == False
def test_is_prime3():
    assert is_prime(0) == False
def test_is_prime4():
    assert is_prime(1) == False
def test_is_prime5():
    assert is_prime(5) == True
def test_is_prime6():
    assert is_prime(97) == True