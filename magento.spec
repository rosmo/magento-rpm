#
# Updated Magento RPM spec for el6+:
# - Add SELinux support
# - Expose only parts of Magento via DocumentRoot (symlinks)
# - More robust default Apache and PHP configuration (nginx can be used as well)
# - RHEL-locations for files
# - Added sample data under docdir
# - Added a patch to fix Magento's fondness of 0777 and 0666 permissions
# 
# (php module names are a bit different from RHEL built-ins)
#
# Magento seems to need following permssions in MySQL database: 
# - DROP, CREATE, ALTER, LOCK TABLES, DELETE, INSERT, SELECT, UPDATE, CREATE TEMPORARY TABLES
#
# Also with SELinux: 
# - setsebool -P httpd_can_network_connect_db=on
# - setsebool -P httpd_can_sendmail_on
# 
# To install via browser: ln -sf /usr/share/magento/install.php /var/www/html/magento/install.php
#
# Based on Silvan Calarco's spec file from Openmamba.
#
%define installdir %{_datadir}/magento
%define sampledata_version 1.9.0.0
Name:          magento
Version:       1.9.0.1
Release:       4.crasman
Summary:       An open-source eCommerce platform focused on flexibility and control
Group:         Applications/Web
Vendor:        Crasman
Packager:      Taneli Leppä <taneli@crasman.fi>, Silvan Calarco <silvan.calarco@mambasoft.it>
URL:           http://www.magentocommerce.com
Source:        http://www.magentocommerce.com/downloads/assets/%{version}/magento-%{version}.tar.bz2
Source1:       magento-crontab
Source2:       http://www.magentocommerce.com/downloads/assets/%{version}/magento-sample-data-%{sampledata_version}.tar.bz2
Patch0:        magento-1.3.2.1-cron_export_fix_lang.patch
Patch1:        magento-1.9-permissions.patch
License:       Open Software License
BuildRoot:     %{_tmppath}/%{name}-%{version}-root
BuildArch:     noarch
Requires:      php-mysql, php-mcrypt, php-imap, php-imagick, php-module
Requires:      httpd, mod_ssl
Requires(post): policycoreutils-python
Requires(postun): policycoreutils-python
Requires(pre): /usr/sbin/useradd

%description
An open-source eCommerce platform focused on flexibility and control.

%prep
%setup -n magento 
%setup -T -D -a 2 -n magento

%patch0 -p1
%patch1 -p1
rm -rf app/.svn

%build

%install
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"
install -d %{buildroot}%{installdir}

