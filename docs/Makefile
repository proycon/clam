.PHONY: all
all: docs html-docs

.PHONY: docs
docs: clam.1 clam.5

.PHONY: html-docs
html-docs: clam.1.html clam.5.html

.PHONY: site
site: html-docs index.html

%: %.scd
	scdoc < $< > $@

index.html: ../README.md site_templates/header.html site_templates/footer.html
	cat site_templates/header.html >$@
	pandoc -f markdown -t html $< >>$@
	cat site_templates/footer.html >>$@

clean:
	rm -f clam.1 clam.5 clam.1.html clam.5.html index.html

# We convert from SCDOC to HTML, after the HTML conversion
# we apply some postprocessing for better internal hyperlinks and styling.
%.html: %.scd
	scd2html < $< | \
		sed -E -e 's/Georgia/Sans/g' \
			-e 's/Menlo/FiraMono Nerd Font, Menlo, Mono/g' \
		    -e 's/font-size: 20px;/font-size: 1em;/g' \
			-e 's/section <u>([A-Z ]+)<\/u>/section <a href="#\1">\1<\/a>/g' \
			-e 's/Section <u>([A-Z ]+)<\/u>/Section <a href="#\1">\1<\/a>/g' \
			-e 's/see <u>([A-Z ]+)<\/u>/see <a href="#\1">\1<\/a>/g' \
			-e 's/See <u>([A-Z ]+)<\/u>/See <a href="#\1">\1<\/a>/g' \
			-e 's/<li><u>([A-Z ]+)<\/u>/<li><a href="#\1">\1<\/a>/g' \
			-e 's/<b>clam<\/b>\(([1-9])\)/<a href="clam.\1.html"><b>clam<\/b><\/a>(\1)/g' | \
		sed -e ':loop' \
    		-e 's/\(href="[^" ]*\) \([^"]*"\)/\1_\2/' \
        	-e 't loop' > "$@" #this last sed statement replace spaces in href attributes with underscores


