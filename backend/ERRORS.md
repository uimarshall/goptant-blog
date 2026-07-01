## {"detail":"Not Found"}

If you get this type of error after starting the server and view it in the browser: `http://127.0.0.1:8000/api/html`
It means you did not use `@` decorator when defining the route, it should be `@app.get` and not just `app.get`.

```python

app.get("/api/html}", response_class=HTMLResponse)
```

Or watch out for wrong url: `@app.get("/api/html}", response_class=HTMLResponse)`

```python
@app.get("/api/html}", response_class=HTMLResponse)
```

There is an extra `}` at the end, so FastAPI registers `/api/html}` not `/api/html`.

Use this instead:

```python
@app.get("/api/html", response_class=HTMLResponse)
def get_post_html():
    ...
```

Then open:

- `http://127.0.0.1:8000/api/html`
