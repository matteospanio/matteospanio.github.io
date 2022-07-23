```{python}
from flask import Flask

app = Flask(__name__)

@app.get('/')
def index():
    return '<h1>Hello</h1>'
```


    #!/usr/bin/python3
    from flask import Flask

    app = Flask(__name__)

    @app.get('/')
    def index():
        return '<h1>Hello</h1>'