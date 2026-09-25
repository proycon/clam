.PHONY: all
all:
	cargo build --release

plan.pdf: PLAN.md
	pandoc $< --pdf-engine=xelatex -o $@

.PHONY: test
test:
	@if ! command -v hurl > /dev/null; then echo "test dependency 'hurl' is not installed, please install it first..">&2; exit 1; fi
	@if ! command -v socat > /dev/null; then echo "test dependency 'socat' is not installed, please install it first..">&2; exit 1; fi
	-if [ -e .pid ]; then kill `cat .pid`; fi
	if [ -e .pid ]; then rm .pid; fi
	if [ -d tests/testservice/data ]; then rm -rf tests/testservice/data; fi
	mkdir -p tests/testservice/data
	cd tests/testservice && cargo run -- --debug --config test.toml &
	echo "(2s grace period for service to start)">&2 && sleep 2
ifeq ($(STOP_SERVICE),0)
	if hurl --test --verbose --jobs 1 tests/test.hurl; then exit 0; else exit 1; fi
	@echo "don't forget to stop the clam service yourself..."
else
	if hurl --test --verbose --jobs 1 tests/test.hurl; then killall clam; exit 0; else killall clam; exit 1; fi
endif
