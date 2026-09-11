This Repository contains a mix of Python scripts written for MacOS, Python scripts written for Ubuntu Desktop and Ubuntu Server, and Powershell scripts written for Windows.  There are multiple sets of scripts here, some that interface with native OS UPS shutdown and some that work with either apcupsd or NUT

Native UPS USB shutdown

Windows, MacOS & Ubuntu Desktop all will autodetect the USB bus on boot looking for a UPS connected via USB.  If the UPS implements the HID Power Devices. Power Device Page (x84) defined by the USB Implementers Forum, Inc. on usb.org, then these OSes will attach drivers to the USB vendor and product ID.

MacOS will then access a detected USB from its System Preferences -> Energy Saver -> UPS button.  This desktop configuration permits configuration of shutdown options.

Windows will access a detected UPS from it's System -> Power & battery (Power & Sleep) Settings.  This driver only pays attention to whether or not the UPS is Online to AC power or On Battery, when On Battery is detected, it can be set to put the machine to sleep after a few minutes.  (effectively it treats the UPS the same as it treats a laptop that is battery) If the UPS reports very low battery a modern Windows OS will transition from S0 (sleep) to S4 (hibernate)

Ubuntu Desktop will check the /etc/UPower/UPower.conf.d/ directory for a configuration snippit that can be configured to shut the system down when it goes on UPS.

There are two problems with these vendor-included UPS monitoring schemes:

1.  Some vendors do not implement data properly according to the HID Power Devices Power Device Page, as a result unless the operating system vendor has put code specifically in for those UPSes they will report missing, partial, or incorrect data.  Minuteman, Triplite & Cyberpower UPSes have all been reported to have problems or work on some versions of MacOS and not later versions and so on.
2.  These vendor-supplied programs have no way of distributing UPS status to other computers, so for large UPSes that have many computers plugged into them, only 1 computer will be able to monitor the UPS and shut down.
3.  Some of the operating systems are very hostile to users attempting to block the OS's drivers from attaching to a UPS, even one that it does not properly interpret output from.

This is why the 2 major UPS monitoring software packages,  NUT and apcupsd, were written.  

NUT and apcupsd take different approaches to the problem of #1.  NUT has wide support for many different models of UPS while apcupsd has concentrated on supporting only APC's UPS products.

Both of these take different approaches to the problem of #2, they each have custom-built, incompatible network protocols used to distribute UPS shutdown information.  I have written scripts that implement these protocols in several repos that can be used as a base should a developer want to write a client program.  Both of these distributions can also act as client programs ad well as server programs using their protocols.

Both take different approaches to the problem of #3:

1. apcupsd wrote a kernel extension for MacOS that prevents MacOS X from attaching to a USB connected UPS, named ApcupsdDummy.kext, which is placed in /System/Library/Extensions, and they wrote a USB device driver for Windows that replaces the Windows UPS HID driver.  They can also use the detach call in libusb under Ubuntu or the installer can put a udev rule in to prevent the UPS from being claimed by the operating system.  Under MacOS they use libusb with the dummy driver to access the USB UPS
2. NUT wrote a compatibility driver for MacOS named macosx-ups that queries the built in Mac USB UPS drivers in read only mode for UPS information.  Under Windows they wrote a driver usbhid-ups and the installer must disable any USB driver in Windows Device Manager.  Under Linux the installer must create a udev rule that blocks the hid-generic driver in Linux from claiming the UPS so that the NUT driver usbhid-ups can claim the UPS USB device.

The downside to both NUT and apcupsd is that these are compiled programs and not easy to modify or correct bugs in by end users.  While they work on current versions of these three operating systems, not all features work.  For example, gapcmon in apcupsd was never ported to Windows and Ubuntu removed any support for gconf in version 26 of Ubuntu which gapcmon is dependent on.  In some OS/UPS Model cases, users have to resort to serial port connectivity to the UPS to get them to work with these programs.

My approach here to these problems is with the following scripts:

