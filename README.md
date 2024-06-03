### Setup google docs access

You'll need to create google service account and invite that account to your target spreadsheet as editor. 

Enable following services:
Google Sheets API
Google Drive API

Download json file with credentials of your service account and rename it to 'credentials.json'.
Place file in project directory (same directory as 'example.env' file)

Here's the video guide for the process described above:
https://www.youtube.com/watch?v=fxGeppjO0Mg

### Setting up the environment
Rename the env.example file to .env in the project's root directory, then populate it with all the necessary values.

### Bot setup:

> You will need at least python 3.11 to run this project
1. python -m venv venv - create virtual environment
2. source venv/bin/activate - activate virtual environment
3. pip install -U . - install project dependencies
4. bot-run - to start the bot