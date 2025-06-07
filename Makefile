.PHONY: install
install:
	sudo emerge -av dev-vcs/git dev-python/urllib3 dev-python/python-gnupg
	sudo ./setup.py install

.PHONY: build-tester
build-tester:
	docker build -t sqfssync-tester .

.PHONY: test
test: build-tester
	docker run --privileged --rm -it -v "$(shell pwd):/sqfssync" sqfssync-tester
