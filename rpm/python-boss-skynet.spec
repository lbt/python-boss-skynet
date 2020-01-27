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
sed -ie 's/__VERSION__/%{version}/g' setup.py
make

%install
sed -ie 's/__VERSION__/%{version}/g' setup.py
make PREFIX=%{_prefix} DESTDIR=%{buildroot} install
mkdir -p %{buildroot}%{_datadir}/boss-skynet

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
%dir %{_datadir}/boss-skynet
%dir %{_sysconfdir}/supervisor
%dir %{_sysconfdir}/supervisor/conf.d
%dir /var/log/supervisor
