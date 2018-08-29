# Battmon Makefile
# Umesh Padia
# All commands should be executed by root 

INSTALLDIR='/usr/bin/'
install:

	cp battmon/battmon.py $(INSTALLDIR)/battmon
	sh build_files/battmon.postinst

uninstall:

	sh build_files/battmon.prerm
	rm $(INSTALLDIR)/battmon

publish: deb submit clean
debclean: deb clean

deb: 

	DIR=$( dirname $0 )
	cd $(DIR)
	cp build_files/* . 
	mkdir debian
	mv battmon.p* debian/
	python3 setup.py --command-packages=stdeb.command  sdist_dsc \
	 --package3 battmon --copyright-file COPYRIGHT bdist_deb 

submit: 

	debsign deb_dist/*source.changes
	dput ppa:padiauj/battmon deb_dist/*source.changes

clean:

	cd $(DIR)
	rm -rf tmp deb_dist dist battmon.egg-info battmon*.tar.gz debian padiauj-battmon.desktop \
	 MANIFEST.in stdeb.cfg
