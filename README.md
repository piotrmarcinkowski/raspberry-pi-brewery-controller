# README #

This README would normally document whatever steps are necessary to get your application up and running.

### What is this repository for? ###

* Quick summary
* Version
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

The app communicates with therm sensors via 1-wire interface. 
By default 1-wire support is disabled on Raspberry-Pi. The library
used for communication with therm sensors attempts to load kernel
module for 1-wire support at every start but preferred way is to
load this module manually and disable auto loading by setting
environment variable W1THERMSENSOR_NO_KERNEL_MODULE=1
In order manually add proper kernel module to enable 1-wire support
do the following on Raspberry-Pi device:
- sudo raspi-config
- Select 'Interfacing Options'
- Select 'P7 1-Wire'
- Select 'Yes' to enable 1-wire interface
- When leaving raspi-config remember to reboot the device
- After boot type lsmod and verify whether w1_gpio module is correctly loaded  

### Configuration ####

#### Dependencies ####

The code requires the dependencies defined in requirements.txt file to be installed. In order to do this type 

```  
pip install -r requirements.txt
```

In the project's root folder there is also requirements-dev.txt file. It contains dependencies that can be usefull for development. All the libraries defined there should already be installed on Raspberry device. Type the following line to install them in your development environment.

```
pip install -r requirements-dev.txt
```

#### How to run tests ####
In order to run unit tests type the following command in the root directory

```
pip3 install -r requirements.txt
export W1THERMSENSOR_NO_KERNEL_MODULE=1
python3 -m unittest discover -s tests
```

In order to run the tests from IDE like PyCharm you may need to specify
the W1THERMSENSOR_NO_KERNEL_MODULE variable in Run Configuration

#### Deployment instructions ####
On your raspberry-pi clone this project and run with

```
pip3 install -r requirements.txt
python3 -m app.main
```

### Used libraries ###
* https://github.com/timofurrer/w1thermsensor

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
