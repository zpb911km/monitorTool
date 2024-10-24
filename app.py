from flask import Flask, render_template, redirect, request, session, Response
from core import Person, Class, Notification, Schedule, Html_index, Html_Error
import os
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import traceback
import requests as rq
from bs4 import BeautifulSoup
#from flask_proxy import FlaskProxy


app = Flask(__name__)

app.secret_key = open('se_key.txt', 'r').read()
#app.wsgi_app = FlaskProxy(app.wsgi_app)
users_file = 'data/users.json'
class_file = 'data/classes.json'
feedback_file = 'data/feedback.txt'
notification_file = 'data/notification.json'
current_users = {}
app.config['SQLALCHEMY_DATABASE_URI'] = open('db_key.txt', 'r').read()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Backup(db.Model):
    created_at = db.Column(db.DateTime, primary_key=True, unique=True, nullable=False, default=datetime.now)
    users = db.Column(db.JSON)
    classes = db.Column(db.JSON)
    notifications = db.Column(db.JSON)
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


with app.app_context():
    db.create_all()


for file in [users_file, class_file, notification_file]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([{}], f, indent=4, ensure_ascii=False)


users = []
classes = []
notifications = []
for user in json.load(open(users_file)):
    if user == {}:
        continue
    p = Person()
    p.from_dict(user)
    users.append(p)
for class_ in json.load(open(class_file)):
    if class_ == {}:
        continue
    c = Class()
    c.from_dict(class_)
    classes.append(c)
for notification in json.load(open(notification_file)):
    if notification == {}:
        continue
    n = Notification()
    n.from_dict(notification)
    notifications.append(n)
for user in users:
    current_users[user.username] = user


def save_files():
    global users, classes, notifications, current_users
    notifications.sort(key=lambda x: (x.deadline - datetime.now()).days, reverse=False)
    notification_name_and_class = []
    for notification in notifications:
        name_and_class = (notification.title, notification.class_name)
        if name_and_class not in notification_name_and_class:
            notification_name_and_class.append(name_and_class)
        else:
            notifications.remove(notification)
    users_name_and_id = []
    for user in users:
        name_and_id = (user.name, user.id)
        if name_and_id not in users_name_and_id:
            users_name_and_id.append(name_and_id)
        else:
            users.remove(user)
    class_name_and_owner = []
    for class_ in classes:
        name_and_owner = (class_.name, class_.owner.name)
        if name_and_owner not in class_name_and_owner:
            class_name_and_owner.append(name_and_owner)
        else:
            classes.remove(class_)
    with open(notification_file, 'w') as f:
        json.dump([notification.to_dict() for notification in notifications], f, indent=4, ensure_ascii=False)
    with open(users_file, 'w') as f:
        json.dump([user.to_dict() for user in users], f, indent=4, ensure_ascii=False)
    with open(class_file, 'w') as f:
        json.dump([class_.to_dict() for class_ in classes], f, indent=4, ensure_ascii=False)
    users = []
    for user in json.load(open(users_file)):
        if user == {}:
            continue
        p = Person()
        p.from_dict(user)
        users.append(p)
    classes = []
    for class_ in json.load(open(class_file)):
        if class_ == {}:
            continue
        c = Class()
        c.from_dict(class_)
        c.update_members(users)
        classes.append(c)
    notifications = []
    for notification in json.load(open(notification_file)):
        if notification == {}:
            continue
        n = Notification()
        n.from_dict(notification)
        notifications.append(n)
    for user in users:
        current_users[user.username] = user
    backup = Backup(users=[user.to_dict() for user in users], classes=[class_.to_dict() for class_ in classes], notifications=[notification.to_dict() for notification in notifications])
    backup.save()


def class_name_list():
    global classes, users
    class_names = []
    if classes != []:
        for class_ in classes:
            for student in class_.students:
                if student.username == session['username']:
                    class_names.append(class_.name)
    else:
        class_names = []
    return class_names


@app.route('/')
def index():
    if 'username' not in session or len(current_users) == 0:
        return redirect('/login')
    else:
        save_files()
        widget = ''
        for class_ in classes:
            for notification in notifications:
                if class_.name == notification.class_name:
                    c = class_
                else:
                    continue
                for receiver in c.students:
                    if receiver.username == session['username']:
                        widget += notification.to_html(receiver.username)
                        break
        index_page = Html_index(current_users[session['username']], class_name_list(), widget)
        return index_page.get_html()


@app.route('/about')
def about():
    return render_template('guide.html')


@app.route('/temp')
def temp():
    a = 10/0
    return render_template('temp.html')


@app.route('/static/css/<file_name>')
def css(file_name):
    return app.send_static_file(f'css/{file_name}')


