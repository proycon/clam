.PHONY: all
all:
	cargo build --release

plan.pdf: PLAN.md
	pandoc $< --pdf-engine=xelatex -o $@
