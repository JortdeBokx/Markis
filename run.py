from Markis import create_app

# Initialise the app
app = create_app()

app.run(host="127.0.0.1", port=5000, threaded=True)