@app.route('/static/js/<file_name>')
def js(file_name):
    return app.send_static_file(f'js/{file_name}')


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedback = request.form['feedback']
        with open(feedback_file, 'a') as f:
            f.write(f"{session['username']}:{feedback}\n")
        return redirect('/')
    else:
        placeholder = '''请输入您的反馈,我们将尽快处理.
如果可以的话,请详细描述复现问题的操作步骤,以便我们更快的定位问题.'''
        widget = '<form method="post">'
        widget += '<textarea name="feedback" id="feedback" rows="10" cols="50" class="input-item" placeholder="{0}"></textarea><br>'.format(placeholder)
        widget += '<button type="submit" class="btn">提交</button>'
        widget += '</form>'
        index_page = Html_index(current_users[session['username']], class_name_list(), widget)
        return index_page.get_html()


@app.route('/create_class', methods=['GET', 'POST'])
def create_class():
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        try:
            class_name = request.form['class_name']
            class_owner = current_users[session['username']]
            members = []
            for member in request.form['members'].split('\n'):
                m_name, m_id = member.split(' ')
                m_name = m_name.strip()
                m_id = m_id.strip()
                for u in users:
                    if u.name == m_name and u.id == m_id:
                        members.append(u)
                        break
                else:
                    m = Person(m_name, m_id)
                    users.append(m)
                    members.append(m)
            c = Class(class_name, class_owner, members)
            global classes
            class_names = []
            if classes != []:
                for class_ in classes:
                    class_names.append(class_.name)
            else:
                class_names = []
            if class_name in class_names:
                err = Html_Error('班级名已存在', '请更换班级名')
                return err.get_html()
            classes.append(c)
            save_files()
            return redirect(f'/class/{class_name}')
        except Exception as e:
            err = Html_Error('创建班级失败', '请检查班级信息是否正确<br>错误信息：' + str(e))
            return err.get_html()
    else:
        class_names = class_name_list()
        widget = open('templates/create_class.html').read()
        index_page = Html_index(current_users[session['username']], class_names, widget)
        return index_page.get_html()


@app.route('/class/<class_name>', methods=['GET', 'POST'])
def class_page(class_name):
    global classes
    for class_ in classes:
        if class_.name == class_name:
            current_class = class_
            break
    else:
        err = Html_Error(f'未找到班级:{class_name}', '请返回')
        return err.get_html()
    current_class.update_members(users)
    save_files()
    if request.method == 'POST':
        if 'members' in request.form:
            members = []
            for member in request.form['members'].split('\n'):
                m_name, m_id = member.split(' ')
                m_name = m_name.strip()
                m_id = m_id.strip()
                for u in users:
                    if u.name == m_name and u.id == m_id:
                        members.append(u)
                        break
                else:
                    m = Person(m_name, m_id)
                    users.append(m)
                    members.append(m)
            new_class = Class(current_class.name, current_class.owner, members)
            for class_ in classes:
                if class_.name == current_class.name:
                    classes.remove(class_)
                    break
            classes.append(new_class)
            save_files()
            return redirect(f'/class/{class_name}')
        elif 'titles' in request.form:
            for title in request.form.getlist('titles'):
                for notification in notifications:
                    if notification.title == title and notification.class_name == class_name:
                        notifications.remove(notification)
                        break
            save_files()
            return redirect(f'/class/{class_name}')
    if session['username'] == current_class.owner.username:
        widget = open('templates/class_method_owner.html').read()
        notification_html = '<details><summary>已发布通知以及确认情况</summary><ul>'
        for notification in notifications:
            if notification.class_name == class_name:
                notification_html += f'<li>{notification.to_confirmed_html(classes)}</li>'
        notification_html += '</ul></details>'
        widget = widget.replace('<!--confirm_details-->', notification_html)
        widget = widget.replace('<!--len-->', str(len(current_class.students) + 10))
        widget = widget.replace('<!--members-->', '\n'.join([f'{u.name} {u.id}' for u in current_class.students]))
        widget = widget.replace('<!--class_name-->', class_name)
    else:
        widget = open('templates/class_method_member.html').read()
        widget = widget.replace('<!--class_name-->', class_name)
    html = Html_index(current_users[session['username']], class_name_list(), widget)
    return html.get_html()


@app.route('/class/<class_name>/write_notification', methods=['GET', 'POST'])
def write_notification(class_name):
    for class_ in classes:
        if class_.name == class_name:
            current_class = class_
            break
    else:
        err = Html_Error(f'未找到班级:{class_name}', '请返回')
        return err.get_html()
    current_class.update_members(users)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        deadline = request.form['deadline']
        need_confirm = request.form.get('need_confirm', 'off') == 'on'
        need_submit = request.form.get('need_submit', 'off') == 'on'
        if need_confirm:
            confirmed_users = []
        else:
            confirmed_users = []
            for u in current_class.students:
                confirmed_users.append(u)
        notification = Notification(title, content, deadline, class_name, confirmed_users, need_submit)
        global notifications
        notifications.append(notification)
        save_files()
        return redirect('/')
    else:
        widget = open('templates/write_notification.html').read()
        html = Html_index(current_users[session['username']], class_name_list(), widget)
        return html.get_html()


