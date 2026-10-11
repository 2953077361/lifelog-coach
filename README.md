# lifelog-coach

Read your markdown life logs. Let AI judge the trend, catch broken targets, and tell you the next step.

No app. No database. No cloud. Just your notes and one command.

```
your markdown logs  ->  AI judge  ->  trends / red lines / next step
```

## Why

I keep my life in plain markdown — sleep, training, food, money, time, work.
Every day I want a second pair of eyes: what is the trend, what target did I miss,
and what is the one thing to do tomorrow. This tool does exactly that.

## Install

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <your-fork-url> lifelog-coach
cd lifelog-coach
uv venv
uv pip install -e .
```

## Configure

Works with any OpenAI-compatible endpoint. It defaults to DeepSeek.

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
```

| Variable | Default | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | required |
| `OPENAI_BASE_URL` | `https://api.deepseek.com` | any OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `deepseek-chat` | model name |

## Use

```bash
# Judge a single day (or a set of files)
lifelog judge 2026/2026-10.md

# Summarize one week
lifelog review 2026/ --week 10-05..10-11

# Write the result to a file instead of stdout
lifelog judge 2026/2026-10.md -o judge.md
```

Your logs are parsed by dated headings like `## 2026-10-10 (Sat)`.
`--week MM-DD..MM-DD` keeps only sections inside that range.

## Develop

```bash
uv pip install -e ".[dev]"
uv run pytest
```

## Roadmap

- v0.2 — give the agent *tools*: read several logs, compute 7-day averages, then judge
- v0.3 — configurable metrics schema (let people choose what to judge)

## License

MIT
