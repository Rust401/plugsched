%define _prefix /usr/local
%define minor_name xxx
%define release yyy

Name:		scheduler-%{minor_name}
Version:	%{KVER}
Release:	%{KREL}.%{release}
Summary:	The schedule policy RPM for linux kernel scheduler subsystem
BuildRequires:	elfutils-devel
BuildRequires:	systemd
Requires:	systemd
Requires:	binutils
Requires:	cpio
Packager:	Yihao Wu <wuyihao@linux.alibaba.com>

Group:		System Environment/Kernel
License:	GPLv2
URL:		None
Source1:	scheduler-install
Source2:	plugsched.service
Source3:	version

%description
The scheduler policy rpm-package.

%prep
# copy files to rpmbuild/SOURCE/
cp %{_outdir}/scheduler-install %{_sourcedir}
cp %{_outdir}/plugsched.service %{_sourcedir}
cp %{_outdir}/version %{_sourcedir}

%build
# Build sched_mod
make -C %{_kerneldir} -f Makefile.plugsched plugsched -j %{threads}

# Build symbol resolve tool
make -C %{_kerneldir}/symbol_resolve

# Generate the tainted_functions file
awk -F '[(,)]' '$2!=""{print $2" "$3" vmlinux"}' %{_kerneldir}/tainted_functions{.h,_sidecar.h} > %{_kerneldir}/tainted_functions

#%pre
# TODO: confict check

%install
#install tool, module and systemd service
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_prefix}/lib/systemd/system
mkdir -p %{buildroot}%{_localstatedir}/plugsched/%{KVER}-%{KREL}.%{_arch}
mkdir -p %{buildroot}%{_rundir}/plugsched

install -m 755 %{_kerneldir}/symbol_resolve/symbol_resolve %{buildroot}%{_bindir}/symbol_resolve
install -m 755 %{_kerneldir}/kernel/sched/mod/scheduler.ko %{buildroot}%{_localstatedir}/plugsched/%{KVER}-%{KREL}.%{_arch}/scheduler.ko
install -m 444 %{_kerneldir}/tainted_functions %{buildroot}%{_localstatedir}/plugsched/%{KVER}-%{KREL}.%{_arch}/tainted_functions

install -m 755 %{SOURCE1} %{buildroot}%{_bindir}
install -m 755 %{SOURCE2} %{buildroot}%{_prefix}/lib/systemd/system
install -m 755 %{SOURCE3} %{buildroot}%{_localstatedir}/plugsched/%{KVER}-%{KREL}.%{_arch}/version

#install kernel module after install this rpm-package
%post
if [ $1 == 1 ];  then
	echo "Installing scheduler"
	systemctl daemon-reload
	systemctl enable plugsched
	systemctl start plugsched
elif [ $1 == 2 ];  then
	echo "Upgrading scheduler - install new version."
	/sbin/rmmod scheduler || echo "scheduler module not loaded. Skip rmmod and continue upgrade."
fi

#uninstall kernel module before remove this rpm-package
%preun
systemctl daemon-reload
if [ $1 == 0 ]; then
	echo "Uninstalling scheduler"
	/usr/local/bin/scheduler-install uninstall || exit 1
elif [ $1 == 1 ]; then
	echo "Upgrading scheduler - uninstall old version."
	systemctl start scheduler
fi

%files
%{_bindir}/symbol_resolve
%{_bindir}/scheduler-install
%{_prefix}/lib/systemd/system/plugsched.service
%{_localstatedir}/plugsched/%{KVER}-%{KREL}.%{_arch}/scheduler.ko
%{_localstatedir}/plugsched/%{KVER}-%{KREL}.%{_arch}/tainted_functions
%{_localstatedir}/plugsched/%{KVER}-%{KREL}.%{_arch}/version

%dir
%{_rundir}/plugsched

%changelog
