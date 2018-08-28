# Battmon Makefile
#

# Must be executed by root
#

INSTALLDIR='/usr/bin/'

install:
	cp battmon/battmon.py $(INSTALLDIR)/battmon
	sh build_files/battmon.postinst

uninstall:
	sh build_files/battmon.prerm
	rm $(INSTALLDIR)/battmon