@app.route('/class/<class_name>/delete_notification/<title>')
def delete_notification(class_name, title):
    for class_ in classes:
        if class_.name == class_name:
            current_class = class_
            break
    else:
        err = Html_Error(f'未找到班级:{class_name}', '请返回')
        return err.get_html()
    current_class.update_members(users)
    global notifications
    for notification in notifications:
        if notification.title == title and notification.class_name == class_name and session['username'] == current_class.owner.username:
            notifications.remove(notification)
            break
    save_files()
    return redirect(f'/class/{class_name}')


@app.route('/class/<class_name>/confirm/<title>')
def confirm_notification(class_name, title):
    for class_ in classes:
        if class_.name == class_name:
            current_class = class_
            break
    else:
        err = Html_Error(f'未找到班级:{class_name}', '请返回')
        return err.get_html()
    current_class.update_members(users)
    for notification in notifications:
        if notification.title == title and notification.class_name == class_name:
            notification.add_confirmed_user(current_users[session['username']])
            save_files()
            return redirect('/')
    else:
        err = Html_Error(f'未找到通知:{title}', '请返回')
        return err.get_html()


@app.route('/class/<class_name>/disconfirm/<title>')
def disconfirm_notification(class_name, title):
    for class_ in classes:
        if class_.name == class_name:
            current_class = class_
            break
    else:
        err = Html_Error(f'未找到班级:{class_name}', '请返回')
        return err.get_html()
    current_class.update_members(users)
    for notification in notifications:
        if notification.title == title and notification.class_name == class_name:
            notification.remove_confirmed_user(current_users[session['username']])
            save_files()
            return redirect('/')
    else:
        err = Html_Error(f'未找到通知:{title}', '请返回')
        return err.get_html()


@app.route('/class/<class_name>/exit')
def exit_class(class_name):
    for class_ in classes:
        if class_.name == class_name:
            current_class = class_
            break
    else:
        err = Html_Error(f'未找到班级:{class_name}', '请返回')
        return err.get_html()
    current_class.update_members(users)
    if session['username'] == current_class.owner.username:
        for class_ in classes:
            if class_.name == class_name:
                classes.remove(class_)
                break
        save_files()
        return redirect('/')
    for u in current_class.students:
        if u.username == session['username']:
            current_class.students.remove(u)
            break
    else:
        err = Html_Error(f'你不是{class_name}的成员', '请返回')
        return err.get_html()
    save_files()
    return redirect('/')


@app.route('/class/<class_name>/schedule')
def class_member_page(class_name):
    for class_ in classes:
        if class_.name == class_name:
            current_class = class_
            break
    else:
        err = Html_Error(f'未找到班级:{class_name}', '请返回')
        return err.get_html()
    current_class.update_members(users)
    save_files()
    if session['username'] == current_class.owner.username:
        time_table = current_class.time_table_to_html(users, True)
        html = Html_index(current_users[session['username']], class_name_list(), time_table)
        return html.get_html()
    else:
        time_table = current_class.time_table_to_html(users, False)
        html = Html_index(current_users[session['username']], class_name_list(), time_table)
        return html.get_html()


