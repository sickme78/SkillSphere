"""Seed problems for Problem of the Day. These are original, short exercises written for
SkillSphere. They are inserted into the `problems` table on first run; after that the
database is the source of truth - add or edit rows there (or append to PROBLEMS and restart,
new titles are inserted automatically) without touching any other code.

Fields: title, domain, topic, skill, difficulty, description, example_input, example_output,
constraints, hints (list), solution (explanation), code (reference solution), xp.
`skill` ties a problem to a skill name from data.ROLE_SKILLS so recommendations can find it.
"""


def P(title, domain, topic, skill, difficulty, description, ex_in, ex_out, constraints,
      hints, solution, code, xp=None):
    return {"title": title, "domain": domain, "topic": topic, "skill": skill,
            "difficulty": difficulty, "description": description, "example_input": ex_in,
            "example_output": ex_out, "constraints": constraints, "hints": hints,
            "solution": solution, "code": code,
            "xp": xp or {"Easy": 50, "Medium": 75, "Hard": 100}[difficulty]}


PROBLEMS = [
    # ------------------------------------------------------------ DSA
    P("Pair With Target Sum", "DSA", "Arrays", None, "Easy",
      "Given a list of integers and a target, return the indices of the two numbers that add up "
      "to the target. Exactly one valid pair exists and you may not use the same element twice.",
      "nums = [2, 7, 11, 15], target = 9", "[0, 1]",
      "2 <= len(nums) <= 10^4; values fit in a 32-bit integer",
      ["Checking every pair works but takes O(n^2). Can you do it in one pass?",
       "For each number, which value would you need to have seen earlier to reach the target?"],
      "Walk the list once, remembering each value's index in a dictionary. For each number, look "
      "up target - number; if it is already stored you have the pair. One pass, O(n) time, O(n) space.",
      "def pair_with_target(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n"
      "        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i"),
    P("Balanced Brackets", "DSA", "Stacks", None, "Easy",
      "Given a string containing only ()[]{} characters, decide whether the brackets are balanced: "
      "every opener is closed by the same type, in the correct order.",
      '"{[()]}"', "true  (and \"([)]\" gives false)", "0 <= length <= 10^4",
      ["The most recently opened bracket must be the first one closed.",
       "Which data structure gives you last-in, first-out access?"],
      "Push openers on a stack. On a closer, the stack must be non-empty and its top must be the "
      "matching opener. The string is balanced if the stack is empty at the end. O(n).",
      "def balanced(s):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n"
      "        if ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n"
      "        else:\n            stack.append(ch)\n    return not stack"),
    P("Find the First Position", "DSA", "Binary Search", None, "Easy",
      "Given a sorted list of integers and a value, return the index of its first occurrence, or -1 "
      "if it is absent. Aim for O(log n).",
      "nums = [1, 2, 2, 2, 5], value = 2", "1", "0 <= len(nums) <= 10^5; list is sorted ascending",
      ["Plain binary search finds *an* occurrence. What should you do when you find one?",
       "Keep searching the left half after a match, remembering the best index so far."],
      "Run binary search; when nums[mid] equals the value, record mid and continue into the left half "
      "(hi = mid - 1). The last recorded index is the first occurrence. O(log n).",
      "def first_position(nums, value):\n    lo, hi, found = 0, len(nums) - 1, -1\n    while lo <= hi:\n"
      "        mid = (lo + hi) // 2\n        if nums[mid] == value:\n            found, hi = mid, mid - 1\n"
      "        elif nums[mid] < value:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return found"),
    P("Best Contiguous Stretch", "DSA", "Dynamic Programming", None, "Medium",
      "Given a list of integers (positive and negative), find the largest sum of any contiguous "
      "sub-list.", "[-2, 1, -3, 4, -1, 2, 1, -5, 4]", "6   (the stretch [4, -1, 2, 1])",
      "1 <= len(nums) <= 10^5",
      ["At each position, you either extend the previous stretch or start fresh.",
       "If the running sum drops below zero, would you ever want to carry it forward?"],
      "Keep the best sum of a stretch ending here: max(n, running + n). Track the maximum seen. "
      "This is Kadane's algorithm - O(n) time, O(1) space.",
      "def best_stretch(nums):\n    running = best = nums[0]\n    for n in nums[1:]:\n"
      "        running = max(n, running + n)\n        best = max(best, running)\n    return best"),
    P("Reverse a Linked List", "DSA", "Linked Lists", None, "Medium",
      "Given the head of a singly linked list, reverse it and return the new head. Do it in place.",
      "1 -> 2 -> 3 -> None", "3 -> 2 -> 1 -> None", "0 <= nodes <= 5000",
      ["You only need to change where each node's next pointer points.",
       "Keep track of the previous node as you walk forward; save next before overwriting it."],
      "Walk the list with three pointers: prev, current, and the saved next. Point current.next at "
      "prev, then step all three forward. When current is None, prev is the new head. O(n), O(1) space.",
      "def reverse(head):\n    prev = None\n    while head:\n        nxt = head.next\n        head.next = prev\n"
      "        prev, head = head, nxt\n    return prev"),
    # ------------------------------------------------------------ Python
    P("Count the Words", "Python", "Dictionaries", "Python", "Easy",
      "Write a function that returns how many times each word appears in a sentence, ignoring "
      "case and surrounding punctuation.", '"The cat and the hat."', "{'the': 2, 'cat': 1, 'and': 1, 'hat': 1}",
      "Words are separated by spaces",
      ["Normalise first: lower-case and strip punctuation from each word.",
       "A dictionary with .get(word, 0) + 1 does the counting."],
      "Split on whitespace, normalise each token with lower() and strip(punctuation), skip empties, "
      "and count with a dictionary (or collections.Counter).",
      "import string\n\ndef count_words(text):\n    counts = {}\n    for raw in text.split():\n"
      "        w = raw.lower().strip(string.punctuation)\n        if w:\n            counts[w] = counts.get(w, 0) + 1\n    return counts"),
    P("Anagram Check", "Python", "Strings", "Python", "Easy",
      "Return True if two strings are anagrams of each other (same letters, same counts), ignoring "
      "spaces and case.", '"Dormitory", "Dirty room"', "True", "Letters and spaces only",
      ["Two strings are anagrams if their sorted letters are identical.",
       "Remove spaces and lower-case both before comparing."],
      "Normalise both strings, then compare sorted(letters) - or compare Counter objects for O(n).",
      "def is_anagram(a, b):\n    clean = lambda s: sorted(s.replace(' ', '').lower())\n    return clean(a) == clean(b)"),
    P("Group by First Letter", "Python", "Lists and Dicts", "Python", "Medium",
      "Given a list of words, group them into a dictionary keyed by their first letter (lower-case), "
      "keeping the original order inside each group.", '["apple", "avocado", "banana", "blueberry"]',
      "{'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry']}", "Words are non-empty",
      ["setdefault or defaultdict(list) saves a lot of if-statements.", "word[0].lower() is your key."],
      "Loop once, appending each word to groups[word[0].lower()]. defaultdict(list) removes the "
      "need to check whether the key exists. O(n).",
      "from collections import defaultdict\n\ndef group_by_letter(words):\n    groups = defaultdict(list)\n"
      "    for w in words:\n        groups[w[0].lower()].append(w)\n    return dict(groups)"),
    P("Bank Account Class", "Python", "OOP", "OOP", "Medium",
      "Design a BankAccount class with deposit(amount) and withdraw(amount). A withdrawal larger "
      "than the balance must raise ValueError and leave the balance unchanged. Keep the balance private.",
      "acct = BankAccount(100); acct.withdraw(30); acct.balance", "70",
      "Amounts are positive numbers",
      ["Use a leading underscore for the stored balance and expose it with a property.",
       "Validate before changing state, not after."],
      "Encapsulation: the balance lives in _balance, changes only through methods that validate "
      "input first. A read-only property exposes it without letting callers assign to it.",
      "class BankAccount:\n    def __init__(self, balance=0):\n        self._balance = balance\n\n"
      "    @property\n    def balance(self):\n        return self._balance\n\n    def deposit(self, amount):\n"
      "        self._balance += amount\n\n    def withdraw(self, amount):\n        if amount > self._balance:\n"
      "            raise ValueError('insufficient funds')\n        self._balance -= amount"),
    P("Add a Simple Endpoint", "Python", "Flask Routing", "Flask", "Easy",
      "Write a Flask route GET /greet/<name> that returns JSON {\"message\": \"Hello, <name>!\"}.",
      "GET /greet/Asha", '{"message": "Hello, Asha!"}', "Use Flask only",
      ["Flask turns <name> in the route into a function argument.", "jsonify builds a JSON response."],
      "The URL variable is passed to the view function by name. jsonify sets the JSON content type "
      "for you.",
      "from flask import Flask, jsonify\napp = Flask(__name__)\n\n@app.route('/greet/<name>')\n"
      "def greet(name):\n    return jsonify(message=f'Hello, {name}!')"),
    P("Clean a Column", "Python", "Pandas", "Pandas", "Medium",
      "A DataFrame column 'price' holds strings like '$1,200' and some blanks. Convert it to a "
      "numeric column, treating blanks as missing, then fill missing values with the median.",
      "['$1,200', '', '$800']", "[1200.0, 1000.0, 800.0]", "Use pandas",
      ["Strip '$' and ',' with str.replace first.",
       "pd.to_numeric(..., errors='coerce') turns blanks into NaN."],
      "Remove the currency symbols, convert with to_numeric(errors='coerce') so blanks become NaN, "
      "then fillna(median).",
      "import pandas as pd\n\ndef clean_price(df):\n    s = df['price'].str.replace(r'[$,]', '', regex=True)\n"
      "    s = pd.to_numeric(s, errors='coerce')\n    df['price'] = s.fillna(s.median())\n    return df"),
    # ------------------------------------------------------------ JavaScript
    P("Counter With Private State", "JavaScript", "Closures", "JavaScript", "Easy",
      "Write makeCounter() that returns a function. Each call to the returned function should "
      "return 1, then 2, then 3 ... with no global variable.", "const next = makeCounter(); next(); next();",
      "1, then 2", "No globals; each counter is independent",
      ["A function remembers variables from where it was created.",
       "Declare the count inside makeCounter, outside the returned function."],
      "The inner function closes over `count`, so the value survives between calls but cannot be "
      "touched from outside. Two counters get two separate variables.",
      "function makeCounter() {\n  let count = 0;\n  return () => ++count;\n}"),
    P("Flatten Nested Arrays", "JavaScript", "Arrays and Recursion", "JavaScript", "Medium",
      "Write flatten(arr) that turns an arbitrarily nested array into a single flat array, without "
      "using Array.prototype.flat.", "[1, [2, [3, [4]]], 5]", "[1, 2, 3, 4, 5]", "Nesting depth is unknown",
      ["If an item is itself an array, you want to flatten *that* first.",
       "Array.isArray tells you which case you are in; reduce can collect the results."],
      "Recursion: for each item, if it is an array, flatten it and spread the result; otherwise "
      "keep the value. reduce accumulates everything into one array.",
      "const flatten = (arr) =>\n  arr.reduce((out, x) => Array.isArray(x) ? out.concat(flatten(x)) : out.concat(x), []);"),
    P("Debounce a Function", "JavaScript", "Higher-order Functions", "JavaScript", "Medium",
      "Write debounce(fn, ms) that delays calling fn until ms milliseconds have passed without "
      "another call. This is how search boxes avoid firing a request on every keystroke.",
      "debounced('a'); debounced('ab'); debounced('abc');", "fn runs once, with 'abc', after the pause",
      "Preserve the arguments of the latest call",
      ["You need a timer id that survives between calls.", "Each new call should cancel the pending timer."],
      "Keep a timeout handle in a closure. Every call clears the previous timeout and starts a new "
      "one, so fn only runs after a quiet period.",
      "function debounce(fn, ms) {\n  let timer;\n  return (...args) => {\n    clearTimeout(timer);\n"
      "    timer = setTimeout(() => fn(...args), ms);\n  };\n}"),
    P("Counter Component", "JavaScript", "React State", "React", "Easy",
      "Build a React function component with a button that shows how many times it was clicked, using "
      "the useState hook.", "Click three times", "Button text reads: Clicked 3 times", "Function component only",
      ["State is declared with const [value, setValue] = useState(initial).",
       "Update with the setter - never modify the variable directly."],
      "useState returns the current value and a setter; calling the setter re-renders the component "
      "with the new value. Use the functional form when the new value depends on the old one.",
      "import { useState } from 'react';\n\nexport default function Counter() {\n"
      "  const [count, setCount] = useState(0);\n  return (\n    <button onClick={() => setCount(c => c + 1)}>\n"
      "      Clicked {count} times\n    </button>\n  );\n}"),
    P("Request Logger Middleware", "JavaScript", "Express Middleware", "Express", "Easy",
      "Write an Express middleware that logs the HTTP method and URL of every request, then lets "
      "the request continue to the route handlers.", "GET /users", "Console: GET /users", "Express 4",
      ["Middleware receives (req, res, next).", "If you forget to call next(), the request hangs."],
      "A middleware runs before the route handlers. It logs req.method and req.originalUrl, then "
      "calls next() to pass control on. Register it with app.use before your routes.",
      "app.use((req, res, next) => {\n  console.log(req.method, req.originalUrl);\n  next();\n});"),
    # ------------------------------------------------------------ SQL
    P("Second Highest Salary", "SQL", "Subqueries", "SQL", "Medium",
      "Table employees(id, name, salary). Write a query that returns the second highest distinct "
      "salary, or NULL if there is none.", "salaries: 100, 300, 200, 300", "200", "Use standard SQL",
      ["Distinct matters: two people can share the top salary.",
       "Find the maximum salary that is lower than the overall maximum."],
      "Take MAX(salary) over rows whose salary is below the overall MAX. If no such row exists the "
      "aggregate returns NULL, which is exactly the required result.",
      "SELECT MAX(salary) AS second_highest\nFROM employees\nWHERE salary < (SELECT MAX(salary) FROM employees);"),
    P("Customers Without Orders", "SQL", "Joins", "SQL", "Easy",
      "Tables customers(id, name) and orders(id, customer_id). List the names of customers who have "
      "never placed an order.", "customer 3 has no rows in orders", "that customer's name",
      "Use a join or a subquery",
      ["An inner join drops the customers you are looking for.",
       "A LEFT JOIN keeps every customer; unmatched order columns are NULL."],
      "LEFT JOIN orders onto customers and keep rows where the order id IS NULL - those customers "
      "had nothing to match.",
      "SELECT c.name\nFROM customers c\nLEFT JOIN orders o ON o.customer_id = c.id\nWHERE o.id IS NULL;"),
    P("Busy Departments", "SQL", "GROUP BY and HAVING", "SQL", "Medium",
      "Table employees(id, name, dept). Return each department that has more than 3 employees, "
      "with its head-count, largest first.", "dept A has 5, dept B has 2", "A | 5",
      "Use GROUP BY",
      ["WHERE filters rows before grouping. What filters groups afterwards?",
       "COUNT(*) gives the size of each group."],
      "Group by dept, count rows, filter groups with HAVING COUNT(*) > 3, and ORDER BY the count "
      "descending.",
      "SELECT dept, COUNT(*) AS headcount\nFROM employees\nGROUP BY dept\nHAVING COUNT(*) > 3\n"
      "ORDER BY headcount DESC;"),
    # ------------------------------------------------------------ DBMS
    P("Spot the Normal Form Violation", "DBMS", "Normalisation", "Database Design", "Medium",
      "A table orders(order_id, customer_id, customer_city, product, qty) has primary key "
      "(order_id, product). customer_city depends only on customer_id. Which normal form does this "
      "break, and how do you fix it?", "orders(order_id, customer_id, customer_city, product, qty)",
      "Violates 2NF/3NF - split customer data into its own table",
      "Explain in a few sentences",
      ["Ask: does customer_city depend on the whole key, or on something else?",
       "Facts about a customer belong in a table about customers."],
      "customer_city is determined by customer_id, which is not the key (and customer_id itself is "
      "determined by order_id). That is a transitive dependency, so the table is not in 3NF. Move "
      "customer_id and customer_city into customers(customer_id, city) and keep only the "
      "customer_id foreign key in orders.",
      "customers(customer_id PK, city)\norders(order_id PK, customer_id FK)\norder_items(order_id FK, product, qty)"),
    P("Why ACID Matters", "DBMS", "Transactions", "SQL", "Easy",
      "A transfer subtracts Rs 500 from account A and adds it to account B. The server crashes after "
      "the first step. Which ACID property prevents A from losing the money, and how?",
      "debit succeeds, credit never runs", "Atomicity - the whole transaction is rolled back",
      "Answer in two or three sentences",
      ["Think about the 'all or nothing' property.", "What does the database do with an unfinished transaction on recovery?"],
      "Atomicity: both updates form one transaction, so either both are applied or neither is. After "
      "the crash the database uses its log to roll back the incomplete debit.",
      "BEGIN;\nUPDATE accounts SET balance = balance - 500 WHERE id = 'A';\n"
      "UPDATE accounts SET balance = balance + 500 WHERE id = 'B';\nCOMMIT;"),
    # ------------------------------------------------------------ Web Development
    P("Center It With Flexbox", "Web Development", "CSS Layout", "CSS", "Easy",
      "Centre a card both horizontally and vertically inside a full-height container using Flexbox.",
      "<div class=\"page\"><div class=\"card\"></div></div>", "Card sits in the exact centre of the viewport",
      "No absolute positioning",
      ["Flexbox has two axes. One property aligns each.", "The container needs a height to centre inside."],
      "Make the parent a flex container; justify-content centres on the main axis and align-items on "
      "the cross axis. min-height: 100vh gives it room.",
      ".page {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n  min-height: 100vh;\n}"),
    P("Stack on Small Screens", "Web Development", "Responsive Design", "Responsive Design", "Easy",
      "A row of three cards should become a single column below 600px wide. Write the CSS.",
      ".cards with three children", "Three columns on desktop, one column on phones", "Use a media query",
      ["Start with the desktop layout, then override for small widths.", "A media query can change flex-direction."],
      "Lay the cards out in a row with Flexbox, then inside @media (max-width: 600px) switch to a "
      "column so they stack.",
      ".cards { display: flex; gap: 1rem; }\n@media (max-width: 600px) {\n  .cards { flex-direction: column; }\n}"),
    P("Fetch With Error Handling", "Web Development", "APIs", "APIs", "Medium",
      "Write an async function getUser(id) that fetches /api/users/<id>, throws a helpful error "
      "when the response is not OK, and otherwise returns the parsed JSON.",
      "getUser(7) when the server returns 404", "Throws: Request failed with status 404",
      "Use fetch and async/await",
      ["fetch only rejects on network failure - a 404 still resolves.", "Check response.ok yourself."],
      "fetch resolves even for HTTP errors, so check response.ok and throw. Callers can then use "
      "try/catch to show an error state.",
      "async function getUser(id) {\n  const res = await fetch(`/api/users/${id}`);\n"
      "  if (!res.ok) throw new Error(`Request failed with status ${res.status}`);\n  return res.json();\n}"),
    # ------------------------------------------------------------ C++ / Java
    P("Swap Without a Copy", "C++", "Pointers and References", None, "Easy",
      "Write a C++ function that swaps two integers so the caller's variables are changed.",
      "int a = 1, b = 2; swap_ints(a, b);", "a == 2, b == 1", "Do not return anything",
      ["Passing by value changes only copies.", "Take the parameters by reference (int&)."],
      "References let the function modify the caller's variables directly. Use a temporary to hold one value.",
      "void swap_ints(int& a, int& b) {\n    int tmp = a;\n    a = b;\n    b = tmp;\n}"),
    P("Equals vs ==", "Java", "Strings", None, "Easy",
      "In Java, why can `new String(\"hi\") == \"hi\"` be false while `.equals` is true? Which should "
      "you use to compare string contents?", "String a = new String(\"hi\"); String b = \"hi\";",
      "a == b is false; a.equals(b) is true", "Explain in a few sentences",
      ["== compares something other than the characters.", "Think about where each String object lives."],
      "== compares object references; new String creates a distinct object, so the references differ. "
      "equals compares the characters. Always use equals (or equalsIgnoreCase) for string content.",
      "String a = new String(\"hi\");\nString b = \"hi\";\nSystem.out.println(a == b);       // false\n"
      "System.out.println(a.equals(b));  // true"),
    # ------------------------------------------------------------ Aptitude / CS fundamentals
    P("Is It a Power of Two?", "CS Fundamentals", "Bit Manipulation", None, "Easy",
      "Decide whether a positive integer is a power of two without loops.", "16", "true  (and 18 gives false)",
      "1 <= n <= 2^31",
      ["Look at powers of two in binary: 1, 10, 100, 1000.", "What does n - 1 look like in binary?"],
      "A power of two has exactly one set bit. n & (n - 1) clears the lowest set bit, so the result is "
      "0 exactly when there was only one. O(1).",
      "def is_power_of_two(n):\n    return n > 0 and (n & (n - 1)) == 0"),
    P("Loop Complexity", "CS Fundamentals", "Time Complexity", None, "Easy",
      "What is the time complexity of: for i in 1..n: for j in 1..n: if j % 2 == 0: print(j)? "
      "Explain why the inner condition does not change it.", "n = 1000", "O(n^2)",
      "Answer with reasoning",
      ["Count how many times the inner body runs.", "A constant factor (like half) is dropped in Big-O."],
      "The inner loop runs n times for each of n iterations: n^2 checks. The condition prints on half of "
      "them, but n^2 / 2 is still O(n^2) because constants are ignored.",
      "# n * n iterations -> O(n^2)"),
]
