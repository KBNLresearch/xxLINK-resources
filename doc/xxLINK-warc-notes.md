# xxLINK WARC capture and rendering notes

These notes describe the capture process of the restored xxLINK sites to WARC, and how these WARCs can be played back.

## Preparation: activate required server configuration

### Multi-site dumps)

Assuming we have multiple Apache server configurations set up (typically one for each tape, as described in the [Apache Notes](./xxLINK-apache-notes.md)):

1. Open tape-specific and system-wide hosts files in text editor as sudo, e.g.:

    ```
    sudo xed /etc/hosts /var/www/xxLINK-DDS-2/etc/hosts
    ```

    Then manually copy entries from tape-specific (`/var/www/xxLINK-DDS-2/etc/hosts`) file to system wide (`/etc/hosts`) file, and save the updated file.

2. Deactivate any currently active Apache configurations, and activate the new one, e.g.:

```
sudo a2dissite *
sudo a2ensite xxLINK-DDS-2
sudo systemctl restart apache2
```

### xxLINK portfolio site dumps

The only contain the xxlink.nl site, so the above procedure is repaced by the simpler:

1. Open system-wide hosts file as sudo:

    ```
    sudo xed /etc/hosts
    ```

    Add these two lines (if they're not there already):

    ```
    127.0.0.1 xxlink.nl
    127.0.0.1 www.xxlink.nl
    ```
    Then save the updated file.

2. Deactivate any currently active Apache configurations, and activate the new one, e.g.:

```
sudo a2dissite *
sudo a2ensite xxLINK-DDS-1
sudo systemctl restart apache2
```
    

## Capture local sites to compressed warc files

We'll be using the Python script [scrape-local.py](./scripts/scrape-local.py), which requires [warcio](https://github.com/webrecorder/warcio).

1. Start a terminal, and go to (or create) an empty directory. 

2. Run the script, using the active Apache config file as the input argument:

```
python3 scrape-local.py /etc/apache2/sites-available/xxLINK-DDS-2.conf
```

The script iterates over all *VirtualHost* entries in the config file, and create the following output files for each entry:

1. A compressed warc file (.warc.gz extension; base name is derived from *ServerName* value in config file). Example: *cameranet.nl.warc.gz*.

2. A list of all internal URLs (.csv extension; base name is derived from *ServerName* value in config file). Example: *cameranet.nl.csv*.

In addition it also creates a file *sites.csv* with the *ServerName* values of all sites extracted from the Apache config file.

## Render warc

Install pywb:

```
python3 -m install --user pywb
```

(BTW installation process reports `Segmentation fault (core dumped)` at end of install, but after this everything seems to work fine.)

Create web archives directory and then enter it:

```
mkdir web-archives
cd web-archives
```

Create new archive (in this case we'll create an archive specifically for the contents of one tape):

```
wb-manager init DDS-2
```

Add all generated warc files from the capture step to the archive (note how the wildcard adds all warc files with one single command):

```
wb-manager add DDS-2 ~/test/*.warc.gz
```

Start pywb:

```
wayback
```

Archive now accessible from browser at below link:

<http://localhost:8080/DDS-2/>

Use the domains listed in the *sites.csv* file to locate specific sites (currently pywb doesn't offer any option to browse the archive).

