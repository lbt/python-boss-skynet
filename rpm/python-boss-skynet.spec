Summary: Boss Python SkyNET
Name: python-boss-skynet
Version: 0.4.0
Release: 1
Source0: %{name}_%{version}.orig.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires: python, python-setuptools
Requires: python, python-ruote-amqp >= 2.1.0, python-amqplib, python-air
BuildArch: noarch
Vendor: David Greaves <david@dgreaves.com>
Url: http://github.com/lbt/boss-python-skynet/

%description
UNKNOWN

%prep
%setup -n %{name}-%{version} -n %{name}-%{version}

%build
python setup.py build

%install
python setup.py install --prefix=/usr --single-version-externally-managed --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%{python_sitelib}/SkyNET
%doc README
%{_datadir}/doc/%{name}
