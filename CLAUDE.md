# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run script: `python main.py --region [AWS_REGION]`
- Install dependencies: `pip install -r requirements.txt`
- Install development dependencies: `pip install -r requirements-dev.txt`
- Create virtual environment: `python -m venv env`
- Activate virtual environment: `source env/bin/activate` (Unix) or `env\Scripts\activate` (Windows)

## Code Style Guidelines
- Formatting: Use `black` for code formatting (the dependency can be found in `requirements-dev.txt`)
  - Simply running `black --line-length 100 .` will format the entire repository
  - Check if `black` is already installed in your virtual environment before offering to install it
  - Always run `black` after making changes to the code
- Type annotations: Use Python type hints for function parameters and return values
- Variable naming: Use snake_case for variables and functions, CamelCase for classes
- Error handling: Use try/except blocks with specific exception types
- Imports: Group standard library imports first, then third-party, then local imports
- String formatting: Prefer f-strings for string formatting
- Class structure: Follow OOP principles, use inheritance as in terraformer.py
- AWS resources: Follow the pattern in converters/* for adding new AWS resource support
- Comments and docstring: do not add docstrings or comments to the code unless the complex logic justifies it. 

## Miscellaneous
- Always disregard virtualenv folders, such as `env/` or `.venv/`, as well as any other `.gitignore`-ed files or folders.
  - Never include them in any code searches and refactors.
- After making change to the code, check if there are unused imports and remove them.