@app.route('/class/<class_name>/submitfiles', methods=['GET', 'POST'])
def submit_files(class_name):
    dir = f'files/{class_name}'
    if not os.path.exists(dir):
        os.makedirs(dir)
    if request.method == 'POST':
        ALLOWED_EXTENSIONS = {'txt', 'pdf', 'zip', 'rar', '7z', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx'}

        if 'file' not in request.files:
            err = Html_Error('没有文件部分', '请选择文件')
            return err.get_html()

        file = request.files['file']

        # 如果用户没有选择文件，浏览器提交空表单
        if file.filename == '':
            err = Html_Error('没有选择文件', '请选择文件')
            return err.get_html()

        # 如果文件名合法，保存文件
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            filename = file.filename
            file.save(os.path.join(dir, filename))
            html = Html_index(current_users[session['username']], class_name_list(), f'<h2>文件{filename}上传成功</h2>')
            return html.get_html()

        err = Html_Error('文件类型不支持', '请上传txt,pdf,zip,rar,7z,doc,docx,ppt,pptx,xls,xlsx格式的文件')
        return err.get_html()
    widget = open('templates/upload.html').read()
    html = Html_index(current_users[session['username']], class_name_list(), widget)
    return html.get_html()


@app.route('/user/<username>', methods=['POST', 'GET'])
def user_page(username):
    if request.method == 'POST':
        raw_schedule = request.form['raw']
        if raw_schedule == '':
            err = Html_Error('课表为空', '请填写课表')
            return err.get_html()
        session['username'] = username
        for user in users:
            if user.username == username:
                user.schedule.update_course(raw_schedule)
                save_files()
                return redirect(f'/user/{username}')
        else:
            err = Html_Error(f'未找到用户:{username}', '请返回')
            return err.get_html()
    for user in users:
        if user.username == username:
            page = f"<h1>{username}的个人信息</h1>"
            page += f"<p>姓名：{user.name}</p>"
            page += f"<p>学号：{user.id}</p>"
            user_page = user.schedule.to_html()
            class_names = class_name_list()
            page += f'<a href="/user/{username}/load_course">从教务系统导入课表</a>'
            page += f"<h2>{username}的个人课表</h2>" + user_page
            page += f'''
            <form method="post">
                <textarea name="raw" id="raw" rows="10" cols="50" class="input-item" placeholder="请粘贴从教务系统直接copy的课表,从'周次/节次'那里开始到第十二节课结束,选全就行"></textarea><br>
                <button type="submit" class="btn">全局更新课表</button><br><br><br><br><br>
            </form>'''
            html = Html_index(user, class_names, page)
            return html.get_html()
    else:
        err = Html_Error(f'未找到用户:{username}', '请返回')
        return err.get_html()
    

@app.route('/user/<username>/load_course', methods=['GET', 'POST'])
def load_course(username):
    # 获取原始请求的URL
    url = request.args.get('http://219.216.96.4/eams/homeExt.action')

    # 向web服务发送代理请求
    response = rq.request(
        method=request.method,
        url=url,
        headers=request.headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )

    # 构造代理响应
    proxy_response = Response(
        response.content,
        status=response.status_code,
        headers=dict(response.headers)
    )

    return proxy_response
    

@app.route('/user/delete_course', methods=['GET'])
def delete_course():
    # 从查询参数中获取值
    course_id = request.args.get('id')
    course_name = request.args.get('name')
    course_teacher = request.args.get('teacher')
    course_time = request.args.get('time')
    for user in users:
        if user.username == session['username']:
            user.schedule.delete_course(course_id, course_name, course_teacher, course_time)
            save_files()
            return redirect(f'/user/{session["username"]}')
    else:
        err = Html_Error(f'未找到用户:{session["username"]}', '请返回')
        return err.get_html()
    

@app.route('/user/add_course', methods=['POST'])
def add_course():
    w = request.form['week']
    d = request.form['weekday']
    n = request.form['number']
    id = request.form['id']
    name = request.form['name']
    teacher = request.form['teacher']
    location = request.form['location']
    for user in users:
        if user.username == session['username']:
            user.schedule.add_course(w, d, n, id, name, teacher, location)
            save_files()
    return redirect(f'/user/{session["username"]}')


@app.route('/logout')
def logout():
    global current_users
    current_users.pop(session['username'])
    session.pop('username')
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session['username'] = username
        global current_users, users
        if users != []:
            for user in users:
                if user.username == username and user.password == password:
                    current_users[session['username']] = user
                    return redirect('/')
            else:
                session.pop('username')
                err = Html_Error('用户名或密码错误', '请检查用户名和密码是否正确')
                return err.get_html()
        return redirect('/register')
    else:
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        password = request.form['password']
        name = request.form['name']
        invaild_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invaild_chars:
            if char in username or char in password or char in name:
                err = Html_Error('用户名或密码或姓名包含非法字符', '请检查用户名或密码或姓名是否包含非法字符')
                return err.get_html()
        id = request.form['id']
        raw_schedule = request.form['schedule']
        schedule = Schedule(raw_schedule)
        user = Person(name, id)
        user.register(username, password, schedule)
        global current_users, users
        current_users[session['username']] = user
        for u in users:
            if u.username == username:
                err = Html_Error('用户名已存在', '请更换用户名')
                return err.get_html()
            if u.name == name and u.id == id:
                users.remove(u)
                break
        users.append(user)
        save_files()
        return redirect('/')
    else:
        return render_template('register.html')


# 错误页面
@app.errorhandler(404)
def page_not_found(error):
    err = Html_Error('页面未找到,请返回首页', f'{error}')
    return err.get_html()


@app.errorhandler(Exception)
def handle_exception(e):
    err = Html_Error('服务器内部错误,请截图并联系管理员', f'{traceback.format_exc()}')
    return err.get_html()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=65506)
