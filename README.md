
# TeachMeUMB

## Table of Contents

- [Resources](https://github.com/dimarcode/TeachMeUMB/new/main?filename=README.md#resources)
- [Set Up Local Environment](https://github.com/dimarcode/TeachMeUMB/new/main?filename=README.md#set-up-local-environment)
  - [Prerequisites](https://github.com/dimarcode/TeachMeUMB/new/main?filename=README.md#prerequisites)
    - [Directions](https://github.com/dimarcode/TeachMeUMB/new/main?filename=README.md#directions)

# Resources

Flask: [https://flask.palletsprojects.com/en/stable/](https://flask.palletsprojects.com/en/stable/)

React: [https://react.dev/](https://react.dev/)

MySQL: [https://www.mysql.com/](https://www.mysql.com/)

HTML Forms: [https://www.w3schools.com/html/html_forms.asp](https://www.w3schools.com/html/html_forms.asp)

# Set Up Local Environment

## Prerequisites

**VSCode:**

- [https://code.visualstudio.com/](https://code.visualstudio.com/)

**Github account:**

- [https://github.com/](https://github.com/)

**Github extension for VSCode:**

- [https://code.visualstudio.com/docs/sourcecontrol/github](https://code.visualstudio.com/docs/sourcecontrol/github)
- Make sure to log in to extension within VSCode

**Docker:**

- Windows or Mac users (Docker for Desktop Personal): [https://docs.docker.com/get-started/get-docker/](https://docs.docker.com/get-started/get-docker/)
- Linux/VM users: [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)
- Docker extension for VSCode

**WSL (Windows users):**

- If you are on windows, you will not be able to run Docker without **Windows Subsystem for Linux.** (Obviously, this is not necessary for Mac)
  - [https://gcore.com/learning/how-to-install-wsl-2-on-windows/](https://gcore.com/learning/how-to-install-wsl-2-on-windows/)
  - Make sure it is WSL2!!!!

## Directions

1. Install prerequisites.

2. Open VSCode and choose the “clone a github repository” option

3. Paste the TeachMeUMB repository URL into VSCode and choose a directory to keep the project in

    1. [More about cloning a repository](https://code.visualstudio.com/docs/sourcecontrol/overview)

4. Clone the repo to that location

5. Make sure docker is running in the background, either by starting docker desktop, or by running `sudo systemctl start docker`

6. Right click the docker-compose.yml file and click `compose up`

    1. The compose file will create four containers, and between them, they will have all the dependencies necessary to run Javascript, python, SQL queries, html, css, flask, and react.

    2. Almost every folder is kept locally on your computer. I set it up this way so you can just edit the files.

    3. The files/folders you should **not** mess with are:

        1. Anything with “Docker” in the name.

        2. .Json files that you did not create

        3. requirements.txt

        4. .gitignore

7. Right now, if everything has been installed correctly, you should be able to open up chrome on your local machine and go to

    1. [http://localhost:5000/](http://localhost:5000/) and see "Flask is Running! 🚀" - this means the front end is working

    2. [http://localhost:5000/db-test](http://localhost:5000/db-test)“ and see “Object of type Row is not JSON serializable" - this means the back end is working, and your front end can talk to the MySQL database running in the other container

8. If there are any issues, please let me know ASAP ![(smile)](https://umb-capstone.atlassian.net/wiki/s/2089941738/6452/9284258a473d8a1043657188f7dc7de0057f64a0/_/images/icons/emoticons/smile.png "(smile)")
