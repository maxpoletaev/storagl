DIR = $(shell pwd)

build:
	docker build -t zenwalker/storage .

develop:
	docker run --rm -it -p 8000:8000 -e DJANGO_DEBUG=1 -v $(DIR)/data:/data \
	-v $(DIR)/storage:/storage zenwalker/storage runserver 0.0.0.0:8000
