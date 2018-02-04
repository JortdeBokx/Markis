# Markis
The ultimate File Management System for (almost) all Tu/e courses

Markis is written in python using the Flask Microframework

## Getting started
follow these instructions if you want to setup a copy of the project on your local machine for development and testing purposes.

### Prerequisits 
In order to setup the development environment you need to install the following:
firstle install [Python 3.6](https://www.python.org/downloads/release/python-360/), together with Pip.
then, in the root directory run `pip install -r requirements.txt` to install all dependancies. 

### Setup
After having installed the required packages you can run `python app.py` to run the server.

Configure `/instance/config.py` as you please. **Don't submit your version of this file to the repository**. We have added
a default development database in `config.py` for you to use. Should you wish to use your own development database overwrite the url in `/instance/config.py`

###folder structure
The files and folders are divided as follows:

| File/Folder         | description|
|---------------------|-------------|
| run.py              |This is the file that is invoked to start up a development server, it won't be used in production  |
| requirements.txt    |This file lists all of the Python packages needed to run this server, run `pip install -r requirements.txt` to install said packages |
| config.py           |This file contains most of the configuration variables, as well as STATIC variables |
| /instance/config.py |This file contains additional/overwritten settings specific to one's development environment. Your version should not be pushed to version control   |
| /Markis/            |The package of our app   |
| /Markis/__init__.py |This file initializes your application and brings together all of the various components   |
| /Markis/views.py    |This is where the routes are defined   |
| /Markis/models.py   |This is where models are defined   |
| /Markis/forms.py    |This is where forms are defined   |
| /Markis/static/     |This folder contains static files such as stylesheets and images   |
| /Markis/templates/  |This folder contains Jinja2 templates   |

More folders may be added as needed.

## Running the tests
TODO
## Built With
* [Flask](http://flask.pocoo.org/)
* [Bootstrap 4.0](https://v4-alpha.getbootstrap.com/)
* [jQuery](https://jquery.com/)

## Authors
Please see the list of [contributors](https://github.com/JortdeBokx/Markis/graphs/contributors) who participated in this project.

## Contributing
If you wish to implement a feature please first discuss your idea with the project owners before making an changes. 
All pull requests are to be reviewed by the project owners, who may suggest some changes or improvements or alternative.
In order to increase the chance your pull request will be accepted:
* Only implement features we approve of, you can check this by sending us an email
* Write tests
* Follow the [style guide](Style.md)
* Write proper commit messages: A (capitalised) max 50 char summary, followed by an optional max 72 char explanation. Always make your summary such that it finishes the sentence "If applied, this commit will ..." . [Don't do this](https://xkcd.com/1296/)
* New web-pages always extend base templates unless there is a valid reason not to