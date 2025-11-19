# -------------------------------
# Conexión a MySQL
# -------------------------------
import databases
import sqlalchemy

DATABASE_URL = "mysql+mysqlconnector://fastapi:FastAPI123!@localhost:3306/ecomarketdb"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(DATABASE_URL)
