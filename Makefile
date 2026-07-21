.PHONY: all
all:
	cargo build --release

plan.pdf: PLAN.md
	pandoc $< --pdf-engine=xelatex -o $@

.PHONY: test
test:
	-if [ -e .pid ]; then kill `cat .pid`; fi
	if [ -e .pid ]; then rm .pid; fi
	cargo run -- --config tests/testservice/test.toml & echo $$! > .pid
	echo "(2s grace period for service to start)">&2 && sleep 2
	hurl --test --verbose --jobs 1 tests/test.hurl
	kill `cat .pid` && rm .pid
