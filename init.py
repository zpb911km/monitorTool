# init.py
from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = open("data/se_key", "r", encoding="utf-8").read()  # 设置密钥
app.config["SQLALCHEMY_DATABASE_URI"] = open("data/db_key", "r", encoding="utf-8").read()  # 数据库配置
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from core import *  # 导入模型
