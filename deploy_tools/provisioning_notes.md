Provisioning a new site
-----------------------

## Required packages:

* nginx
* Python 3
* Git
* pip
* virtualenv
* ImageMagick
* Supervisor

## Nginx Virtual Host config

* see nginx.template.conf
* replace SITENAME
* replace HOSTNAME
* replace SITE_FOLDER

## Start job

# See gunicorn.template.conf
* replace USER
* replace SITENAME
* replace SITE_FOLDER
* replace PROJECT_ROOT
# See supervisor.template.conf
* replace SITENAME
* replace SITE_FOLDER


## Using Fabric to provision
* use fab enviroment provision

## Using Fabric to deploy
* use fab enviroment deploy

## Folder structure
Assume we have a user account at /home/username

/home/username/sites/
└── SITENAME
   ├── src
   ├── static
   ├── media
   ├── tmp
   ├── bin
