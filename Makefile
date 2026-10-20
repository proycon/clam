PREFIX := /usr

.PHONY: all
all: check-dependencies docs
	cargo build --release

.PHONY: install
install: check-dependencies docs
	cargo install --root $(PREFIX)
	mkdir -p $(PREFIX)/share/man/man1 $(PREFIX)/share/man/man5
	cp docs/*.1 $(PREFIX)/share/man/man1
	cp docs/*.5 $(PREFIX)/share/man/man5

.PHONY: check-dependencies deps
check-dependencies deps:
	@if ! command -v cargo > /dev/null; then echo "Error: dependency 'cargo' is not installed, please install it first.. It is needed to manage Rust dependencies">&2; exit 1; fi
	@if ! command -v rustc > /dev/null; then echo "Error: dependency 'rustc' is not installed, please install it first.. It is needed to compile Rust code">&2; fi
	@if ! command -v scdoc > /dev/null; then echo "Error: dependency 'scdoc' is not installed, please install it first.. It is needed to generate documentation">&2; fi

.PHONY: test-deps
test-deps:
	@if ! command -v hurl > /dev/null; then echo "test dependency 'hurl' is not installed, please install it first..">&2; exit 1; fi
	@if ! command -v socat > /dev/null; then echo "test dependency 'socat' is not installed, please install it first..">&2; exit 1; fi
	@if ! command -v socat > /dev/null; then echo "test dependency 'dex' is not installed, you need it only if you want to run authentication tests..">&2; exit 1; fi

.PHONY: test
test: test-deps
	-if [ -e .pid ]; then kill `cat .pid`; fi
	if [ -e .pid ]; then rm .pid; fi
	if [ -d tests/testservice/data ]; then rm -rf tests/testservice/data; fi
	mkdir -p tests/testservice/data
	cd tests/testservice && cargo run -- --debug --config test.toml &
	echo "(2s grace period for service to start)">&2 && sleep 2
ifeq ($(STOP_SERVICE),0)
	if hurl --test --very-verbose --jobs 1 tests/test.hurl; then exit 0; else exit 1; fi
	@echo "don't forget to stop the clam service yourself..."
else
	if hurl --test --very-verbose --jobs 1 tests/test.hurl; then killall clam; exit 0; else killall clam; exit 1; fi
endif

.PHONY: testauth
testauth: test-deps
	dex serve tests/testauthservice/dex.yaml &
	echo "(2s grace period for dex to start)">&2 && sleep 2
	cd tests/testauthservice && cargo run -- --debug --config test.toml &
	echo "(2s grace period for service to start)">&2 && sleep 2
ifeq ($(STOP_SERVICE),0)
	if hurl --test --very-verbose --jobs 1 tests/testauth.hurl; then exit 0; else exit 1; fi
	@echo "don't forget to stop the clam and dex services yourself..."
else
	if hurl --test --very-verbose --jobs 1 tests/testauth.hurl; then killall clam dex; exit 0; else killall clam dex; exit 1; fi
endif

.PHONY: docs
docs:
	cd docs && $(MAKE) clam.1 clam.5

plan.pdf: PLAN.md
	pandoc $< --pdf-engine=xelatex -o $@



