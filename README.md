# Recipe Catalog

This is a project made with Flask that allows Users to add their own recipes. Users can edit,
delete or update their recipes.

## Dependencies

[Flask 0.9](http://flask.pocoo.org/docs/0.12/installation/)

[SQLite 2.6.0](https://www.sqlite.org/download.html)

[SQL Alchemy 1.1.10](https://www.sqlalchemy.org/download.html)

[Bootstrap](http://getbootstrap.com/)

If using vagrant you can ignore the above:

[VirtualBox](https://www.virtualbox.org/wiki/Downloads)

[Vagrant](https://www.vagrantup.com/downloads.html)

[Vagrant Config File](https://github.com/udacity/fullstack-nanodegree-vm)

## Installation

### Vagrant Users

1. In the root directory use the command:

```
vagrant up
```

2. Once finished type in:

```
vagrant ssh
```

3. Once logged in type:

```
cd /vagrant
```


### Get this repository

In your terminal type in:

```
git clone https://github.com/arthurchan1111/catalog.git

```
Or download the repository [here](https://github.com/arthurchan1111/catalog.git)

If using vagrant:

Copy the files into catalog directory of the [Vagrant Config File](https://github.com/udacity/fullstack-nanodegree-vm)

### Set up Google OAuth2 application

1. Go to your app's page in the Google APIs Console — https://console.developers.google.com/apis

2. Choose Credentials from the menu on the left.

3. Create an OAuth Client ID.

4. Click on configure consent screen

5. Type in a product name and save

6. When you're presented with a list of application types, choose Web application.

7. Set the authorized JavaScript origins to http://0.0.0.0:5000 and http://localhost:5000

8. Click create client ID

9. Click download JSON and save it into the root directory of this project.

10. Rename the JSON file to **client_secret.json**

11. In the file **login.html** change the data-clientid="" to the client_id which can be found in **client_secret.json**

### Set up database and start application

1. Go to the root directory of this project and type:

```
python database_setup.py
```
2. Then type in:

```
python application.py
```

3. In your browser type in http://0.0.0.0:5000 or http://localhost:5000
