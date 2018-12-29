ORG := raise
PACKAGE := deploy
TARGET_OS := linux

.PHONY: install images run

default: run

install:
	sudo pip install -e .

images:
	packer build templates/packer.json
	packer build templates/packer-v2.json

run: images
