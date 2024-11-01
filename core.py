from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Person(db.Model):
    __tablename__ = 'persons'

    id = db.Column(db.Integer, primary_key=True)  # 这里设为整数
    name = db.Column(db.String(256))  # 设置长度为 256
    username = db.Column(db.String(256))  # 设置长度为 256
    password = db.Column(db.String(256))  # 设置长度为 256
    email = db.Column(db.String(256))  # 设置长度为 256
    ips = db.Column(db.Text)  # 以逗号分隔的 IP 地址字符串
    courses = db.Column(db.Text)  # 以逗号分隔的课程 ID 字符串
    classes = db.Column(db.Text)  # 以逗号分隔的班级 ID 字符串

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    name = db.Column(db.String(256))  # 设置长度为 256
    teacher = db.Column(db.String(256))  # 设置长度为 256
    courcations = db.Column(db.Text)  # 以逗号分隔的课程 ID 字符串

class Courcation(db.Model):
    __tablename__ = 'courcations'

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    location = db.Column(db.String(256))  # 设置长度为 256
    time_tables = db.Column(db.Text)  # 以逗号分隔的 (w, d, n) 元组(int, int, int) 字符串

class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    name = db.Column(db.String(256))  # 设置长度为 256
    administrators = db.Column(db.Text)  # 以逗号分隔的管理员 ID 字符串
    students = db.Column(db.Text)  # 以逗号分隔的学生 ID 字符串
    notifications = db.Column(db.Text)  # 以逗号分隔的通知 ID 字符串

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    title = db.Column(db.String(256))  # 设置长度为 256
    content = db.Column(db.Text)  # 通知内容
    deadline = db.Column(db.DateTime)  # 截止日期
    confirmeds = db.Column(db.Text)  # 以逗号分隔的确认者 ID 字符串
    unconfirmeds = db.Column(db.Text)  # 以逗号分隔的未确认者 ID 字符串
