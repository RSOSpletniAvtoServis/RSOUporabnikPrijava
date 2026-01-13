from typing import Union

from fastapi import FastAPI

import mysql.connector

app = FastAPI()


@app.get("/")
def read_root():
    return {"Mikrostoritev": "UporabnikPrijava"}

@app.get("/items/")
def read_items():
    return {"Tu": "So izdelki"}

@app.post("/registracija/")
def registriraj_stranko(username: str, password: str, ime: str, priimek: str, email: str, telefon: str, davcna: str):
    print(username)
    print(password)
    print(ime)
    print(priimek)
    print(email)
    print(telefon)
    print(davcna)
    return {"Tu": "So izdelki"}
    
@app.post("/prijava/")
def read_items():
    return {"Tu": "So izdelki"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
    
