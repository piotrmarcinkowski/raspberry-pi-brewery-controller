# README #

This README would normally document whatever steps are necessary to get your application up and running.

### What is this repository for? ###

* Quick summary
* Version
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

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
export W1THERMSENSOR_NO_KERNEL_MODULE=1
python -m unittest discover -s tests/controller/ -p '*_test.py'
```

#### Deployment instructions ####

### Used libraries ###
* https://github.com/timofurrer/w1thermsensor

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
