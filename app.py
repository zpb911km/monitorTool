from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    student_id = db.Column(db.Integer, primary_key=True)  # 学号
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    
    classes = db.relationship('UserClass', back_populates='user')

class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)  # 班级ID
    name = db.Column(db.String(100), nullable=False)

    students = db.relationship('UserClass', back_populates='class_')

class UserClass(db.Model):  # 中间表，连接用户与班级
    __tablename__ = 'user_classes'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.student_id'), primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), primary_key=True)

    user = db.relationship('User', back_populates='classes')
    class_ = db.relationship('Class', back_populates='students')


from flask import Flask, jsonify
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = open('data\db_key', 'r').read()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def create_tables():
    db.create_all()
    # 随机生成数据
    if not User.query.first():  # 确保只初始化一次
        create_sample_data()

def create_sample_data():
    # 创建班级
    class1 = Class(name='班级A')
    db.session.add(class1)

    # 创建用户
    for i in range(1, 6):  # 生成5个学生
        user = User(student_id=i, username=f'user{i}', password='password')
        db.session.add(user)
        user_class = UserClass(user_id=i, class_id=class1.id)
        db.session.add(user_class)

    db.session.commit()

@app.route('/class/<int:class_id>/students', methods=['GET'])
def get_students(class_id):
    class_ = Class.query.get(class_id)
    if class_:
        students = UserClass.query.filter_by(class_id=class_.id).all()
        usernames = [User.query.get(student.user_id).username for student in students]
        return jsonify(usernames)
    return jsonify({"error": "班级不存在"}), 404

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
