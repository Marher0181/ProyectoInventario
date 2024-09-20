import os

class Config:
    #SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://ADMINMH:Marlon123@PC-DEV36/GestorInventario?driver=ODBC+Driver+17+for+SQL+Server'
    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://ADMINMH:ADMINMH@DESKTOP-HMS6GDC/GestorInventario?driver=ODBC+Driver+17+for+SQL+Server'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)