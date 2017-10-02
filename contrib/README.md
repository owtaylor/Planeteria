The files in this directory are the configuration files for a deployment
of Planeteria using a hybrid model where a Docker container is used for
dynamic content (`admin.py`) and httpd acts as a frontend and serves up
the static content.

SELinux
-------
Because the files in `/srv/planeteria/www` need to be written to by the
container (when the planets are rebuilt), but also need to be read by
Apache, the standard docker+SELinux model where containers can only write
files labeled as `svirt_sandbox_file_t` doesn't work, since Apache
httpd also needs to read those files. To avoid having to establish custom
SELinux policy, the docker container is run without SELinux confinement.
(`--security-opt="label=disable"`)

Hopefully, running as an unprivileged user with a limited view of the host
filesystem already provides a sufficient level of security.

Container image rebuilds
------------------------
The policy here is that, every 15 minutes, before we rebuild the planets,
we check:

* Was the image built with the current git revision?
* Was the image built within the last 7 days

If the answer to either is "no", we rebuild the image from scratch and
restart the service.

Deployment
----------

``` bash
groupadd -r planeteria
useradd -r planeteria -g planeteria

semanage fcontext -t httpd_sys_context_t '/srv/planeteria/static(/.*)?'
semanage fcontext -t httpd_sys_context_t '/srv/planeteria/templates/([^/]*)/pub.d(/.*)?'
semanage fcontext -t httpd_sys_context_t '/srv/planeteria-data/www(/.*)?'

git clone git@github.com:owtaylor/Planeteria.git /srv/planeteria

mkdir -p /srv/planeteria-data/{www,logs}
chown -R planeteria:planeteria /srv/planeteria-data

cp start-planeteria.sh update-planeteria.sh /usr/local/bin

cp planeteria.service planeteria-update.{service,timer} /etc/systemd/system
systemctl enable planeteria.service planeteria-update.timer
systemctl start planeteria.service planeteria-update.timer

cp planeteria.conf /etc/httpd/conf.d
systemctl restart httpd
```

Note that the config file and scripts in this `/contrib` directory should only be
manually updated after checking what has changed, since they run as root and
are not sandboxed.

