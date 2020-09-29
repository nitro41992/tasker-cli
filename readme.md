````
  __  __  _                _                 __  __
 / / / / | |_   __ _  ___ | | __  ___  _ __  \ \ \ \
/ / / /  | __| / _` |/ __|| |/ / / _ \| '__|  \ \ \ \
\ \ \ \  | |_ | (_| |\__ \|   < |  __/| |     / / / /
 \_\ \_\  \__| \__,_||___/|_|\_\ \___||_|    /_/ /_/

````

# To Configure

Install virtual env

```
pip install virtualenv
```

Create an environment in your project directory

```
py -m venv venv
source venv/Scripts/activate
```

Install all necessary packages

```
pip install -r requirements.txt
```

Run the program

```
py tasker.py
```

To convert.py to .exe run the following command:
```
pyinstaller.exe --onefile tasker.py
```
**Note:** The executable will be located in dist directory


#
**Before committing and pushing to the repo, make sure the requirements.txt are updated with any of the imports**

```
pip freeze > requirements.txt
```