1. For operating system/UPS model combinations where there is solid OS support of a UPS, I have scripts that will interface with the OS-supplied UPS monitoring and offer UPS status over the network via JSON queries.  Some will offer to shutdown the operating system if the OS does not provide a proper shutdown in it's support (Windows)
2. For operating systems where the OS does NOT support the UPS model, and either apcupsd or NUT is loaded, I have bridge scripts that will query NUT or apcupsd locally and offer UPS status over the network via JSON
3. For operating system/monitor package combos where there is no longer a working desktop monitor (due to bitrot of code in NUT or apcupsd) I have scripts that provide that on the desktop.  Some also offer a JSON server mode where UPS status of the connected UPS is made available over the network in a read-only manner
4. I also bave some NUT (Network UPS Tools) client monitoring scripts, these scripts query a NUT server over the network and can replace programs like WinNUT and shut the system down if the remote NUT server reports the UPS is on battery.
5. I also have JSON client scripts that monitor the JSON servers created by the first group to shut down the device they are on, if the JSON server reports the UPS has gone on battery.

None of these are executable software programs so as to allow easy user modification, support for different UPS models, easy bug fixes, and avoid the security requirements of executable programs on some operating systems and to make their operation completely transparent for easy security auditing by the user.  See the documentation files. 

UPS manufacturers who offer UPS shutdown software often charge for versions of it that allow for distributed shutdown information. Commercial software for UPSes generally takes the approach that control of an individual UPS on an individual computer is free, and often manufacturer's software to do this is free.  But any software that allows for a single PC to communicate status to multiple PCs plugged into the same UPS is considered commercial and costs, and worse nowadays is that there is sometimes a subscription fee.   In addition, manufacturers will not keep their software packages updated for newer operating systems once their model of UPS they wrote it for is no longer being sold.

These scripts were all debugged on the oldest, simplest, cheapest UPSes I could find with UPS monitoring ports that speak UPS USB HID.  There are some very proprietary UPSes that do
have USB monitoring ports that are completely proprietary and use protocols that are alien to USB HID UPS.  These scripts do not support that.

Network parameters available via the JSON servers are simple, just enough to enable networked shutdown.

The following files are contained here:

simple-ups-server.py    Python server that queries a USB connected UPS for status and makes that status available via a JSON query.  For Macintosh

Shutdown-Monitor-Mac.py   Desktop cient program that queries a JSON server for UPS status and shuts the system down if the UPS loses AC power.  For Macintosh

query-apc-on-usb.py    Diagnostic program to see if a USB-connected UPS is compatible with Monitor-UPS.ps1.  For Macintosh

ups_monitor.py   Desktop program that creates an icon on a Macintosh desktop the user can click on and get status of the UPS, as well as making a JSON server available. For Macintosh

GetUPSStatusNUT.py  Desktop program for the iMac that creates an icon on an Apple Macintosh desktop that the user can click on and get status of a UPS on a NUT server and will shut down the iMac if the NUT UPS goes on battery.  This is a NUT client.  For Macintosh

GetUPSStatusNUT.py.README.html  documentation for GetUPSStatusNUT.py

Monitor-UPS.ps1   Desktop program that creates an icon on a Windows desktop the user can click on and get status of the UPS, as well as making a JSON server available.  It can also monitor a remote NUT server and shut down the PC if the UPS goes on battery  For Windows

Monitor-UPS-ReadInfo.ps1  Command line test diagnostic program that reads a USB-connected UPS to see if it is compatible with Monitor-UPS.ps1.    For Windows

ubuntu_ups_monitor.py  Python script for Ubuntu Desktop that hooks into the upower program that is included in Ubuntu Desktop and provides a JSON server for a USB UPS HID connected UPS, this puts a status indicator icon on the desktop that it is running

ubuntu_ups_info.py  Python script for Ubuntu Desktop that queries the upower/dbus program for stats for a USB UPS HID connected UPS, used for testing to see if the attached UPS will work

README-Ubuntu-UPS_monitor.html   HTML documentation for the ubuntu_ups_monitor.py script

ubuntuREADME-UPS_monitor.txt  textfile that is saved most likely in /root/UPS or other convenient location for use with the desktop icon to provide a readme menu for it

