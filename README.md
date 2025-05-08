# TeachMeUMB

Capstone Project - TeachMeUMB Tutoring App

Adapted from [The Flask Mega-Tutorial by Miguel Grinberg](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

## Database migration
- First enter virtual environment (example uses docker):
```bash
docker exec -it <container-name> sh
```
- if you there is no "migrations" folder it means you haven't initialized the database, please do so
```bash
flask db init
```
- stage migration changes and add a descriptive note:
```bash
flask db migrate -m "<context for migration>"
```
- push changes
```bash
flask db upgrade
```

### If you made a mistake and need to undo the last migration:
```bash
flask db downgrade
```

For more migration details [click here](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database)