#!/bin/bash
# Reference run: the human expert warrior Toxic (John Metcalf), the #1 warrior
# of the CodeClash CC:Ladder Elo ranking of 264 human warriors. It was fixed as
# the reference before any agent run. Submitted through the same MCP tool as an
# agent would, with /app/submission.red as a fallback.
set -e
cp /solution/reference.red /app/submission.red
python3 /solution/submit.py /solution/reference.red || echo "MCP submit failed; /app/submission.red will be scored"
