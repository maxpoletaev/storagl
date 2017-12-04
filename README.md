# Storagl

Simple storage for screenshots and other shared files with short direct links.

<img src="screenshot.png" width="616" height="344" alt="Screenshot">

## Quick Start

```bash
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data zenwalker/storagl
```

## Cleanup

Remove files which does not have downloads for last year.

```bash
docker run --rm -it -v $(pwd)/data:/app/data zenwalker/storagl cleanup --days=365
```
