# The Haven Engine

Dynamic backend for The Haven. Designed for Render.

## Render deployment

Create a Render Web Service from this repository.

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Health: `/health`

### Persistent storage

Attach a Render Persistent Disk and mount it at:

`/var/data`

The included `render.yaml` uses `/var/data` as DATA_DIR.

This is where The Haven stores:
- chat memory JSON
- generated project JSON
- uploaded files
- generated ZIPs

Render's filesystem is ephemeral unless you attach a persistent disk.

## Important: GitHub is NOT unlimited storage

Do not store chat history, videos, pictures, and arbitrary uploads in a Git repository. GitHub has repository/file limits. GitHub should be the source-control and optional backup layer.

For large production media, add an object-storage adapter later. For shared relational memory, add Postgres later.

## No AI

This engine does not call OpenAI, Anthropic, Gemini, Claude, or another AI model.

The "knowledge" layer is deterministic. Expand it with:
- language specifications
- project templates
- AST/parser adapters
- validators
- compiler adapters
- test runners
- dependency manifests
- documentation indexes

## Security

Do not put GitHub tokens in the browser. If GitHub backup is added, tokens belong only in Render environment variables or, preferably, a GitHub App with minimum permissions.

Uploaded files should eventually receive quotas, authentication, content-type checks, malware scanning, and per-user namespaces before public deployment.
