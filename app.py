from flask import Flask, render_template, session, redirect, url_for, request, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import random
from init import app, db
from core import Person, Html_Error, Html_index, send_verify, send_warning, is_valid_email, is_valid_username, is_valid_password
en_key = ''  # 加密密钥


# 加密函数
def generate_login_key(id):
    global en_key  # 导入加密密钥
    return str(id) + en_key  # 加密方式为 ID + 加密密钥


# 数据库初始化
def create_tables():
    db.create_all()


exec(open('data/en_key', 'r', encoding='utf-8').read())  # 导入加密密钥


# 定义根路由
@app.route('/')
def home():
    if 'id' in session:  # 如果已登录
        html = f'<h1>Welcome, {Person.query.filter_by(id=session["id"]).first().username}!</h1><a href="/logout">Logout</a>'
        return html
    else:
        return redirect('/login')  # 否则重定向到登录页面
    

# 图标路由
@app.route('/favicon.ico')
def favicon():
    return  send_from_directory('static/icon', 'favicon.ico') # 发送静态文件


# 用户登录示例
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        person = Person.query.filter_by(username=username, password=password).first()
        if person:  # 如果用户名和密码正确
            id = person.id  # 获取用户 ID
            key = generate_login_key(id)  # 生成登录密钥
            resp = make_response(redirect('/'))  # 重定向到主页
            resp.set_cookie('id', str(id), max_age=60*60*24*3)  # 设置登录 ID 作为 cookie
            resp.set_cookie('key', key, max_age=60*60*24*3)  # 设置登录密钥作为 cookie
            login_ip = request.remote_addr  # 获取登录 IP 地址
            if person.login_ip(login_ip):
                send_warning(person.email, person.name, login_ip)  # 发送警告邮件
            session['id'] = id  # 将用户 ID 存储在会话中
            return resp
        else:
            err = Html_Error('用户名或密码错误', '用户名或密码错误<a href="/login">返回登录</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面

    try:
        id = request.cookies.get('id')  # 从 URL 中获取用户 ID
        key = request.cookies.get('key')  # 从 URL 中获取登录密钥
        if generate_login_key(id) == key:  # 如果登录密钥正确
            session['id'] = id  # 将用户 ID 存储在会话中
            ips = Person.query.filter_by(id=id).first().ips
            if request.remote_addr in ips.split(', '):  # 如果登录 IP 地址在 IP 地址列表中
                return redirect('/')  # 重定向到主页
    except:
        pass  # 忽略错误
    return render_template('login.html')  # 渲染登录页面


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        person = Person.query.filter_by(id=id, name=name).first()
        if not person:
            err = Html_Error('用户不存在', '用户不存在<a href="/login">返回登录</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        random_code = str(random.randint(100000, 999999))  # 生成随机验证码
        session['verify_code'] = random_code  # 将验证码存储在会话中
        session['id'] = id  # 将用户 ID 存储在会话中
        send_verify(person.email, person.name, random_code)  # 发送验证码邮件
        return redirect('/reset2')  # 重定向到重置密码页面 2
    else:
        return render_template('reset.html')  # 渲染重置密码页面 1


# 重置密码页面 2
@app.route('/reset2', methods=['GET', 'POST'])
def reset2():
    if request.method == 'POST':
        verify_code = request.form['verify-code']
        username = request.form['username']
        password = request.form['password']
        if is_valid_username(username) and is_valid_password(password):  # 如果用户名和密码有效
            pass
        else:
            err = Html_Error('用户名或密码非法', '用户名只能包含字母（大小写都可以）、数字、下划线（_）和减号（-）<br />,密码长度必须在8到20个字符之间,需要也只能包含大小写字母和数字')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        if verify_code == session['verify_code']:  # 如果验证码正确
            id = session['id']
            person = Person.query.filter_by(id=id).first()
            person.username = username  # 更新用户名
            person.password = password  # 更新密码
            db.session.commit()  # 提交数据库更改
            session.pop('verify_code', None)  # 从会话中移除验证码
            person.ips = ''  # 清空 IP 地址列表
            db.session.commit()  # 提交数据库更改
            return redirect('/login')  # 重定向到登录页面
        else:
            err = Html_Error('验证码错误', '验证码错误<a href="/reset_password">返回重置密码</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
    else:
        return render_template('reset2.html')  # 渲染重置密码页面 2


# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        email = request.form['email']
        session['id'] = id  # 将用户 ID 存储在会话中
        session['name'] = name  # 将用户姓名存储在会话中
        session['email'] = email  # 将用户邮箱存储在会话中
        if not is_valid_email(email):  # 如果邮箱不合法
            err = Html_Error('邮箱格式错误', '邮箱格式错误<a href="/register">返回注册</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        person = Person.query.filter_by(id=id).first()  # 查询用户是否已注册
        if person:  # 如果已注册
            err = Html_Error('用户已注册', '用户已注册<a href="/login">返回登录</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        person = Person.query.filter_by(email=email).first()  # 查询邮箱是否已注册
        if person:  # 如果已注册
            err = Html_Error('邮箱已注册', '邮箱已注册<a href="/login">返回登录</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        random_code = str(random.randint(100000, 999999))  # 生成随机验证码
        session['verify_code'] = random_code  # 将验证码存储在会话中
        send_verify(email, name, random_code)  # 发送验证码邮件
        return redirect('/register2')  # 重定向到注册页面 2
    else:
        return render_template('register.html')  # 渲染注册页面 1
    

# 用户注册页面 2
@app.route('/register2', methods=['GET', 'POST'])
def register2():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if is_valid_username(username) and is_valid_password(password):  # 如果用户名和密码有效
            pass
        else:
            err = Html_Error('用户名或密码非法', '用户名只能包含字母（大小写都可以）、数字、下划线（_）和减号（-）<br />,密码长度必须在8到20个字符之间,需要也只能包含大小写字母和数字<br /><a href="/register2">返回注册</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        verify_code = request.form['verify-code']
        if verify_code == session['verify_code']:  # 如果验证码正确
            person = Person(id=session['id'], name=session['name'], username=username, password=password, email=session['email'], ips='')  # 创建用户对象
            db.session.add(person)  # 添加到数据库
            db.session.commit()  # 提交数据库更改
            session.pop('verify_code', None)  # 从会话中移除验证码
            return redirect('/login')  # 重定向到登录页面
        else:
            err = Html_Error('验证码错误', '验证码错误<a href="/register2">返回注册</a>')  # 显示错误信息
            return err.get_html()  # 显示错误信息
    else:
        return render_template('register2.html')  # 渲染注册页面 2


# 用户注销
@app.route('/logout')
def logout():
    if 'id' in session:  # 如果已登录
        session.pop('id', None)  # 从会话中移除用户 ID
        session.pop('name', None)  # 从会话中移除用户姓名
        session.pop('email', None)  # 从会话中移除用户邮箱
        session.pop('verify_code', None)  # 从会话中移除验证码
        session.pop('username', None)  # 从会话中移除用户名

        resp = make_response(redirect('/'))  # 创建响应对象并重定向到主页
        resp.set_cookie('id', '', expires=0)  # 清除登录 ID 作为 cookie
        resp.set_cookie('key', '', expires=0)  # 清除登录密钥作为 cookie

    return resp  # 返回修改后的响应对象



if __name__ == '__main__':
    with app.app_context():  # 确保在应用上下文中运行
        create_tables()  # 创建数据库
    app.run(host='0.0.0.0', port=65506, debug=True)