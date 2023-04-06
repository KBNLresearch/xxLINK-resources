# Restoration of xxLINK sites

Extract TARs:

```
sudo tar -xvzf tapes-DDS-extracted.tar.gz > /dev/null
```

Note: extracting as regular user will result in permission-related errors for some directories, so better to extract as sudo. Some of the resulting folders/files will be inaccessible because of owners/permissions, but we'll fix that while copying them over to /var/www below. 

## Interesting data

- dir `/home/www.xxlink.nl` contains logs (1994/95)
- dir `/home/local/www` contains 26 folders that each hold a web site!
- dir `/home/local/etc` contains [httpd configuration file](https://httpd.apache.org/docs/2.4/configuring.html) `httpd.conf` which defines the configuration for all sites.

Note that this is a a config file for the [CERN httpd](https://en.wikipedia.org/wiki/CERN_httpd) server software; docs available [here](https://www.w3.org/Daemon/User/Config/Overview.html).


## Copy one site to var/www

```
sudo rsync -avhl ~/kb/xxLINK/tapes-DDS/2/file000001/home/local/www/schiphol /var/www/
sudo find /var/www/schiphol -type d -exec chmod 755 {} \;
sudo find /var/www/schiphol -type f -exec chmod 644 {} \;
sudo find /var/www/schiphol/cgi-bin -type f -exec chmod 755 {} \;
```

## Python script for config reading/writing copying

[Here](../scripts/restore-sites.py).

Example:

```
sudo python3 ~/kb/xxLINK-resources/scripts/restore-sites.py /home/johan/kb/xxLINK/tapes-DDS/2/file000001 /var/www/xxLINK-DDS-2
```

Output:

- Folder *www* with sites data (including updated symbolic links, wherever possible)
- Folder *etc* with auto-generated Apache config file and file with *hosts* entries
- Additional files/folders that are referenced by symbolic links


## Additional manual configuration

1. Copy auto-generated Apache config file to Apache *sites-available* folder:

```
sudo cp /var/www/xxLINK-DDS-2/etc/sites.conf /etc/apache2/sites-available/xxLINK-DDS-2.conf
```

2. Copy contents of *etc/hosts* file (in output folder) into system */etc/hosts* file.

3. Activate the new Apache configuration:

```
sudo a2ensite xxLINK-DDS-2.conf
```

4. Restart Apache:

```
sudo systemctl reload apache2
```

All done!


## DDS tapes with website data

- 1 (file000003/local/www/root)
- 2 (file000001/home/local/www)
- 3 (file000003/local/www/root)
- 4 (file000001/home/local/www)
- 5 (file000001/home/local/www)
- 6 (file000003/local/www/root)
- 12 (file000003/local/www)
- 14 (file000001/home/local/www)
- 15 (file000003/local/WWW/doc_root)
- 16 (file000003/local/www/root)
- 17? (file000002/html/www), doesn't look like production location.
- 18? (file000002/html/www), doesn't look like production location.

### Setup of xxLINK portfolio site

Copy files + set permissions:

```
sudo rsync -avhl ~/kb/xxLINK/tapes-DDS/3/file000003/local/www/root/ /var/www/xxLINK-DDS-3
sudo find /var/www/xxLINK-DDS-3 -type d -exec chmod 755 {} \;
sudo find /var/www/xxLINK-DDS-3 -type f -exec chmod 644 {} \;
```

Apache config - in this case we copy existing file from tape 1 to a new file:

```
sudo cp /etc/apache2/sites-available/xxLINK-DDS-1.conf /etc/apache2/sites-available/xxLINK-DDS-3.conf
```

Then edit DocumentRoot:

```
sudo nano /etc/apache2/sites-available/xxLINK-DDS-3.conf
```

Result:

```
<VirtualHost *:80>
ServerName xxlink.nl
ServerAlias www.xxlink.nl
DocumentRoot /var/www/xxLINK-DDS-3
RedirectMatch ^/$ "/home.htm"
RedirectMatch ^(.*)/$ $1/home.htm
</VirtualHost>
```

Deactivate existing config, activate new one:

```
sudo a2dissite xxLINK-DDS-1
sudo a2ensite xxLINK-DDS-3
sudo systemctl restart apache2

```

Capture to WARC (run from WARC output dir):

```
python3 ~/kb/xxLINK-resources/scripts/scrape-local.py /etc/apache2/sites-enabled/xxLINK-DDS-3.conf xxLINK-DDS-3.warc.gz xxLINK-DDS-3-urls.csv

```

Create new collection in pywayback and import WARC:

```
wb-manager init DDS-3
wb-manager add DDS-3 ~/kb/xxLINK/warc/DDS/3/xxLINK-DDS-3.warc.gz
```

### Setup of multi-site dumps

Run script to copy data, set permissions:

```
sudo python3 ~/kb/xxLINK-resources/scripts/restore-sites.py /home/johan/kb/xxLINK/tapes-DDS/4/file000001 /var/www/xxLINK-DDS-4
```

Copy generated Apache config file:

```
sudo cp /var/www/xxLINK-DDS-4/etc/sites.conf /etc/apache2/sites-available/xxLINK-DDS-4.conf
```

Manually add entries from `/var/www/xxLINK-DDS-4/etc/hosts` to `/etc/hosts` file.

```
sudo xed /etc/hosts /var/www/xxLINK-DDS-4/etc/hosts
```

Deactivate existing config, activate new one:

```
sudo a2dissite xxLINK-DDS-16
sudo a2ensite xxLINK-DDS-4
sudo systemctl restart apache2
```

Capture to WARC (run from WARC output dir):

```
python3 ~/kb/xxLINK-resources/scripts/scrape-local.py /etc/apache2/sites-enabled/xxLINK-DDS-4.conf xxLINK-DDS-4.warc.gz xxLINK-DDS-4-urls.csv

```

Create new collection in pywayback and import WARC:

```
wb-manager init DDS-4
wb-manager add DDS-4 ~/kb/xxLINK/warc/DDS/4/xxLINK-DDS-4.warc.gz
```


## DLT tapes with website data

- 1 (file000001/www (with another www subfolder with what looks like the xxlink portfolio site.
- 2 (file000001/www); Apache config files under apache.intel/conf.
- 4
- 6
- 7 (11 GB!)
- 12
- 14

## DLT tapes config

### Tape 1

Directory:

```
/media/johan/xxLINK/xxLINK-DLT/tapes-DLT/1/file000001/apache.intel/conf/configdb
```

Apache config file for each site. BUT:

- Some config files don't contain DocumentRoot entry, which is imported through INCLUDE. Applies to hospitalitynet. Hard-coded fix in script.

- File www/sbi/adfo/root/beeld/rtv/9646: broken symlink.

- Dir www/hospitorg/root/davey symlink to dir 'davey' in parent dir (www/hospitorg/davey)

- Dir www/hospitorg/root/vlist: symlink to ../../hospitalitynet/root/vlist.


### Tape 2

```
/media/johan/xxLINK/xxLINK-DLT/tapes-DLT/2/file000001/apache.intel/conf/httpd.conf.isobel
```

Apache config file w. VirtualHost entries. BUT only 34 entries vs 250 folders in www. Also ServerName values do not always reflect true domains where sites were hosted, e.g. `libris.xxLINK.nl`.

<!--
So let's search the entir tape for "schiphol.nl" (which is not included in the config file):

```
grep -r "schiphol.nl" /media/johan/xxLINK/xxLINK-DLT/tapes-DLT/2/file000001 > schiphol.txt
```
-->

### Tape 4

Directory:

```
/media/johan/xxLINK/xxLINK-DLT/tapes-DLT/4/file000001/apache.intel/conf/configdb
```

- 478 files, each for 1 site

- 375 folders in www


## Rendering notes

### DDS-1

xxLINK website + corporate sites as sub-sites (but not under original URLs, looks like portfolio site).

- Links on front page uses some weird scripting, which doesn't work inb reconstructed version (also, scripts only print out URLS so don't understand how this originally worked).

- Some referenced resources are missing from source data (notably the 'nbt' directory)


### DDS-2

<http://nbbi.nl/home.htm>

Uses obsolete image map navigation.

<http://nl.fortis.com>

Returns 404 (no html in directory)


### DDS-3

As DDS-1.

### DDS-4

Links that are supposed to point to xxLINK domain (which is not included in this dump) instead link to individual corporate domains. Example: page <http://localhost:8080/DDS-4/20201023153432/http://www.schiphol.nl/1/cantake.htm> links to <http://localhost:8080/DDS-4/20201023153432mp_/http://www.schiphol.nl/1/about.htm>. Looks like a config problem. In source:

```html
HTML-conversie: <A HREF=/1/about.htm>xxLINK</A> Internet Services
```

Many sites on this tape appear to be really early versions with hardly any content at all.

### DDS-6

As DDS-1.

### DDS-12

- <http://localhost:8080/DDS-12/20201023162532/http://www.cameranet.nl/ads>: doesn't load

- <http://www.cameranet.nl/ads/com/com.htm>: search results in no matches, but is included in URL list.

### DDS-14

REALLY early version, some sites are merely stubs without even an index page.

### DDS-15

As DDS-1.

### DDS-16

As DDS-1. Contrary to info on tape label ("www 31 jan '95 DUMP") most recent files date from January 1996, so this is probably a labeling errror.


## Scripts

Many dependencies on non-standard/obsolete versions of interpreters, refs to locally installed applications/tools/custom software. Some examples:

### Cameranet

Mail form:

```
#!/usr/local/bin/ksh

eval $(/home/local/www/cgi-bin/cgiparse -init)
eval $(/home/local/www/cgi-bin/cgiparse -form)

print "Location: http://www.cameranet.nl/ads/adv.htm"
print ""

FILENAME="/tmp/sads$$.tmp"    

::
::

/usr/ucb/mail -s "Camera Magazine advertentie" redacted@redacted.nl redacted@redacted.nl <$FILENAME

rm $FILENAME
```


## Solaris 1.2 install in qemu

Create machine image:

```
qemu-img create -f qcow2 solaris112.qcow2 2G

```

Boot:

```
qemu-system-sparc -M SS-5 -m 128 -drive file=solaris112.qcow2,bus=0,unit=0,media=disk -drive file=Solaris1_1_2.iso,bus=0,unit=2,media=cdrom,readonly=on
```

Fails with:

```
qemu: could not load prom 'openbios-sparc32'
```



## Resources

- [Server-side Preservation of Dynamic Websites](https://publications.beeldengeluid.nl/pub/633/) (mentions ReproZip, need to look at this)

- [Archaeology of the Amsterdam digital city; why digital data are dynamic and should be treated accordingly](https://www.tandfonline.com/doi/full/10.1080/24701475.2017.1309852)

- [Playing with SunOS 4.1.4 SPARC on QEmu](http://defcon.no/sysadm/playing-with-sunos-4-1-4-on-qemu/) (but based on outdated qemu version!)

- [Build your own SPARC workstation with QEMU and Solaris](https://learn.adafruit.com/build-your-own-sparc-with-qemu-and-solaris?view=all)