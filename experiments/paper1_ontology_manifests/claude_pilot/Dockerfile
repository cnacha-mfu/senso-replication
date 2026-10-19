# Agent sandbox for the Claude Code pilot (Paper 1, WP5 deviation 17). Only git and the task venv's needs; the claude binary,
# the uv-managed Pythons and the task root are bind-mounted at their host paths at run time.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates make && rm -rf /var/lib/apt/lists/*
RUN useradd -u 1000 -m agent
USER agent
