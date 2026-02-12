from typing import Union
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from mysql.connector import pooling
from pydantic import BaseModel
from typing import List
from argon2 import PasswordHasher

db_healthy = True
app = FastAPI(root_path="/upopri")

for i in range(5):
    try:
        pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            host="127.0.0.1",               #34.44.150.229",
            user="zan",
            password=">tnitm&+NqgoA=q6",
            database="RSOUporabnikPrijava",
            autocommit=True
        )
    except Exception as e:
        print("Error: ",e)
        print(f"DB connection failed, retrying... ({i+1}/5)")
        time.sleep(5)
else:
    raise RuntimeError("Could not connect to the database after 5 attempts")
    db_healthy = False

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

class Prijava(BaseModel):
    username: str
    password: str

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


@app.get("/addadmin/")
def add_admin():
    username = "admin"
    password = "admin"
    hash = ph.hash(password)
    timestamp = time.time()
    print(hash)
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO Uporabnik(UporabniskoIme,Geslo,Vloga,UniqueID) VALUES (%s,%s,1,%s)"
        cursor.execute(sql, (username,hash,timestamp))
        return {"Dodaja": "Success"}
        
        
    except Exception as e:
        print("Error: ", e)
        return {"Dodaja": "Spodletela", "Error": e}
    finally:
        cursor.close()
        conn.close()     
    return {"Dodaja": "Unknown"}
    
