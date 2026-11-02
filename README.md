# PERSONAL FINANCE TRACKER

#### DESCRIPTION

If you're reading this, you're probably grading my final project for CS50P, or maybe you just stumbled upon this repository. Either way, welcome!

This project started as my final project for CS50's Introduction to Programming with Python, but I see it as the first module of something bigger: my future Personal App. I developed it throughout the course, adding features as I learned. What started as a simple way to record income and expenses gradually became a more complete application.

Because I've been building this since the beginning, you might notice there are no "classes" or some advanced concepts taught in the final weeks. I chose to avoid a heavy refactor because I was terrified of breaking what I had already built. It's a snapshot of my learning journey, built step-by-step.


## FEATURES

- Record income and expenses using predefined or custom categories.
- Calculate balances, view summaries (this month, last month, or all time), and list recent transactions.
- Check the current balance in another currency using live exchange rates.
- Change the base currency and convert existing transactions and budgets.
- Set monthly budgets and receive warnings when spending approaches a limit.
- Export financial reports in Markdown format.
- Save transactions, currency settings, budgets, and the user's name locally.


## DESIGN DECISIONS AND CHALLENGES

**The Float Disaster:** Initially, I used `float` to handle money. It worked fine until I learned that floats can cause rounding errors (like `0.1 + 0.2 = 0.30000000000000004`). I hated the idea of my app being inaccurate, so I learned about the `decimal` module.

Moving from `float` to `Decimal` broke my entire code. Every math operation and CSV read had to be rewritten. I implemented `quantize(Decimal("0.01"))` to force two decimal places and ensured `add_transaction` checked amounts *before* quantizing. Otherwise, `0.004` could round down to `0.00` and break my logic.

**Why So Many Loops and Menus?** I absolutely **hate** restarting a terminal program every time I make a typo. If you type "expense" when the program expects "expenses", it can be infuriating. That's why this app uses `while` loops and numerical menus. You don't need to memorize commands; just look at the screen, press a number, and hit Enter.

**The Weird "Greyed Out" Code:** In VS Code, methods like `.strip()`, `.replace(",", ".")`, or `.quantize(...)` sometimes appear greyed out because the linter considers them redundant. However, users might paste numbers with spaces or use commas as decimal separators. I kept these operations to handle such cases. I learned the editor is just a tool; *I* know what my code needs to handle.

**Data Persistence:** I hated losing my data, so the lecture where David Malan introduced `csv` was my favorite (right after loops). This project uses multiple files to store information. I also used `datetime` to track transactions. Every time you add something, it stamps today's date.


## PROJECT FILES

- `project.py`: The main application.
- `test_project.py`: Tests for core functions and important edge cases.
- `finance_data.csv`: Stores transactions.
- `finance_config.csv`: Stores the selected currency and symbol.
- `finance_budgets.json`: Stores monthly budget limits.
- `finance_user.csv`: Stores the user's name.
- `finance_report_YYYY-MM-DD.md`: The exported financial report.

These data files are created when needed, so they do not all have to exist before the first run.


## REQUIREMENTS AND USAGE

The application uses Python's standard library, so no additional packages are needed to run the main program. An internet connection is required for live exchange rates.

To start the application, run:
`python project.py`

Follow the numbered menu options. Where supported, type "back" or enter "0" to return to a previous menu.

To run the tests, install pytest if necessary, then execute:
`pytest`

I have a confession about testing. I enjoy going to the terminal, entering wrong inputs, and watching how the program responds. I like the manual feedback. In my test file, I focused on core logic and edge cases, such as rejecting `NaN` or `0.004`. I know automated tests are important for larger projects, and I plan to expand the test suite as this Personal App grows.


## FINAL THOUGHTS

There's still room to improve the application, especially by expanding the test suite and covering more file operations and error scenarios. I see this as a starting point for the larger Personal App I want to build.

There's also a small Easter egg hidden somewhere in the application. I'll leave that one for you to discover.

I'm proud of how far this project has come, and I'm looking forward to applying what I've learned to my next projects.

Thank you for taking the time to look at my work!

This was me, Goodbye!
