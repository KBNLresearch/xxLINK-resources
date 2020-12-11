# xxLINK WARC capture and rendering notes

These describe the capture process of the restored xxLINK sites to WARC, and how these WARCs can be played back.

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
 
