> Historical V1 documentation. Use README.md for the current setup and scope.

# Car Rental Management — Full-Stack Web Application

**Python · Flask · REST API · MySQL · HTML · JavaScript · AJAX**

An educational full-stack application with a browser interface and a Python API for working with **cars and customers** in a relational database.

![Application screenshot](./images/pageview.jpg)

## Why this project matters

Rather than analysing a dataset in isolation, this project brings together application structure, data persistence and user-facing workflows. It demonstrates how a frontend, API routes and SQL database fit together.

## Features in the coursework

- Flask server exposing car and customer endpoints.
- REST-style operations for creating, viewing, updating and deleting records.
- MySQL data access layer and database initialisation script.
- HTML and JavaScript frontend with asynchronous requests.
- Basic demonstration login mechanism.

## Architecture

```text
Browser interface (static/CarServer.html)
             │  HTTP / AJAX
             ▼
       Flask (CarServer.py)
             │
             ▼
    CarDao.py / CustomerDao.py
             │
             ▼
          MySQL database
```

## Project files

| File | Role |
| --- | --- |
| [CarServer.py](./CarServer.py) | Flask application and endpoints |
| [CarDao.py](./CarDao.py) | Car data operations |
| [CustomerDao.py](./CustomerDao.py) | Customer data operations |
| [createDatabase.py](./createDatabase.py) | Database setup |
| [dbconfig.py](./dbconfig.py) | Local MySQL connection settings |
| [static/CarServer.html](./static/CarServer.html) | Browser interface |
| [testCarDao.py](./testCarDao.py) | Data access exercises/tests |

## Run locally

1. Install Python and MySQL; create a virtual environment.
2. Install the packages in [requirements.txt](./requirements.txt) (`pip install -r requirements.txt`).
3. Set `DB_HOST`, `DB_USER`, `DB_PASSWORD` and `DB_NAME` for a **local test** MySQL server, plus `DEMO_USERNAME` and `DEMO_PASSWORD` for the example login. Do not use real credentials.
4. Run `python createDatabase.py`, then `python CarServer.py`.
5. Open the local URL printed by Flask.

A separate [PythonAnywhere deployment experiment](https://github.com/benjanning/deploytopythonanywhere) is also available. Its historical hosted demo may no longer be running.

**Security and maturity:** This is coursework code, not a production-hardened booking system. The demo authentication, input validation, configuration and error handling would need strengthening for real users. Do not deploy it with the example credentials.

---

Part of my Higher Diploma in Computing (Data Analytics). [View the full portfolio](https://benjanning.github.io/projects/).

## Verified local demonstration (October 2026)

Install the updated requirements in a virtual environment. In PowerShell, run `$env:DEMO_MODE="1"` and `python CarServer.py`; on macOS/Linux run `DEMO_MODE=1 python CarServer.py`. Open http://127.0.0.1:5000. This explicit mode uses temporary synthetic records, not MySQL. Run `python -m unittest test_api.py`.

The original MySQL path remains available with DEMO_MODE unset and DB_* plus DEMO_USERNAME/DEMO_PASSWORD configured. API routes now require demo authentication in MySQL mode. MySQL integration has not been executed in this review. The setup script preserves existing databases and seeds only empty tables. The interface was refreshed while retaining its existing table/form workflows. Missing records retain HTTP 404; record inputs are checked. This remains a local academic prototype.