mkdir -p %{buildroot}%{_docdir}/magento-sample-data
mv magento-sample-data-%{sampledata_version}/* %{buildroot}%{_docdir}/magento-sample-data
rm -rf magento-sample-data-%{sampledata_version}/*

cp -a * %{buildroot}%{installdir}
rm -f %{buildroot}%{installdir}/*.html %{buildroot}%{installdir}/*.txt

install -d %{buildroot}%{_sysconfdir}/httpd/conf.d
cat > %{buildroot}%{_sysconfdir}/httpd/conf.d/%{name}.conf << EOF

<Directory "%{installdir}">
    Options None
    Order allow,deny
    Deny from all
</Directory>

<Directory "%{_var}/www/html/magento">
  Options FollowSymLinks
  RewriteEngine on

  # XSS protection
  RewriteCond %{REQUEST_METHOD} ^TRAC[EK]
  RewriteRule .* - [L,R=405]

  RewriteRule ^api/rest api.php?type=rest [QSA,L]

  RewriteCond %{REQUEST_URI} !^/(media|skin|js)/
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule .* index.php [L]
</Directory>

<Directory "%{_var}/www/html/magento/media">
  Options FollowSymLinks
  php_flag engine Off
</Directory>

<Directory "%{_var}/www/html/magento/skin">
  Options FollowSymLinks
  php_flag engine Off
</Directory>

<Directory "%{_var}/www/html/magento/js">
  Options FollowSymLinks
  php_flag engine Off
</Directory>

NameVirtualHost *:80
<VirtualHost *:80>
   ServerName localhost

   DocumentRoot %{_var}/www/html/magento
   ErrorLog %{_var}/log/httpd/%{name}-error_log
   CustomLog %{_var}/log/httpd/%{name}-access_log common
</VirtualHost>

<IfModule mod_ssl.c>
NameVirtualHost *:443
<Directory "%{_var}/www/secure_html/magento">
  Options FollowSymLinks
  RewriteEngine on

  # XSS protection
  RewriteCond %{REQUEST_METHOD} ^TRAC[EK]
  RewriteRule .* - [L,R=405]

  RewriteRule ^api/rest api.php?type=rest [QSA,L]

  RewriteCond %{REQUEST_URI} !^/(media|skin|js)/
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule .* index.php [L]
</Directory>

<Directory "%{_var}/www/secure_html/magento/media">
  Options FollowSymLinks
  php_flag engine Off
</Directory>

<Directory "%{_var}/www/secure_html/magento/skin">
  Options FollowSymLinks
  php_flag engine Off
</Directory>

<Directory "%{_var}/www/secure_html/magento/js">
  Options FollowSymLinks
  php_flag engine Off
</Directory>

<VirtualHost *:443>
  ServerName localhost

  DocumentRoot %{_var}/www/secure_html/magento
  ErrorLog %{_var}/log/httpd/%{name}-error_log
  CustomLog %{_var}/log/httpd/%{name}-access_log common

  SSLEngine on
  SSLHonorCipherOrder On
  SSLCipherSuite ECDHE-RSA-AES128-SHA256:AES128-GCM-SHA256:RC4:HIGH:!MD5:!aNULL:!EDH
  SSLProtocol all -SSLv2
  <IfVersion >= 2.4.4>
    SSLCompression off
  </IfVersion>
  <IfVersion < 2.4>
    <IfVersion >= 2.2.24>
      SSLCompression off
    </IfVersion>
  </IfVersion>
  SSLCertificateFile /etc/pki/tls/certs/magento.crt
  SSLCertificateKeyFile /etc/pki/tls/private/magento.key
  # SSLCertificateChainFile /etc/pki/tls/certs/chain.crt
  SetEnvIf User-Agent ".*MSIE [1-5].*" nokeepalive ssl-unclean-shutdown downgrade-1.0 force-response-1.0
  SetEnvIf User-Agent ".*MSIE [6-9].*" ssl-unclean-shutdown
</VirtualHost>

</IfModule>
EOF

mkdir -p %{buildroot}%{_sysconfdir}/cron.d/
install %{SOURCE1} %{buildroot}%{_sysconfdir}/cron.d/magento

mkdir -p %{buildroot}%{_sysconfdir}/php.d
cat > %{buildroot}%{_sysconfdir}/php.d/magento.ini << EOF
short_open_tag = Off
asp_tags = Off
output_buffering = 4096
expose_php = Off

max_execution_time = 60
memory_limit = 768M

error_reporting = E_ALL & ~E_DEPRECATED
display_errors = Off
log_errors = On
log_errors_max_len = 2048

safe_mode = Off
register_globals = Off
magic_quotes_gpc = Off
magic_quotes_runtime = Off
default_charset = "utf-8"
enable_dl = Off

arrow_url_fopen = Off
allow_url_include = Off

mysql.allow_local_infile = Off
mysqli.allow_local_infile = Off
EOF

mkdir -p %{buildroot}%{_var}/www/html/magento
mkdir -p %{buildroot}%{_var}/www/secure_html/magento
ln -sf %{installdir}/index.php %{buildroot}%{_var}/www/html/magento/index.php
ln -sf %{installdir}/index.php %{buildroot}%{_var}/www/secure_html/magento/index.php
ln -sf %{installdir}/get.php %{buildroot}%{_var}/www/html/magento/get.php
ln -sf %{installdir}/get.php %{buildroot}%{_var}/www/secure_html/magento/get.php
ln -sf %{installdir}/api.php %{buildroot}%{_var}/www/html/magento/api.php
ln -sf %{installdir}/api.php %{buildroot}%{_var}/www/secure_html/magento/api.php

ln -sf %{installdir}/media %{buildroot}%{_var}/www/html/magento/media
ln -sf %{installdir}/skin %{buildroot}%{_var}/www/html/magento/skin
ln -sf %{installdir}/js %{buildroot}%{_var}/www/html/magento/js

ln -sf %{installdir}/media %{buildroot}%{_var}/www/secure_html/magento/media
ln -sf %{installdir}/skin %{buildroot}%{_var}/www/secure_html/magento/skin
ln -sf %{installdir}/js %{buildroot}%{_var}/www/secure_html/magento/js

find %{buildroot}%{installdir} -name ".htaccess" -exec 'rm' '{}' ';'

perl -pi -e 's|getcwd\(\)|"%{installdir}"|' %{buildroot}%{installdir}/index.php

%clean
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"

%pre
/usr/sbin/useradd -M -d %{_datadir}/magento -s /usr/libexec/openssh/sftp-server -c "Magento developer" magedev >/dev/null 2>&1 || :

%post
semanage fcontext -a -t httpd_sys_content_t '%{installdir}(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{installdir}/media(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{installdir}/downloadable(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{installdir}/app/etc(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{installdir}/var(/.*)?' 2>/dev/null || :
restorecon -R %{installdir}/ || :

%postun
if [ $1 -eq 0 ] ; then
   semanage fcontext -d -t httpd_sys_content_t '%{installdir}(/.*)?' 2>/dev/null || :
   semanage fcontext -d -t httpd_sys_rw_content_t '%{installdir}/media(/.*)?' 2>/dev/null || :
   semanage fcontext -d -t httpd_sys_rw_content_t '%{installdir}/downloadable(/.*)?' 2>/dev/null || :
   semanage fcontext -d -t httpd_sys_rw_content_t '%{installdir}/app/etc(/.*)?' 2>/dev/null || :
   semanage fcontext -d -t httpd_sys_rw_content_t '%{installdir}/var(/.*)?' 2>/dev/null || :
fi

%files
%doc LICENSE.html LICENSE.txt LICENSE_AFL.txt RELEASE_NOTES.txt
%docdir %{_datadir}/doc/magento-sample-data
%{_datadir}/doc/magento-sample-data
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %{_sysconfdir}/php.d/magento.ini
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/cron.d/magento
%defattr(0640,root,apache,0750)
%{_var}/www/html/magento/*
%{_var}/www/secure_html/magento/*
%{installdir}/*.php
%{installdir}/errors
%{installdir}/app/code/community/*
%{installdir}/app/code/core/*
%{installdir}/app/design/install/*
%{installdir}/app/design/adminhtml/*
%attr(0660,root,apache) %config(noreplace) %{installdir}/app/etc/*
%attr(0770,root,apache) %dir %{installdir}/app/etc
%attr(0770,root,apache) %dir %{installdir}/app/etc/modules
%{installdir}/app/locale/*
%{installdir}/app/Mage.php
%{installdir}/downloader/*
%{installdir}/includes/config.php
%{installdir}/index.php.sample
%{installdir}/js/*
%{installdir}/lib/*
%{installdir}/mage/
%{installdir}/pkginfo/*
%{installdir}/shell/*.php
#%{installdir}/skin/*
%attr(0660,root,apache) %{installdir}/var/package/*
%attr(0770,magedev,apache) %dir %{installdir}/media
%attr(0770,root,apache) %dir %{installdir}/media/downloadable
%attr(0770,root,apache) %dir %{installdir}/var
%attr(0770,root,apache) %dir %{installdir}/var/package
%{installdir}/favicon.ico
%{installdir}/cron.sh
%{installdir}/php.ini.sample
%defattr(0660,root,apache,0770)
%{installdir}/media/*
%defattr(0640,magedev,apache,0750)
%dir %{installdir}/app/code/local/
%dir %{installdir}/app/design/frontend/
%{installdir}/app/design/frontend/*
%dir %{installdir}/skin
%{installdir}/skin/*
#%{installdir}/media/*
%defattr(0640,root,apache,0750)


%changelog
* Wed Aug  6 2014 Taneli Leppa <taneli@crasman.fi> - 1.9.0.1-4.crasman
- Add "magedev" user with SFTP shell, make certain theme directories writable by them (for theme installers, etc).

* Mon Aug  4 2014 Taneli Leppa <taneli@crasman.fi> - 1.9.0.1-1.crasman
- bump to upstream 1.9.0.1

* Mon Sep 30 2013 Taneli Leppä <taneli@crasman.fi> - 1.8.0.0-6.crasman
- bumped to upstream 1.8.0 and modify packaging

* Fri Mar 01 2013 Automatic Build System <autodist@mambasoft.it> 1.7.0.0-1mamba
- automatic version update by autodist

* Wed Jan 26 2011 Silvan Calarco <silvan.calarco@mambasoft.it> 1.4.1.1-2mamba
- added patch to always send order email even when payment is done through redirect (PayPal)

* Sun Aug 08 2010 Silvan Calarco <silvan.calarco@mambasoft.it> 1.4.1.1-1mamba
- update to 1.4.1.1

* Sun Aug 08 2010 Silvan Calarco <silvan.calarco@mambasoft.it> 1.4.1.0-2mamba
- added price_list patch

* Sat Jul 17 2010 Silvan Calarco <silvan.calarco@mambasoft.it> 1.4.1.0-1mamba
- update to 1.4.1.0

* Thu May 13 2010 Automatic Build System <autodist@mambasoft.it> 1.4.0.0-1mamba
- automatic update by autodist

* Thu Sep 24 2009 Silvan Calarco <silvan.calarco@mambasoft.it> 1.3.2.4-1mamba
- update to 1.3.2.4

* Fri Jul 24 2009 Silvan Calarco <silvan.calarco@mambasoft.it> 1.3.2.3-1mamba
- update to 1.3.2.3
- added patch for PHP 4.3

* Wed Jun 17 2009 Silvan Calarco <silvan.calarco@mambasoft.it> 1.3.2.1-1mamba
- update to 1.3.2.1

* Wed Jan 14 2009 Silvan Calarco <silvan.calarco@mambasoft.it> 1.1.8-1mamba
- update to 1.1.8

* Tue Sep 02 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 1.1.4-1mamba
- update to 1.1.4

* Tue Sep 02 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 1.1.3-1mamba
- update to 1.1.3

* Fri Jun 20 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 1.0.19870.4-1mamba
- update to 1.0.19870.4
- updated italian translation from www.magentocommerce.com/langs

* Tue May 06 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 1.0.19700-1mamba
- update to 1.0.19700

* Wed Apr 09 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 1.0-1mamba
- update to 1.0

* Sat Mar 29 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 0.9.17740-1mamba
- update to 0.9.17740

* Fri Mar 14 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 0.8.17240-1mamba
- update to 0.8.17240
- added italian translation from code.google.com/p/magento-it/source/checkout

* Fri Feb 08 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 0.7.15480-2mamba
- fixes for httpd.d file

* Wed Feb 06 2008 Silvan Calarco <silvan.calarco@mambasoft.it> 0.7.15480-1mamba
- package created by autospec