@app.post("/prijava/")
def prijava(prijava: Prijava):
    uporabnikID = ""
    geslo = ""
    vloga = ""
    uniqueID = ""
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        
        query = "SELECT IDUporabnik, UporabniskoIme, Geslo, Vloga, UniqueID, IDTennant FROM Uporabnik WHERE UporabniskoIme = %s"
        cursor.execute(query,(prijava.username,))
        rows = cursor.fetchall()
        for row in rows:
            print(row)   # row is a tuple (id, name)
            uporabnikID = row[0]
            geslo = row[2]
            vloga = row[3]
            uniqueID = row[4]
            idtennant = row[5]
            break
        
        ph.verify(geslo, prijava.password)
        timestamp = int(time.time())
        #da se zagotovi, da je obstaja samo ena aktivna prijava na uporabnika
        sql = "DELETE FROM Prijava WHERE IDUporabnik = %s"
        cursor.execute(sql, (uporabnikID,))
        
        sql = "INSERT INTO Prijava(ZasebniKljuc,CasZacetka,CasTrajanja,IDUporabnik) VALUES (%s,%s,%s,%s)"
        cursor.execute(sql, ('kljuc',timestamp,1000,uporabnikID))
        return {"Prijava": "passed", "IDUporabnik": uporabnikID, "Vloga": vloga, "UniqueID": uniqueID, "idtennant": idtennant}
        
        
    except Exception as e:
        print("Error: ", e)
        print("MySQL error:", repr(e))
        return {"Prijava": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Prijava": "failed"}

class Odjava(BaseModel):
    uniqueid: str

@app.delete("/odjava/")
def odjava(odjava: Odjava):
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM Prijava WHERE IDUporabnik IN (SELECT IDUporabnik FROM Uporabnik WHERE uniqueid = %s)"
        cursor.execute(query,(odjava.uniqueid,))
        return {"Odjava": "passed"}
        
    except Exception as e:
        print("Error: ", e)
        print("MySQL error:", repr(e))
        return {"Odjava": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Odjava": "unknown"}    

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
    uporabnikID = ""
    vloga = ""
    uniqueID = ""
    timestamp = time.time()
    print(hash)
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        
        sql = "INSERT INTO Uporabnik(UporabniskoIme,Geslo,Vloga,UniqueID) VALUES (%s,%s,3,%s)"
        cursor.execute(sql, (stranka.username,hash,timestamp))
        
        query = "SELECT IDUporabnik, UporabniskoIme, Vloga, UniqueID FROM Uporabnik WHERE UporabniskoIme = %s"
        cursor.execute(query,(stranka.username,))
        rows = cursor.fetchall()
        for row in rows:
            print(row)   # row is a tuple (id, name)
            sql = "INSERT INTO Stranka(Ime,Priimek,Email,Telefon,DavcnaStevilka,IDUporabnik) VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, (stranka.ime,stranka.priimek,stranka.email,stranka.telefon,stranka.davcna,row[0]))
            uporabnikID = row[0]
            vloga = row[2]
            uniqueID = row[3]
            break
        
        
        
    except Exception as e:
        print("Error: ", e)
        return {"Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"UporabnikID": uporabnikID, "Vloga": vloga, "UniqueID": uniqueID}
    

@app.get("/preveriusername/{username}")
def preveri_username(username: str):
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT IDUporabnik, UporabniskoIme, Vloga, UniqueID FROM Uporabnik WHERE UporabniskoIme = %s"
        cursor.execute(query,(username,))
        rows = cursor.fetchall()
        
        if rows:
            return {"valid": "False"}
        else:
            return {"valid": "True"}
    except Exception as e:
        print("Error: ", e)
    finally:
        cursor.close()
        conn.close() 
    return {"valid": "unknown"}


# Zacetek za vodjo

class Vodja(BaseModel):
    username: str
    password: str

@app.post("/dodajvodjo/")
def dodaj_vodjo(vodja: Vodja):
    print(vodja.username)
    print(vodja.password)
    hash = ph.hash(vodja.password)
    uporabnikID = ""
    vloga = ""
    uniqueID = ""
    timestamp = time.time()
    print(hash)
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        
        sql = "INSERT INTO Uporabnik(UporabniskoIme,Geslo,Vloga,UniqueID) VALUES (%s,%s,%s,%s)"
        cursor.execute(sql, (vodja.username,hash,4,timestamp))
        
        query = "SELECT IDUporabnik, UporabniskoIme, Vloga, UniqueID FROM Uporabnik WHERE UporabniskoIme = %s"
        cursor.execute(query,(vodja.username,))
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Znamka not found")

        return {"Vodja": "passed", "IDUporabnik": row[0], "UporabniskoIme": row[1], "Vloga": row[2], "UniqueID": row[3]}

        
        
        
    except Exception as e:
        print("Error: ", e)
        return {"Vodja": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Vodja": "undefined"}

@app.get("/vodje/")
def get_vodje():
    try:
        with pool.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT IDUporabnik, UporabniskoIme, Vloga, UniqueID, IDTennant FROM Uporabnik WHERE Vloga = 4"
                )
                rows = cursor.fetchall()
        # Fixed columns → no need to read cursor.description
        return [
            {"IDUporabnik": row[0], "UporabniskoIme": row[1], "Vloga": row[2], "UniqueID": row[3], "IDTennant": row[4]}
            for row in rows
        ]
    except Exception as e:
        print("DB error:", e)
        raise HTTPException(status_code=500, detail="Database error")
    return {"Vodja": "failed"}   


class Vodja1(BaseModel):
    idvodja: str
    idtennant: str
    uniqueid: str
    
@app.put("/dodelivodjo/")
def dodeli_vodjo(vodja: Vodja1):
    userid = vodja.uniqueid
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM Uporabnik WHERE IDUporabnik = %s AND IDTennant IS NOT NULL"
        cursor.execute(sql, (vodja.idvodja,))
        row = cursor.fetchone()
        if row is None:
            sql = "UPDATE Uporabnik SET IDTennant = NULL WHERE IDTennant =  %s"
            cursor.execute(sql, (vodja.idtennant,))
            
            sql = "UPDATE Uporabnik SET IDTennant = %s WHERE IDUporabnik = %s"
            cursor.execute(sql, (vodja.idtennant,vodja.idvodja))
            return {"Vodja": "passed"}
        else:
            return {"Vodja": "failed", "Opis": "izbrani uporabnik je vodja že drugemu tennantu"}

        
    except Exception as e:
        print("Error: ", e)
        return {"Vodja": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Vodja": "undefined"}

class VodjaProst(BaseModel):
    uniqueid: str

@app.post("/prostevodje/")
def get_prostevodje(vodja: VodjaProst):
    userid = vodja.uniqueid
    try:
        with pool.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT IDUporabnik, UporabniskoIme, Vloga, UniqueID, IDTennant FROM Uporabnik WHERE Vloga = 4 AND IDTennant IS NULL"
                )
                rows = cursor.fetchall()
        # Fixed columns → no need to read cursor.description
        return [
            {"IDUporabnik": row[0], "UporabniskoIme": row[1], "Vloga": row[2], "UniqueID": row[3], "IDTennant": row[4]}
            for row in rows
        ]
    except Exception as e:
        print("DB error:", e)
        raise HTTPException(status_code=500, detail="Database error")
    return {"Vodja": "failed"}   

@app.delete("/odstranivodjo/")
def odstrani_vodjo(vodja: Vodja1):
    userid = vodja.uniqueid
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        sql = "UPDATE Uporabnik SET IDTennant = NULL WHERE IDUporabnik = %s"
        cursor.execute(sql, (vodja.idvodja,))
        return {"Vodja": "passed"}

        
    except Exception as e:
        print("Error: ", e)
        return {"Vodja": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Vodja": "undefined"}


# Konec za vodjo

# za username 

class Usernames(BaseModel):
    ids: List[int]
    uniqueid: str

@app.post("/usernames/")
def get_usernames(users: Usernames):
    print(users.ids)     # list[int]
    print(users.uniqueid)  # str
    ids_string = "("
    idmiddle = ",".join(str(i) for i in users.ids)
    full_string = "(" + idmiddle + ")"
    print(ids_string)
    print(idmiddle)
    print(full_string)
    
    try:
        with pool.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT IDUporabnik, UporabniskoIme FROM Uporabnik WHERE IDUporabnik IN " + full_string
                cursor.execute(sql)
                rows = cursor.fetchall()
        # Fixed columns → no need to read cursor.description
        return {row[0]: row[1] for row in rows}

    except Exception as e:
        print("DB error:", e)
        raise HTTPException(status_code=500, detail="Database error")
        return {"Username": "failed"} 
    return {"Username": "failed"}    


#konec za username

# Zacetek zaposleni

class Zaposleni(BaseModel):
    username: str
    password: str
    idtennant: str
    uniqueid: str

@app.post("/dodajzaposlenega/")
def dodaj_zaposlenega(zaposleni: Zaposleni):
    print(zaposleni.username)
    print(zaposleni.password)
    hash = ph.hash(zaposleni.password)
    uporabnikID = ""
    vloga = ""
    uniqueID = ""
    timestamp = time.time()
    print(hash)
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        
        sql = "INSERT INTO Uporabnik(UporabniskoIme,Geslo,Vloga,UniqueID,IDTennant) VALUES (%s,%s,%s,%s,%s)"
        cursor.execute(sql, (zaposleni.username,hash,2,timestamp,zaposleni.idtennant))
        
        query = "SELECT IDUporabnik, UporabniskoIme, Vloga, UniqueID FROM Uporabnik WHERE UporabniskoIme = %s"
        cursor.execute(query,(zaposleni.username,))
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Znamka not found")

        return {"Zaposleni": "passed", "IDUporabnik": row[0], "UporabniskoIme": row[1], "Vloga": row[2], "UniqueID": row[3]}

        
        
        
    except Exception as e:
        print("Error: ", e)
        return {"Zaposleni": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Zaposleni": "undefined"}



# Zacetek odstrani zaposlenega

class Uporabnik(BaseModel):
    iduporabnik: str
    uniqueid: str

@app.delete("/odstraniuporabnika/")
def odstrani_uporabnika(upo: Uporabnik):
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
            
        sql = "DELETE FROM Uporabnik WHERE IDUporabnik = %s"
        cursor.execute(sql, (upo.iduporabnik,))
        return {"Uporabnik": "passed"}
     
    except Exception as e:
        print("Error: ", e)
        return {"Uporabnik": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Uporabnik": "undefined"}

# Konec odstrani zaposlenega
# Konec zaposleni

# Zacetek stranka

class Stranka1(BaseModel):
    iduporabnik: str
    uniqueid: str

@app.post("/stranka/")
def get_stranka(stranka: Stranka1):
    
    try:
        with pool.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT IDStranka, Ime, Priimek, Email, Telefon, DavcnaStevilka, IDUporabnik FROM Stranka WHERE IDUporabnik = %s",
                    (stranka.iduporabnik,)
                )

                row = cursor.fetchone()

                if row is None:
                    raise HTTPException(status_code=404, detail="Znamka not found")

                return {"IDStranka": row[0], "Ime": row[1], "Priimek": row[2], "Email": row[3], "Telefon": row[4], "DavcnaStevilka": row[5], "IDUporabnik": row[6]}

    except HTTPException:
        raise
    except Exception as e:
        print("DB error:", e)
        raise HTTPException(status_code=500, detail="Database error")
        return {"Stranka": "failed"}
    return {"Stranka": "undefined"}


class Stranka2(BaseModel):
    ime: str
    priimek: str
    email: str
    telefon: str
    davcna: str
    iduporabnik: str
    uniqueid: str
    
@app.put("/posodobistranko/")
def posodobi_stranko(stranka: Stranka2):
    userid = stranka.uniqueid
    try:
        conn = pool.get_connection()
        # Create a cursor
        cursor = conn.cursor()

        query = "UPDATE Stranka SET Ime = %s, Priimek = %s, Email = %s, Telefon = %s, DavcnaStevilka = %s WHERE IDUporabnik = %s"
        cursor.execute(query,(stranka.ime,stranka.priimek,stranka.email,stranka.telefon,stranka.davcna,stranka.iduporabnik))
        return {"Stranka": "passed"}
  
    except Exception as e:
        print("Error: ", e)
        return {"Stranka": "failed"}
    finally:
        cursor.close()
        conn.close() 
    return {"Stranka": "unknown"}


#Konec stranka

# Zacetek geslo

class Geslo(BaseModel):
    trenutnogeslo: str
    novogeslo: str
    iduporabnik: str
    uniqueid: str

@app.put("/spremenigeslo/")
def spremenigeslo(geslo: Geslo):

    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        
        query = "SELECT IDUporabnik, UporabniskoIme, Geslo, Vloga, UniqueID, IDTennant FROM Uporabnik WHERE IDUporabnik = %s"
        cursor.execute(query,(geslo.iduporabnik,))
        row = cursor.fetchone()
        password = row[2]
        
        ph.verify(password, geslo.trenutnogeslo)
        
        hash = ph.hash(geslo.novogeslo)
        query = "UPDATE Uporabnik SET Geslo = %s WHERE IDUporabnik = %s"
        cursor.execute(query,(hash,geslo.iduporabnik,))
        return {"Geslo": "passed"}
        
        
        
        
    except Exception as e:
        print("Error: ", e)
        print("MySQL error:", repr(e))
        return {"Geslo": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Geslo": "failed"}

# Konec geslo

# Dobi stranke

class Stranka007(BaseModel):
    ids: List[int]
    uniqueid: str

@app.post("/izbranestranke/")
def get_izbranestranke(stranka: Stranka007):
    print(stranka.ids)     # list[int]
    print(stranka.uniqueid)  # str
    ids_string = "("
    idmiddle = ",".join(str(i) for i in stranka.ids)
    full_string = "(" + idmiddle + ")"
    print(ids_string)
    print(idmiddle)
    print(full_string)
    
    try:
        with pool.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT IDStranka, Ime, Priimek, Telefon, Email, DavcnaStevilka FROM Stranka WHERE IDStranka IN " + full_string
                cursor.execute(sql)
                rows = cursor.fetchall()
                # Fixed columns → no need to read cursor.description
                columns = [desc[0] for desc in cursor.description]
                return { row[0]: dict(zip(columns, row)) for row in rows}

    except Exception as e:
        print("DB error:", e)
        raise HTTPException(status_code=500, detail="Database error")
        return {"Stranka": "failed"} 
    return {"Stranka": "failed"}
    
#Komentar

# za health checks

@app.get("/health")
def health():
    return {"status": "ok"}
    
@app.get("/health/live")
def live():
    if db_healthy:
        return {"status": "alive"}
    else:
        return Response(status_code=500)

@app.get("/health/ready")
def ready():
    return {"status": "ready"}