Summary: Boss Python SkyNET
Name: python-boss-skynet
Version: 0.6.3
Release: 1
Source0: %{name}-%{version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
Obsoletes: boss-skynet < 0.6.0
Provides: boss-skynet
BuildRequires: python, python-distribute, supervisor
Requires: python, python-ruote-amqp >= 2.1.0, python-amqplib, supervisor, python-setproctitle
Requires(post): pwdutils
BuildArch: noarch
Vendor: David Greaves <david@dgreaves.com>
Url: http://github.com/MeeGoIntegration/boss-python-skynet/

%description
UNKNOWN

%prep
%setup -n %{name}-%{version} -n %{name}-%{version}

%build
make

%install
make PREFIX=%{_prefix} DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/var/log/supervisor

%clean
rm -rf $RPM_BUILD_ROOT

%pre
    # the only crazy way for rpm
    if [ "$(head -n 1 /usr/bin/skynet)" == '#!/bin/bash' ]; then
      # Upgrade from daemontools based version
      SERVICE_DIR=/var/lib/SkyNET/services/
      STORAGE_DIR=/var/lib/SkyNET/store/
      [ -f /etc/sysconfig/boss-skynet ] && . /etc/sysconfig/boss-skynet
      echo "stopping daemontools controlled participants ... this may take a while ..."
      for PART in $(find ${SERVICE_DIR} -type l); do
        rm $PART
        svc -dx ${STORAGE_DIR}/$(basename $PART)
        sleep 2
        svc -dx ${STORAGE_DIR}/$(basename $PART)/log
      done
    fi



%post

chkconfig supervisord on || true
service supervisord start || true

if [ $1 -eq 1 ]; then
    if ! grep "skynet" /etc/passwd; then
      /usr/sbin/useradd --system skynet
    fi

else
    if [ "$(head -n 1 /usr/bin/skynet)" == '#!/bin/bash' ]; then
        # Upgrade from daemontools based version to supervisor based version

        for PART in $(find /var/lib/SkyNET/store -maxdepth 2 -name config.exo); do
            code=$(awk -F "=" '/^code/ {print $2}' ${PART})
            name=$(awk -F "=" '/^name/ {print $2}' ${PART})
            queue=$(awk -F "=" '/^queue/ {print $2}' ${PART})
            runas=$(awk -F "=" '/^runas/ {print $2}' ${PART})
            regexp=$(awk -F "=" '/^regexp/ {print $2}' ${PART})
            if ! grep -R -q $code /etc/supervisor/conf.d/ ; then
                skynet install -u $runas -r $regexp -q $queue -n $name $code
            fi
            sed -i -e '/user_managed/d' /etc/supervisor/conf.d/*
        done

    else
        # Upgrade from supervisord based version

        skynet rebuild --all || true
        skynet apply || true
    fi
fi

%files
%defattr(-,root,root)
%{python_sitelib}/SkyNET
%{python_sitelib}/*egg-info
%{_datadir}/doc/%{name}
%{_bindir}/skynet
%{_bindir}/skynet_exo
%config(noreplace) %{_sysconfdir}/skynet/skynet.conf
%config(noreplace) %{_sysconfdir}/skynet/skynet.env
%{_sysconfdir}/skynet
%dir /var/log/supervisor
