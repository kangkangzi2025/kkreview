# kkreview

A CLI tool that trains your code review skills using AI-generated challenges.

```
$ kkreview practice -l python -c security

╭──────────────────────────────────────────────────╮
│  CODE REVIEW CHALLENGE                           │
│  Language: python  |  Difficulty: medium          │
│                                                   │
│  A Flask endpoint that handles user file uploads  │
│  and stores metadata in a database.               │
╰──────────────────────────────────────────────────╯

   1 │ @app.route('/upload', methods=['POST'])
   2 │ def upload_file():
   3 │     filename = request.files['file'].filename
   4 │     path = os.path.join(UPLOAD_DIR, filename)
   ...

  Enter your review findings below.
  > Path traversal vulnerability on line 4 — filename is not sanitized
  > ...

╭──────────────────────────────────────────────────╮
│  RESULTS: 3/4 issues found  |  Score: 79%        │
╰──────────────────────────────────────────────────╯
```

## How it works

1. Claude generates realistic code with intentional bugs
2. You review the code and write down what you find
3. Claude evaluates your findings, scores them, and explains what you missed
4. Your progress is tracked so the tool focuses on your weak spots

## Install

```bash
pip install -e .
```

## Quick start

```bash
# First-time setup (choose 'cli' backend to use Claude Max subscription)
kkreview config init

# Start practicing
kkreview practice

# Fixed 5-round session on Python security
kkreview practice -l python -c security -n 5

# View your progress
kkreview stats
```

## Options

```
kkreview practice [OPTIONS]
  -l, --language    python/go/javascript/typescript/rust/c/cpp/java (default: random)
  -c, --category    security/performance/logic/quality/design/concurrency (default: random)
  -d, --difficulty  easy/medium/hard (default: medium)
  -n, --rounds      number of rounds, 0 = unlimited (default: 0)
```

## Backends

| Backend | Auth | Cost |
|---------|------|------|
| `cli` (default) | Claude Max subscription via Claude Code CLI | Included in subscription |
| `api` | Anthropic API key | Pay-per-use |

```bash
kkreview config set backend cli   # Use Claude Max subscription
kkreview config set backend api   # Use Anthropic API
```

## Categories

- **security** — SQL injection, XSS, path traversal, hardcoded secrets
- **performance** — N+1 queries, unnecessary copies, inefficient algorithms
- **logic** — off-by-one, race conditions, null handling, edge cases
- **quality** — DRY violations, poor naming, missing error handling
- **design** — tight coupling, wrong abstraction, SOLID violations
- **concurrency** — deadlocks, data races, improper synchronization

## Customize

```bash
kkreview config set theme monokai          # Dark syntax theme
kkreview config set theme github-light     # Light syntax theme
kkreview config set model opus             # Use a different model
```

## License

MIT
