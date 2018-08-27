# battmon
A simple battery monitoring tool for Linux operating systems

# Installation
## Ubuntu (Bionic, Xenial, Precise, Trusty, Cosmic) 
```
sudo add-apt-repository ppa:padiauj/battmon
sudo apt-get update
sudo apt-get install python3-battmon
```

## Manual 

### Dependencies 
* Python 3
* setuptools>=20.7.0
* matplotlib>=2.1.2
* numpy>=1.14.0
* PyQt4>=4.11.4

```
make 
sudo make install 
```

# How it works 
According to kernel specifications [here]( https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-power) individual power supplies are given subdirectories in `/sys/class/power_supply`. 

For batteries, the subdirectory contains:
* `type`
* `status`
* `capacity`
* `manufacturer`
* `model_name`
* `serial_number`

## --log
Battery logging is scheduled by cron to run every 2 minutes to `LOG_PATH=/var/log/battmon/'
For each power supply that has `supply/type` "Battery": the time (unix millisecond timestamp), `status`, and `capacity` are logged to  `LOG_PATH/<manufacturer>_<model_name>_<serial_number>.log`

# License
Battmon is licensed under GPLv2, which can be found [here](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html). 

