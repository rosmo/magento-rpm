RPM spec file for Magento 1.9 in Red Hat Enterprise Linux 6 / CentOS 6 / compatible distro.

Updated Magento RPM spec for el6+:
- Add SELinux support
- Expose only parts of Magento via DocumentRoot (symlinks)
- More robust default Apache and PHP configuration (nginx can be used as well)
- RHEL-locations for files
- Added sample data under docdir
- Added a patch to fix Magento's fondness of 0777 and 0666 permissions

(php module names are a bit different from RHEL built-ins)

Magento seems to need following permssions in MySQL database: 
- DROP, CREATE, ALTER, LOCK TABLES, DELETE, INSERT, SELECT, UPDATE, CREATE TEMPORARY TABLES

Also with SELinux: 
- setsebool -P httpd_can_network_connect_db=on
- setsebool -P httpd_can_sendmail_on

To install via browser: ln -sf /usr/share/magento/install.php /var/www/html/magento/install.php

Based on Silvan Calarco's spec file from Openmamba.


