# Storagl

Simple storage for screenshots and other files with short direct links.

<img src="screenshot.png" width="616" height="344" alt="Screenshot">

## Quick Start

``` sh
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data zenwalker/storagl
```

## Using curl to upload files to storagl

``` sh
curl http://static.example.com -F "file=@archive.zip"
```

## Cleanup

Remove files which haven’t been downloaded for the last year.

``` sh
docker run --rm -it -v $(pwd)/data:/app/data zenwalker/storagl cleanup --days=365
```
