#!/bin/bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

WORKTREE="/Users/amirgefen/Documents/CursorP/stocky/.claude/worktrees/gifted-black"
MAIN_VENV="/Users/amirgefen/Documents/CursorP/stocky/backend/venv"

# Start backend (worktree code, main venv)
(cd "$WORKTREE/backend" && "$MAIN_VENV/bin/uvicorn" app.main:app --reload --host 127.0.0.1 --port 8000) &

# Frontend: use main repo so Cursor edits on stocky/frontend are what you see on :3000
MAIN_FRONTEND="/Users/amirgefen/Documents/CursorP/stocky/frontend"
(cd "$MAIN_FRONTEND" && /usr/local/bin/npm run dev)
