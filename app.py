from flask import Flask
from database.db import get_db_connection
from routes.auth import auth
from routes.groups import groups

app = Flask(__name__)

app.secret_key = "smartsplit-secret-key"

app.register_blueprint(auth)
app.register_blueprint(groups)

@app.route("/")
def home():
    return "SmartSplit is running! 🚀"


if __name__ == "__main__":
    app.run(debug=True)