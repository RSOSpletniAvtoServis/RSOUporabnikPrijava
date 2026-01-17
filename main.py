from typing import Union
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from mysql.connector import pooling
from pydantic import BaseModel
from argon2 import PasswordHasher

app = FastAPI()
try:
    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        host="34.44.150.229",
        user="zan",
        password=">tnitm&+NqgoA=q6",
        database="RSOUporabnikPrijava"
    )
except Exception as e:
    print("Error: ",e)

ph = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=64 * 1024,  # 64 MB
    parallelism=4
)

class Stranka(BaseModel):
    username: str
    password: str
    ime: str
    priimek: str
    email: str
    telefon: str
    davcna: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (dev only!)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Mikrostoritev": "UporabnikPrijava"}

@app.get("/items/")
def read_items():
    return {"Tu": "So izdelki"}

@app.post("/registracija/")
def registriraj_stranko(stranka: Stranka):
    print(stranka.username)
    print(stranka.password)
    print(stranka.ime)
    print(stranka.priimek)
    print(stranka.email)
    print(stranka.telefon)
    print(stranka.davcna)
    hash = ph.hash(stranka.password)
    timestamp = time.time()
    print(hash)
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        
        sql = "INSERT INTO Uporabnik(UporabniskoIme,Geslo,Vloga,UniqueID) VALUES (%s,%s,3,%s)"
        cursor.execute(sql, (stranka.username,hash,timestamp))
        
        query = "SELECT ID_Uporabnik, UporabniskoIme, Vloga, UniqueID FROM Uporabnik WHERE UporabniskoIme = %s"
        cursor.execute(query,(stranka.username,))
        rows = cursor.fetchall()
        for row in rows:
            print(row)   # row is a tuple (id, name)
            sql = "INSERT INTO Stranka(Ime,Priimek,Email,Telefon,DavcnaStevilka,Uporabnik_ID_Uporabnik) VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, (stranka.ime,stranka.priimek,stranka.email,stranka.telefon,stranka.davcna,row[0]))
            break
        
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error: ", e)
    return {"Registracija": "Dela"}
    
@app.post("/prijava/")
def read_items():
    return {"Tu": "So izdelki"}

@app.get("/preveriusername/{username}")
def read_item(username: str):
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT ID_Uporabnik, UporabniskoIme, Vloga, UniqueID FROM Uporabnik WHERE UporabniskoIme = %s"
        cursor.execute(query,(username,))
        rows = cursor.fetchall()
        
        if rows:
            return {"valid": "False"}
        else:
            return {"valid": "True"}
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error: ", e)    
    return {"valid": "unknown"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
    
