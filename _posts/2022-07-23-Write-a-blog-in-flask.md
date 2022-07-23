```{python}
from flask import Flask

app = Flask(__name__)

@app.get('/')
def index():
    return '<h1>Hello</h1>'
```


    ::python
    from flask import Flask

    app = Flask(__name__)

    @app.get('/')
    def index():
        return '<h1>Hello</h1>'