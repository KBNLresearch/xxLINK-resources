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

- 1 (file000003/local/www/root): xxLINK website + corporate sites as sub-sites. Note that links on front page uses some weird scripting, which doesn't work inb reconstructed version (also, scripts only print out URLS so don't understand how this originally worked).
- 2 (file000001/home/local/www)
- 3 (file000003/local/www/root)
- 4 (file000001/home/local/www)
- 5 (file000001/home/local/www)
- 6 (file000003/local/www/root)
- 12 (file000003/local/www)
- 14 (/file000001/home/local/www)
- 16 (file000003/local/www/root)
- 18? (file000002/html/www), doesn't look like production location.

NOTE: where is XXLINK home page located?!

## DLT tapes with website data

- 1 (file000001/www (with another www subfolder with even more sites!)
- 2 (file000001/www); Apache config files under apache.intel/conf.
- 4
- 6
- 7 (11 GB!)



## Rendering notes

### DDS-2

<http://nbbi.nl/home.htm>

Uses obsolete image map navigation.

<http://nl.fortis.com>

Returns 404 (no html in directory)

<http://mazda.nl/cgi-bin/dealer>

Returns 404. Source:

``` html
<A HREF=/cgi-bin/dealer><IMG SRC=323.jpg WIDTH=188 HEIGHT=100 BORDER=0><BR>Of vind nu al de kortste weg naar de Mazda dealer</A>
```

Looking at httpd.conf:

```
Exec    /cgi-bin/*	/home/local/www/mazda/cgi-bin/*
```

Note path is outside of "root" dir, i.e.:

```
Map /*.map  /htbin/htimage/home/local/www/mazda/root/
```

So perhaps */cgi-bin/* needs ScriptAlias:

<https://stackoverflow.com/questions/18903002/apache-scriptalias-cgi-bin-directory>


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