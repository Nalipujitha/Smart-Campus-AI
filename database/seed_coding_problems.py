"""
Seed script for 20+ Coding Lab Practice Problems with starter code and test cases.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.extensions import db
from backend.models.coding import CodingProblem

CODING_PROBLEMS_DATA = [
    {
        "slug": "two-sum-problem",
        "title": "Sum of Two Numbers",
        "difficulty": "Easy",
        "topic": "Variables and Data Types",
        "description_markdown": "Write a program that takes two integers `A` and `B` from standard input and prints their sum.",
        "input_format": "Two integers `A` and `B` separated by a space on a single line.",
        "output_format": "A single integer representing the sum `A + B`.",
        "constraints": "-10^9 <= A, B <= 10^9",
        "sample_input": "5 7",
        "sample_output": "12",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef solve():\n    # Read input from standard input\n    line = sys.stdin.read().strip()\n    if not line:\n        return\n    a, b = map(int, line.split())\n    # Calculate and print sum\n    print(a + b)\n\nif __name__ == '__main__':\n    solve()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "5 7\n", "expected_output": "12", "is_hidden": False},
            {"input": "10 20\n", "expected_output": "30", "is_hidden": False},
            {"input": "-5 15\n", "expected_output": "10", "is_hidden": True},
            {"input": "0 0\n", "expected_output": "0", "is_hidden": True},
            {"input": "-100 -250\n", "expected_output": "-350", "is_hidden": True},
        ])
    },
    {
        "slug": "odd-or-even",
        "title": "Odd or Even Checker",
        "difficulty": "Easy",
        "topic": "Conditional Statements",
        "description_markdown": "Given an integer `N`, determine if it is `Even` or `Odd`. Print `'Even'` if the number is divisible by 2, otherwise print `'Odd'`.",
        "input_format": "A single integer `N`.",
        "output_format": "Print `Even` or `Odd`.",
        "constraints": "-10^9 <= N <= 10^9",
        "sample_input": "4",
        "sample_output": "Even",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    val = sys.stdin.read().strip()\n    if not val:\n        return\n    n = int(val)\n    # Your logic here\n    if n % 2 == 0:\n        print('Even')\n    else:\n        print('Odd')\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "4\n", "expected_output": "Even", "is_hidden": False},
            {"input": "7\n", "expected_output": "Odd", "is_hidden": False},
            {"input": "0\n", "expected_output": "Even", "is_hidden": True},
            {"input": "-3\n", "expected_output": "Odd", "is_hidden": True},
            {"input": "1000002\n", "expected_output": "Even", "is_hidden": True},
        ])
    },
    {
        "slug": "reverse-string",
        "title": "Reverse a String",
        "difficulty": "Easy",
        "topic": "Strings",
        "description_markdown": "Given a string `S`, print the reversed version of the string.",
        "input_format": "A single line containing string `S`.",
        "output_format": "The reversed string.",
        "constraints": "1 <= length(S) <= 1000",
        "sample_input": "hello",
        "sample_output": "olleh",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    s = sys.stdin.read().strip()\n    # Reverse and print string\n    print(s[::-1])\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "hello\n", "expected_output": "olleh", "is_hidden": False},
            {"input": "algorithm\n", "expected_output": "mhtirogla", "is_hidden": False},
            {"input": "a\n", "expected_output": "a", "is_hidden": True},
            {"input": "racecar\n", "expected_output": "racecar", "is_hidden": True},
            {"input": "SmartCampus 2026\n", "expected_output": "6202 supmCahtramS", "is_hidden": True}
        ])
    },
    {
        "slug": "palindrome-check",
        "title": "Check Palindrome String",
        "difficulty": "Easy",
        "topic": "Strings",
        "description_markdown": "Determine whether a given string is a palindrome. A string is a palindrome if it reads the same backward as forward (case-sensitive). Print `YES` if it is a palindrome, otherwise print `NO`.",
        "input_format": "A single line containing the string `S`.",
        "output_format": "Print `YES` or `NO`.",
        "constraints": "1 <= length(S) <= 5000",
        "sample_input": "radar",
        "sample_output": "YES",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    s = sys.stdin.read().strip()\n    if not s:\n        return\n    if s == s[::-1]:\n        print('YES')\n    else:\n        print('NO')\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "radar\n", "expected_output": "YES", "is_hidden": False},
            {"input": "world\n", "expected_output": "NO", "is_hidden": False},
            {"input": "noon\n", "expected_output": "YES", "is_hidden": True},
            {"input": "Madam\n", "expected_output": "NO", "is_hidden": True},
            {"input": "12321\n", "expected_output": "YES", "is_hidden": True},
        ])
    },
    {
        "slug": "factorial-calculator",
        "title": "Factorial Calculation",
        "difficulty": "Easy",
        "topic": "Functions",
        "description_markdown": "Given a non-negative integer `N`, compute its factorial `N!`. Note: `0! = 1`.",
        "input_format": "A single integer `N`.",
        "output_format": "A single integer representing `N!`.",
        "constraints": "0 <= N <= 20",
        "sample_input": "5",
        "sample_output": "120",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\nimport math\n\ndef main():\n    data = sys.stdin.read().strip()\n    if not data:\n        return\n    n = int(data)\n    print(math.factorial(n))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "5\n", "expected_output": "120", "is_hidden": False},
            {"input": "0\n", "expected_output": "1", "is_hidden": False},
            {"input": "1\n", "expected_output": "1", "is_hidden": True},
            {"input": "7\n", "expected_output": "5040", "is_hidden": True},
            {"input": "10\n", "expected_output": "3628800", "is_hidden": True},
        ])
    },
    {
        "slug": "fizzbuzz-classic",
        "title": "FizzBuzz Generator",
        "difficulty": "Easy",
        "topic": "Loops",
        "description_markdown": "Given an integer `N`, print numbers from `1` to `N` each on a new line. But for multiples of 3, print `Fizz` instead of the number, for multiples of 5, print `Buzz`, and for numbers which are multiples of both 3 and 5, print `FizzBuzz`.",
        "input_format": "A single integer `N`.",
        "output_format": "N lines according to the FizzBuzz rules.",
        "constraints": "1 <= N <= 100",
        "sample_input": "5",
        "sample_output": "1\n2\nFizz\n4\nBuzz",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    raw = sys.stdin.read().strip()\n    if not raw:\n        return\n    n = int(raw)\n    for i in range(1, n + 1):\n        if i % 15 == 0:\n            print('FizzBuzz')\n        elif i % 3 == 0:\n            print('Fizz')\n        elif i % 5 == 0:\n            print('Buzz')\n        else:\n            print(i)\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "5\n", "expected_output": "1\n2\nFizz\n4\nBuzz", "is_hidden": False},
            {"input": "3\n", "expected_output": "1\n2\nFizz", "is_hidden": False},
            {"input": "15\n", "expected_output": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz", "is_hidden": True},
        ])
    },
    {
        "slug": "fibonacci-number",
        "title": "Nth Fibonacci Number",
        "difficulty": "Easy",
        "topic": "Basic Mathematics",
        "description_markdown": "Compute the `N`-th Fibonacci number where `F(0) = 0`, `F(1) = 1`, and `F(n) = F(n-1) + F(n-2)` for `n >= 2`.",
        "input_format": "A single integer `N`.",
        "output_format": "The `N`-th Fibonacci number.",
        "constraints": "0 <= N <= 30",
        "sample_input": "6",
        "sample_output": "8",
        "points": 15,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef fib(n):\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n\ndef main():\n    val = sys.stdin.read().strip()\n    if not val:\n        return\n    print(fib(int(val)))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "6\n", "expected_output": "8", "is_hidden": False},
            {"input": "0\n", "expected_output": "0", "is_hidden": False},
            {"input": "1\n", "expected_output": "1", "is_hidden": True},
            {"input": "10\n", "expected_output": "55", "is_hidden": True},
            {"input": "20\n", "expected_output": "6765", "is_hidden": True},
        ])
    },
    {
        "slug": "prime-number-check",
        "title": "Prime Number Validator",
        "difficulty": "Easy",
        "topic": "Basic Mathematics",
        "description_markdown": "Determine if a given integer `N` is a prime number. Print `PRIME` if `N` is prime, otherwise print `NOT PRIME`.",
        "input_format": "A single integer `N`.",
        "output_format": "`PRIME` or `NOT PRIME`.",
        "constraints": "1 <= N <= 10^7",
        "sample_input": "29",
        "sample_output": "PRIME",
        "points": 15,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef is_prime(n):\n    if n <= 1:\n        return False\n    if n <= 3:\n        return True\n    if n % 2 == 0 or n % 3 == 0:\n        return False\n    i = 5\n    while i * i <= n:\n        if n % i == 0 or n % (i + 2) == 0:\n            return False\n        i += 6\n    return True\n\ndef main():\n    val = sys.stdin.read().strip()\n    if not val:\n        return\n    n = int(val)\n    print('PRIME' if is_prime(n) else 'NOT PRIME')\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "29\n", "expected_output": "PRIME", "is_hidden": False},
            {"input": "4\n", "expected_output": "NOT PRIME", "is_hidden": False},
            {"input": "1\n", "expected_output": "NOT PRIME", "is_hidden": True},
            {"input": "2\n", "expected_output": "PRIME", "is_hidden": True},
            {"input": "97\n", "expected_output": "PRIME", "is_hidden": True},
            {"input": "100\n", "expected_output": "NOT PRIME", "is_hidden": True},
        ])
    },
    {
        "slug": "sum-of-array-elements",
        "title": "Sum of Array Elements",
        "difficulty": "Easy",
        "topic": "Lists and Arrays",
        "description_markdown": "Given an array of `N` integers, calculate and print the sum of all elements.",
        "input_format": "First line contains `N`, the number of elements.\nSecond line contains `N` space-separated integers.",
        "output_format": "A single integer representing the sum.",
        "constraints": "1 <= N <= 10^4\n-10^5 <= arr[i] <= 10^5",
        "sample_input": "5\n1 2 3 4 5",
        "sample_output": "15",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    tokens = sys.stdin.read().split()\n    if not tokens:\n        return\n    n = int(tokens[0])\n    arr = [int(x) for x in tokens[1:n+1]]\n    print(sum(arr))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "5\n1 2 3 4 5\n", "expected_output": "15", "is_hidden": False},
            {"input": "3\n-10 0 10\n", "expected_output": "0", "is_hidden": False},
            {"input": "1\n42\n", "expected_output": "42", "is_hidden": True},
            {"input": "4\n100 200 300 400\n", "expected_output": "1000", "is_hidden": True},
        ])
    },
    {
        "slug": "find-largest-element",
        "title": "Find the Maximum Element",
        "difficulty": "Easy",
        "topic": "Lists and Arrays",
        "description_markdown": "Find the maximum integer in an array of `N` integers.",
        "input_format": "First line contains `N`.\nSecond line contains `N` space-separated integers.",
        "output_format": "The maximum element.",
        "constraints": "1 <= N <= 10^4",
        "sample_input": "4\n8 3 12 5",
        "sample_output": "12",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    tokens = sys.stdin.read().split()\n    if not tokens:\n        return\n    n = int(tokens[0])\n    arr = [int(x) for x in tokens[1:n+1]]\n    print(max(arr))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "4\n8 3 12 5\n", "expected_output": "12", "is_hidden": False},
            {"input": "5\n-5 -2 -10 -1 -8\n", "expected_output": "-1", "is_hidden": False},
            {"input": "1\n99\n", "expected_output": "99", "is_hidden": True},
            {"input": "6\n7 7 7 7 7 7\n", "expected_output": "7", "is_hidden": True},
        ])
    },
    {
        "slug": "second-largest-element",
        "title": "Second Largest Element in Array",
        "difficulty": "Medium",
        "topic": "Lists and Arrays",
        "description_markdown": "Given an array of integers, find the second largest distinct element. If no second largest distinct element exists, print `-1`.",
        "input_format": "First line contains `N`.\nSecond line contains `N` space-separated integers.",
        "output_format": "The second largest distinct element, or `-1`.",
        "constraints": "2 <= N <= 10^5",
        "sample_input": "5\n12 35 1 10 34",
        "sample_output": "34",
        "points": 20,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    tokens = sys.stdin.read().split()\n    if not tokens:\n        return\n    n = int(tokens[0])\n    arr = [int(x) for x in tokens[1:n+1]]\n    unique = sorted(list(set(arr)))\n    if len(unique) < 2:\n        print(-1)\n    else:\n        print(unique[-2])\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "5\n12 35 1 10 34\n", "expected_output": "34", "is_hidden": False},
            {"input": "3\n10 10 10\n", "expected_output": "-1", "is_hidden": False},
            {"input": "4\n5 1 4 2\n", "expected_output": "4", "is_hidden": True},
            {"input": "2\n100 50\n", "expected_output": "50", "is_hidden": True},
        ])
    },
    {
        "slug": "count-vowels-consonants",
        "title": "Count Vowels in String",
        "difficulty": "Easy",
        "topic": "Strings",
        "description_markdown": "Given a lowercase string `S`, count the number of vowels (`a`, `e`, `i`, `o`, `u`).",
        "input_format": "A single string `S` in lowercase.",
        "output_format": "A single integer representing the count of vowels.",
        "constraints": "1 <= length(S) <= 1000",
        "sample_input": "education",
        "sample_output": "5",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    s = sys.stdin.read().strip().lower()\n    vowels = set('aeiou')\n    count = sum(1 for c in s if c in vowels)\n    print(count)\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "education\n", "expected_output": "5", "is_hidden": False},
            {"input": "rhythm\n", "expected_output": "0", "is_hidden": False},
            {"input": "aeiou\n", "expected_output": "5", "is_hidden": True},
            {"input": "smartcampus\n", "expected_output": "3", "is_hidden": True},
        ])
    },
    {
        "slug": "binary-search-problem",
        "title": "Binary Search Algorithm",
        "difficulty": "Medium",
        "topic": "Searching and Sorting",
        "description_markdown": "Given a sorted array of `N` distinct integers and a target value `K`, return the 0-based index of `K` if found. If `K` is not present, print `-1`.",
        "input_format": "First line: `N` and `K` separated by space.\nSecond line: `N` sorted integers.",
        "output_format": "Index of `K` or `-1`.",
        "constraints": "1 <= N <= 10^5",
        "sample_input": "5 7\n1 3 5 7 9",
        "sample_output": "3",
        "points": 20,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n\ndef main():\n    tokens = sys.stdin.read().split()\n    if not tokens:\n        return\n    n, k = int(tokens[0]), int(tokens[1])\n    arr = [int(x) for x in tokens[2:2+n]]\n    print(binary_search(arr, k))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "5 7\n1 3 5 7 9\n", "expected_output": "3", "is_hidden": False},
            {"input": "5 4\n1 3 5 7 9\n", "expected_output": "-1", "is_hidden": False},
            {"input": "1 10\n10\n", "expected_output": "0", "is_hidden": True},
            {"input": "6 20\n2 4 8 10 15 20\n", "expected_output": "5", "is_hidden": True},
        ])
    },
    {
        "slug": "valid-parentheses",
        "title": "Valid Parentheses Checker",
        "difficulty": "Medium",
        "topic": "Problem-solving Fundamentals",
        "description_markdown": "Given a string `S` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.\nAn input string is valid if brackets are closed in the correct order.\nPrint `VALID` or `INVALID`.",
        "input_format": "A single line containing the bracket string.",
        "output_format": "`VALID` or `INVALID`.",
        "constraints": "1 <= length(S) <= 10^4",
        "sample_input": "()[]{}",
        "sample_output": "VALID",
        "points": 20,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef is_valid(s):\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return not stack\n\ndef main():\n    s = sys.stdin.read().strip()\n    if not s:\n        print('VALID')\n        return\n    print('VALID' if is_valid(s) else 'INVALID')\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "()[]{}\n", "expected_output": "VALID", "is_hidden": False},
            {"input": "(]\n", "expected_output": "INVALID", "is_hidden": False},
            {"input": "([{}])\n", "expected_output": "VALID", "is_hidden": True},
            {"input": "(((\n", "expected_output": "INVALID", "is_hidden": True},
            {"input": "{[]}\n", "expected_output": "VALID", "is_hidden": True},
        ])
    },
    {
        "slug": "anagram-checker",
        "title": "Valid Anagram",
        "difficulty": "Easy",
        "topic": "Strings",
        "description_markdown": "Given two strings `S1` and `S2`, check whether `S2` is an anagram of `S1`. Print `YES` if they are anagrams, otherwise `NO`.",
        "input_format": "Two space-separated strings `S1` and `S2`.",
        "output_format": "`YES` or `NO`.",
        "constraints": "1 <= length(S1), length(S2) <= 10^4",
        "sample_input": "anagram nagaram",
        "sample_output": "YES",
        "points": 15,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    tokens = sys.stdin.read().split()\n    if len(tokens) < 2:\n        return\n    s1, s2 = tokens[0], tokens[1]\n    if sorted(s1) == sorted(s2):\n        print('YES')\n    else:\n        print('NO')\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "anagram nagaram\n", "expected_output": "YES", "is_hidden": False},
            {"input": "rat car\n", "expected_output": "NO", "is_hidden": False},
            {"input": "listen silent\n", "expected_output": "YES", "is_hidden": True},
            {"input": "hello world\n", "expected_output": "NO", "is_hidden": True},
        ])
    },
    {
        "slug": "sum-of-digits",
        "title": "Sum of Digits of a Number",
        "difficulty": "Easy",
        "topic": "Basic Mathematics",
        "description_markdown": "Given a positive integer `N`, find the sum of its individual digits.",
        "input_format": "A single integer `N`.",
        "output_format": "Sum of the digits of `N`.",
        "constraints": "1 <= N <= 10^18",
        "sample_input": "12345",
        "sample_output": "15",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    s = sys.stdin.read().strip()\n    if not s:\n        return\n    print(sum(int(ch) for ch in s if ch.isdigit()))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "12345\n", "expected_output": "15", "is_hidden": False},
            {"input": "9999\n", "expected_output": "36", "is_hidden": False},
            {"input": "7\n", "expected_output": "7", "is_hidden": True},
            {"input": "1000000\n", "expected_output": "1", "is_hidden": True},
        ])
    },
    {
        "slug": "leap-year-checker",
        "title": "Leap Year Identifier",
        "difficulty": "Easy",
        "topic": "Conditional Statements",
        "description_markdown": "Determine whether a given year `Y` is a leap year. A year is a leap year if it is divisible by 4, except end-of-century years, which must be divisible by 400. Print `LEAP` or `NOT LEAP`.",
        "input_format": "A single integer `Y` representing the year.",
        "output_format": "`LEAP` or `NOT LEAP`.",
        "constraints": "1 <= Y <= 9999",
        "sample_input": "2024",
        "sample_output": "LEAP",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef is_leap(year):\n    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)\n\ndef main():\n    data = sys.stdin.read().strip()\n    if not data:\n        return\n    y = int(data)\n    print('LEAP' if is_leap(y) else 'NOT LEAP')\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "2024\n", "expected_output": "LEAP", "is_hidden": False},
            {"input": "1900\n", "expected_output": "NOT LEAP", "is_hidden": False},
            {"input": "2000\n", "expected_output": "LEAP", "is_hidden": True},
            {"input": "2023\n", "expected_output": "NOT LEAP", "is_hidden": True},
        ])
    },
    {
        "slug": "character-frequency",
        "title": "Character Frequency Counter",
        "difficulty": "Easy",
        "topic": "Strings",
        "description_markdown": "Given a string `S` (alphanumeric, no spaces) and a character `C`, count how many times `C` appears in `S` (case-sensitive).",
        "input_format": "First line contains `S`.\nSecond line contains `C`.",
        "output_format": "Number of occurrences of `C`.",
        "constraints": "1 <= length(S) <= 10^4",
        "sample_input": "engineering\ne",
        "sample_output": "3",
        "points": 10,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    lines = [l.strip() for l in sys.stdin.read().splitlines() if l.strip()]\n    if len(lines) < 2:\n        return\n    s, c = lines[0], lines[1]\n    print(s.count(c))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "engineering\ne\n", "expected_output": "3", "is_hidden": False},
            {"input": "success\ns\n", "expected_output": "3", "is_hidden": False},
            {"input": "python\nz\n", "expected_output": "0", "is_hidden": True},
            {"input": "Mississippi\ns\n", "expected_output": "4", "is_hidden": True},
        ])
    },
    {
        "slug": "bubble-sort-array",
        "title": "Sort an Array",
        "difficulty": "Easy",
        "topic": "Searching and Sorting",
        "description_markdown": "Given an array of `N` integers, sort the array in ascending order and print the elements separated by a space.",
        "input_format": "First line contains `N`.\nSecond line contains `N` space-separated integers.",
        "output_format": "The sorted integers on a single line separated by space.",
        "constraints": "1 <= N <= 10^4",
        "sample_input": "5\n64 25 12 22 11",
        "sample_output": "11 12 22 25 64",
        "points": 15,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    tokens = sys.stdin.read().split()\n    if not tokens:\n        return\n    n = int(tokens[0])\n    arr = [int(x) for x in tokens[1:n+1]]\n    arr.sort()\n    print(*(arr))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "5\n64 25 12 22 11\n", "expected_output": "11 12 22 25 64", "is_hidden": False},
            {"input": "3\n3 2 1\n", "expected_output": "1 2 3", "is_hidden": False},
            {"input": "4\n-1 -5 10 0\n", "expected_output": "-5 -1 0 10", "is_hidden": True},
            {"input": "1\n100\n", "expected_output": "100", "is_hidden": True},
        ])
    },
    {
        "slug": "power-of-two",
        "title": "Power of Two Check",
        "difficulty": "Easy",
        "topic": "Basic Mathematics",
        "description_markdown": "Given an integer `N`, determine if it is a power of two (i.e., `N = 2^k` for some integer `k >= 0`). Print `YES` or `NO`.",
        "input_format": "A single integer `N`.",
        "output_format": "`YES` or `NO`.",
        "constraints": "-2^31 <= N <= 2^31 - 1",
        "sample_input": "16",
        "sample_output": "YES",
        "points": 15,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef is_power_of_two(n):\n    return n > 0 and (n & (n - 1)) == 0\n\ndef main():\n    raw = sys.stdin.read().strip()\n    if not raw:\n        return\n    n = int(raw)\n    print('YES' if is_power_of_two(n) else 'NO')\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "16\n", "expected_output": "YES", "is_hidden": False},
            {"input": "18\n", "expected_output": "NO", "is_hidden": False},
            {"input": "1\n", "expected_output": "YES", "is_hidden": True},
            {"input": "0\n", "expected_output": "NO", "is_hidden": True},
            {"input": "1024\n", "expected_output": "YES", "is_hidden": True},
        ])
    },
    {
        "slug": "matrix-diagonal-sum",
        "title": "Matrix Main Diagonal Sum",
        "difficulty": "Medium",
        "topic": "Lists and Arrays",
        "description_markdown": "Given an `N x N` square matrix of integers, calculate the sum of elements on its main diagonal (from top-left to bottom-right).",
        "input_format": "First line: `N`.\nNext `N` lines: `N` space-separated integers each.",
        "output_format": "The sum of the main diagonal elements.",
        "constraints": "1 <= N <= 100",
        "sample_input": "3\n1 2 3\n4 5 6\n7 8 9",
        "sample_output": "15",
        "points": 20,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef main():\n    tokens = sys.stdin.read().split()\n    if not tokens:\n        return\n    n = int(tokens[0])\n    diag_sum = 0\n    idx = 1\n    for i in range(n):\n        for j in range(n):\n            val = int(tokens[idx])\n            if i == j:\n                diag_sum += val\n            idx += 1\n    print(diag_sum)\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "3\n1 2 3\n4 5 6\n7 8 9\n", "expected_output": "15", "is_hidden": False},
            {"input": "2\n10 20\n30 40\n", "expected_output": "50", "is_hidden": False},
            {"input": "1\n99\n", "expected_output": "99", "is_hidden": True},
            {"input": "4\n1 0 0 0\n0 2 0 0\n0 0 3 0\n0 0 0 4\n", "expected_output": "10", "is_hidden": True},
        ])
    },
    {
        "slug": "max-subarray-sum",
        "title": "Maximum Subarray Sum (Kadane's Algorithm)",
        "difficulty": "Medium",
        "topic": "Problem-solving Fundamentals",
        "description_markdown": "Given an array of integers `arr`, find the maximum possible sum of a non-empty contiguous subarray.",
        "input_format": "First line: `N`.\nSecond line: `N` space-separated integers.",
        "output_format": "A single integer denoting the maximum subarray sum.",
        "constraints": "1 <= N <= 10^5\n-10^4 <= arr[i] <= 10^4",
        "sample_input": "8\n-2 -3 4 -1 -2 1 5 -3",
        "sample_output": "7",
        "points": 25,
        "starter_code_json": json.dumps({
            "python": "import sys\n\ndef max_subarray_sum(arr):\n    max_so_far = arr[0]\n    curr_max = arr[0]\n    for x in arr[1:]:\n        curr_max = max(x, curr_max + x)\n        max_so_far = max(max_so_far, curr_max)\n    return max_so_far\n\ndef main():\n    tokens = sys.stdin.read().split()\n    if not tokens:\n        return\n    n = int(tokens[0])\n    arr = [int(x) for x in tokens[1:n+1]]\n    print(max_subarray_sum(arr))\n\nif __name__ == '__main__':\n    main()\n"
        }),
        "test_cases_json": json.dumps([
            {"input": "8\n-2 -3 4 -1 -2 1 5 -3\n", "expected_output": "7", "is_hidden": False},
            {"input": "4\n-1 -2 -3 -4\n", "expected_output": "-1", "is_hidden": False},
            {"input": "5\n1 2 3 4 5\n", "expected_output": "15", "is_hidden": True},
            {"input": "3\n5 -2 8\n", "expected_output": "11", "is_hidden": True},
        ])
    }
]


def seed_coding_problems():
    """Seed all coding problems into the database."""
    app = create_app()
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        added_count = 0
        updated_count = 0

        for item in CODING_PROBLEMS_DATA:
            existing = CodingProblem.query.filter_by(slug=item['slug']).first()
            if existing:
                existing.title = item['title']
                existing.difficulty = item['difficulty']
                existing.topic = item['topic']
                existing.description_markdown = item['description_markdown']
                existing.input_format = item['input_format']
                existing.output_format = item['output_format']
                existing.constraints = item['constraints']
                existing.sample_input = item['sample_input']
                existing.sample_output = item['sample_output']
                existing.starter_code_json = item['starter_code_json']
                existing.test_cases_json = item['test_cases_json']
                existing.points = item['points']
                updated_count += 1
            else:
                problem = CodingProblem(
                    slug=item['slug'],
                    title=item['title'],
                    difficulty=item['difficulty'],
                    topic=item['topic'],
                    description_markdown=item['description_markdown'],
                    input_format=item['input_format'],
                    output_format=item['output_format'],
                    constraints=item['constraints'],
                    sample_input=item['sample_input'],
                    sample_output=item['sample_output'],
                    starter_code_json=item['starter_code_json'],
                    test_cases_json=item['test_cases_json'],
                    points=item['points']
                )
                db.session.add(problem)
                added_count += 1

        db.session.commit()
        print(f"Successfully seeded Coding Problems: {added_count} created, {updated_count} updated. Total: {len(CODING_PROBLEMS_DATA)}")


if __name__ == '__main__':
    seed_coding_problems()
