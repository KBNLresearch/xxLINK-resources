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
sudo python3 ~/kb/xxLINK-resources/scripts/restore-sites.py \ 
    /home/johan/kb/xxLINK/tapes-DDS/2/file000001/home/local/www \
    /home/johan/kb/xxLINK/siteData-DDS/2/www \
    /home/johan/kb/xxLINK/tapes-DDS/2/file000001/home/local/etc/httpd.conf \
    /home/johan/kb/xxLINK/siteData-DDS/2/etc/sites.conf
```

## Configure

```
sudo cp /etc/apache2/sites-available/ziklies.conf /etc/apache2/sites-available/schiphol.conf
```

Edit as follows:


```
ServerName schiphol.nl:80
ServerAdmin webmaster@localhost
ServerName schiphol.nl
ServerAlias www.schiphol.nl
DocumentRoot /var/www/schiphol/root
# Below line redirects DocumentRoot to home.htm
RedirectMatch ^/$ "/home.htm"

```

Add site domain to hosts file /etc/hosts (mind the TAB character!):

127.0.0.1	schiphol.nl

## Activate configuration

```
sudo a2dissite kbresearch.conf
sudo a2ensite schiphol.conf
```

## Restart server

```
sudo systemctl restart apache2
```

## Try hosting from different folder

```
DocumentRoot /home/johan/kb/xxLINK/sites/schiphol/root
```

Results in 403 Forbidden. Probably possible to change through config, but don't want to go there (also bvc of possible security concerns), so instead added /var/www folder to daily backup schedule.

## Firefox

<https://stackoverflow.com/questions/50183899/firefox-cant-connect-to-a-local-site-but-chrome-can>


browser.fixup.dns_first_for_single_words set to True

## Resources

- [Server-side Preservation of Dynamic Websites](https://publications.beeldengeluid.nl/pub/633/) (mentions ReproZip, need to look at this)

- [Archaeology of the Amsterdam digital city; why digital data are dynamic and should be treated accordingly](https://www.tandfonline.com/doi/full/10.1080/24701475.2017.1309852)