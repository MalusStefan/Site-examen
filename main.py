from website import create_app

app = create_app()

if __name__ == '__main__': #ruleaza site-ul doar daca rulezi codul
    app.run(debug=True)
