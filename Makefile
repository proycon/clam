.PHONY: all
all:
	cargo build --release

plan.pdf: PLAN.md
	pandoc $< --pdf-engine=xelatex -o $@

.PHONY: test
test:
	-if [ -e .pid ]; then kill `cat .pid`; fi
	if [ -e .pid ]; then rm .pid; fi
	if [ -d tests/testservice/data ]; then rm -rf tests/testservice/data; fi
	mkdir -p tests/testservice/data
	cd tests/testservice && cargo run -- --config test.toml &
	echo "(2s grace period for service to start)">&2 && sleep 2
	hurl --test --verbose --jobs 1 tests/test.hurl
	killall -w clam #wait for clam to die (this presumes you have no other clam services running besides this test)
