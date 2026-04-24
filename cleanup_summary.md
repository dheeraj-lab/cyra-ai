# Decoupling Personal Data for GitHub

This document summarizes the changes made to clean up the repository and move personal/sensitive information into external files that are ignored by Git.

## 1. Personality and System Prompt
- **Personal traits** (like girlfriend/horny personality modes) have been moved to `personality.txt`.
- This file is added to `.gitignore` to prevent it from being pushed.
- The `modules/llm.py` now uses a clean default prompt and loads the personal traits from the file path specified in `.env`.

## 2. Interests and Ideas
- **Personal interests, project ideas, and motivational quotes** have been moved to `interests.json`.
- This file is added to `.gitignore`.
- `modules/greeting.py` now loads this data dynamically and uses generic defaults if the file is missing.

## 3. Configuration and Contacts
- `cyra_config.json` and `contacts.json` are now ignored by Git.
- **Example templates** have been created for both:
  - `cyra_config.json.example`
  - `contacts.json.example`

## 4. Code Generalization
- Hardcoded references to **"Dheeraj"** and **"Delhi"** have been replaced with dynamic calls to the config system in:
  - `main.py`
  - `modules/agent.py`
  - `modules/greeting.py`
  - `modules/mood.py`
  - `modules/stt.py`
  - `dashboard/templates/index.html`

## 5. Environment Variables
- Added `PERSONALITY_FILE` and `INTERESTS_FILE` to `.env`.
- Updated `.env.example` to guide other users.

---
**Your repository is now clean and ready for GitHub!**
