from website import App
app = App(__name__)

if __name__ == "__main__":
    app.run(threaded=True)
