# Storage

<img src="screenshot.png" width="616" height="344" alt="Screenshot">


## Start

```bash
docker run -d -p 8000:8000 -v $(pwd)/data:/data -e ALLOWED_HOST=localhost zenwalker/storage
```

## Cleanup

Remove files which not downloads for last year.

```
docker run --rm -it -v $(pwd)/data:/data zenwalker/storage cleanup --days=365
```
