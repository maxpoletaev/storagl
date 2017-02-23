DIR = $(shell pwd)

build:
	docker build -t zenwalker/storagl .

develop:
	docker run --rm -it -p 8000:8000 -e DJANGO_DEBUG=1 \
	-v $(DIR):/app zenwalker/storagl runserver 0.0.0.0:8000

.PHONY: build develop
