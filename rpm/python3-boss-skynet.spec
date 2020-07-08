Summary: Boss Python SkyNET
Name: python3-boss-skynet
Version: 0.7.0
Release: 1
Source0: %{name}-%{version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
Obsoletes: boss-skynet < 0.6.0
Provides: boss-skynet
BuildRequires: python3, supervisor >= 4.0.0
Requires: python3
Requires: python3-ruote-amqp
Requires: python3-pika
Requires: supervisor >= 4.0.0
Requires: python3-setproctitle
Requires(post): pwdutils
BuildArch: noarch
Vendor: David Greaves <david@dgreaves.com>
Url: http://github.com/MeeGoIntegration/boss-python-skynet/

%description
This provides the Exo wrapper for BOSS participants

%prep
%setup -n %{name}-%{version} -n %{name}-%{version}

%build
%python3_build

%install
sed -ie 's/__VERSION__/%{version}/g' setup.py
%python3_install

mkdir -p %{buildroot}%{_datadir}/boss-skynet
mkdir -p %{buildroot}%{_sysconfdir}/skynet/conf.d/
mkdir -p %{buildroot}%{_sysconfdir}/supervisor/conf.d
mkdir -p %{buildroot}/var/log/supervisor

%post
if [ $1 -eq 1 ]; then
    if ! grep "skynet" /etc/passwd; then
      /usr/sbin/useradd --system skynet
    fi

    systemctl start supervisord.service || true
    systemctl enable supervisord.service || true
else
    skynet rebuild --all || true
    skynet apply || true
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
%{_sysconfdir}/skynet/conf.d/
%dir %{_datadir}/boss-skynet
%dir %{_sysconfdir}/supervisor
%dir %{_sysconfdir}/supervisor/conf.d
%dir /var/log/supervisor
