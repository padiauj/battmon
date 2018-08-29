# battmon
A simple battery monitoring tool for Linux operating systems.

## Screenshot
![](http://i.imgur.com/V4RNRZa.png)

# Installation
## Ubuntu (Xenial) 
```
sudo add-apt-repository ppa:padiauj/battmon
sudo apt-get update
sudo apt-get install battmon
```
## Manual  (all other Linux Distributions) 
Clone (or download) the repository using:

```
git clone https://github.com/padiauj/battmon.git
cd battmon
sudo make install 
```

### Dependencies 
* Python 3
* setuptools>=20.7.0
* matplotlib>=2.1.2
* numpy>=1.14.0
* PyQt4>=4.11.4

# Usage
```
usage: battmon [-h] [--log] [--graph]

optional arguments:
  -h, --help  show this help message and exit
  --log       log current battery charge and status
  --graph     show battery history graph GUI
```

# How it works 
According to kernel specifications [here]( https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-power), individual power supplies are given subdirectories in `/sys/class/power_supply`. 

For batteries, the subdirectory contains files such as:
* `type`
* `status`
* `capacity`
* `manufacturer`
* `model_name`
* `serial_number`

## --log
Battery logging is scheduled by cron to run every 2 minutes to `LOG_PATH=/var/log/battmon/`

For each power supply that has `supply/type` "Battery": 
* the time (unix millisecond timestamp), 
* `status`, 
* `capacity` 

are logged to `LOG_PATH/<manufacturer>_<model_name>_<serial_number>.log`

## --graph
Battmon presents a GUI with an interactive plot and current battery statistics. (shown in the screenshot above)

# License
Battmon is licensed under GPLv2, which can be found [here](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html). 

