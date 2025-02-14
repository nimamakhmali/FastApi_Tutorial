from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

#@app.post('/index')
#def hello():
#    return 'Hello Post' 

#past prameter
@app.get('/blog/all')
def get_blogs():
    return {"message": f'all Blogs'}

@app.get('/blog/{id}')
def get_blog(id:int):
    return {"message": f'Blogs {id}'}

