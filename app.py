from flask import Flask, send_file, jsonify, render_template, session, redirect, url_for, request, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import random
from init import app, db
from core import Person, Class, Notification, Html_Error, Html_index, send_verify, send_warning, is_valid_email, is_valid_username, is_valid_password, parse_xls, is_valid_input_str, recursive_remove
import traceback
import os
from time import sleep
from functools import wraps
import datetime

en_key = ""  # 加密密钥


# 加密函数
def generate_login_key(id):
    global en_key  # 导入加密密钥
    return str(id) + en_key  # 加密方式为 ID + 加密密钥


# 数据库初始化
def create_tables():
    db.create_all()


exec(open("data/en_key", "r", encoding="utf-8").read())  # 导入加密密钥


def if_login(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 验证合法性
        id = request.cookies.get("id")  # 从 URL 中获取用户 ID
        key = request.cookies.get("key")  # 从 URL 中获取登录密钥
        if not id or not key:
            return redirect("/login")  # 重定向到登录页面
        if generate_login_key(id) != key:  # 如果登录密钥不正确
            return redirect("/login")  # 重定向到登录页面
        if "id" not in session:  # 如果用户未登录
            return redirect("/login")  # 重定向到登录页面
        if session["id"] != id:  # 如果用户 ID 不匹配
            return redirect("/login")  # 重定向到登录页面
        if Person.query.filter_by(id=id).first() is None:  # 如果用户不存在
            return redirect("/login")  # 重定向到登录页面
        if request.cookies.get("pass_key"):  # 如果存在密码重置密钥
            return redirect("/login")  # 重定向到密码重置页面
        # 验证完了
        return func(*args, **kwargs)  # 调用被修饰的函数

    return decorated_function


# 定义根路由
@app.route("/")
@if_login
def home():
    for class_ in Class.query.all():  # 更新课程信息
        class_.sync_to_people()
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    html = Html_index(people)
    return html.get_index_html()  # 返回主页


@app.route("/class/<int:class_id>", methods=["GET", "POST"])
@if_login
def class_page(class_id):
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    class_ = Class.query.filter_by(id=class_id).first()  # 获取课程信息
    if not class_:
        err = Html_Error("课程不存在", f"课程{class_id}不存在")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    class_.sync_to_people()
    if request.method == "POST":
        students = request.form["students"].split("\r\n")
        admins = request.form["admins"].split("\r\n")
        class_.update_members(admins, students)
    return class_.methods_page(people)  # 返回课程页面


@app.route("/class/<class_id>/confirm/<notification_id>", methods=["POST"])
@if_login
def confirm_notification(class_id, notification_id):
    notification = Notification.query.filter_by(id=notification_id).first()  # 获取通知信息
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    class_ = Class.query.filter_by(id=class_id).first()  # 获取课程信息
    if str(people.id) not in class_.students.split(",") + class_.administrators.split(","):
        return jsonify({"message": "你没有权限确认通知"})
    if class_id != str(class_.id):
        return jsonify({"message": "通知与课程不匹配"})
    notification.confirm(people)
    return jsonify({"message": "success"})


@app.route("/class/<class_id>/disconfirm/<notification_id>", methods=["POST"])
@if_login
def disconfirm_notification(class_id, notification_id):
    notification = Notification.query.filter_by(id=notification_id).first()  # 获取通知信息
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    class_ = Class.query.filter_by(id=class_id).first()  # 获取课程信息
    if str(people.id) not in class_.students.split(",") + class_.administrators.split(","):
        return jsonify({"message": "你没有权限取消确认通知"})
    if class_id != str(class_.id):
        return jsonify({"message": "通知与课程不匹配"})
    notification.disconfirm(people)
    return jsonify({"message": "success"})


@app.route("/class/<int:class_id>/schedule")
@if_login
def class_schedule(class_id):
    class_ = Class.query.filter_by(id=class_id).first()  # 获取课程信息
    if not class_:
        err = Html_Error("课程不存在", "课程不存在")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    if str(people.id) in class_.administrators.split(","):
        widget = class_.schedule_name()
    elif str(people.id) in class_.students.split(","):
        widget = class_.schedule_count()
    else:
        err = Html_Error("权限不足", "你没有权限查看课程时间表")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    widget += "<script>"
    widget += open("static/js/fill_color.js", "r", encoding="utf-8").read().replace("<!--total-->", str(len(class_.students.split(",")) + len(class_.administrators.split(","))))
    widget += "</script>"
    html = Html_index(people, widget)
    return html.get_html()  # 返回课程时间表页面


@app.route("/class/<int:class_id>/dismiss")
@if_login
def class_dismiss(class_id):
    class_ = Class.query.filter_by(id=class_id).first()  # 获取课程信息
    if not class_:
        err = Html_Error("课程不存在", "课程不存在")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    if str(people.id) in class_.administrators.split(","):
        class_.dismiss()
        return redirect("/")
    else:
        err = Html_Error("权限不足", "你没有权限删除课程")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面


@app.route("/class/<int:class_id>/write_notification", methods=["GET", "POST"])
@if_login
def class_write_notification(class_id):
    class_ = Class.query.filter_by(id=class_id).first()  # 获取课程信息
    if not class_:
        err = Html_Error("课程不存在", "课程不存在")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        deadline = request.form["deadline"]
        need_confirm = request.form.get("need_confirm", "off") == "on"
        need_submit = request.form.get("need_submit", "off") == "on"
        if need_confirm:
            unconfirmeds = class_.students + "," + class_.administrators
            confirmeds = ""
        else:
            unconfirmeds = ""
            confirmeds = class_.students + "," + class_.administrators
        if need_submit:
            file_path = os.path.join("data", "submissions", str(random.randint(100000, 999999)))
            os.makedirs(file_path, exist_ok=True)
        else:
            file_path = "no_file_path"
        Notification.new(title, content, deadline, confirmeds, unconfirmeds, file_path, class_.id)
        db.session.commit()
        return redirect("/class/" + str(class_id))  # 重定向到课程页面
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    widget = open("templates/write_notification.html", "r", encoding="utf-8").read()
    html = Html_index(people, widget)
    return html.get_html()  # 返回主页


@app.route("/submit/<int:passkey>", methods=["GET", "POST"])
@if_login
def submit(passkey):
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    if request.method == "POST":
        file = request.files["file"]
        if not file:
            err = Html_Error("文件为空", "请选择文件")  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        file_path = os.path.join("data", "submissions", str(passkey))
        if not os.path.exists(file_path):
            err = Html_Error("提交失败", "提交链接已失效")  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        file_name = file.filename
        file_path = os.path.join(file_path, people.name + "_" + str(people.id) + "_" + file_name)
        file.save(file_path)
        return """
                    文件上传成功
                    <script>
                        setTimeout(function() {
                            window.location.href = "/";
                        }, 2000);
                    </script>
                """
    else:
        widget = open("templates/submit.html", "r", encoding="utf-8").read()
        html = Html_index(people, widget)
        return html.get_html()  # 返回提交页面


@app.route("/file_submit/<path:file_dir>/<id>", methods=["GET", "POST"])
@if_login
def file_submit(file_dir, id):
    file_dir += "/" + id
    notification = Notification.query.filter_by(file_path=file_dir).first()  # 获取通知信息
    if notification:
        deadline = notification.deadline
        if deadline and deadline < datetime.datetime.now():
            err = Html_Error("提交失败", "提交截止时间已过")  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
    person = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    if not os.path.exists(file_dir):
        err = Html_Error("非法文件路径", "不要随意访问文件")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    if file_dir.split("/")[1] != "submissions":
        err = Html_Error("非法文件路径", "不要随意访问文件")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    if request.method == "POST":
        file = request.files["file"]
        file.save(file_dir + "/" + person.name + "_" + str(person.id) + "_-_" + file.filename)
        return redirect("/")
    widget = open("templates/submit_files.html", "r", encoding="utf-8").read()
    html = Html_index(person, widget)
    return html.get_html()  # 返回文件提交页面


@app.route("/download_file_from_notification/<notification_id>")
@if_login
def download_file_from_notification(notification_id):
    notification = Notification.query.filter_by(id=notification_id).first()  # 获取通知信息
    if not notification:
        err = Html_Error("通知不存在", "通知不存在")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    class_ = Class.query.filter_by(id=notification.class_id).first()  # 获取课程信息
    if not class_:
        err = Html_Error("课程不存在", "课程不存在")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    if str(session["id"]) not in class_.administrators.split(","):
        err = Html_Error("权限不足", "你没有权限下载文件")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    if not os.path.exists(notification.file_path):
        err = Html_Error("文件不存在", "请重新投放通知")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    file_dir = notification.file_path

    # 定义压缩包的名称
    zip_file_name = f"{class_.name}_{notification.title}.zip"  # 这里可以自定义为你想要的名称
    zip_file_path = os.path.join(file_dir, zip_file_name)  # 将 ZIP 文件保存在 file_dir 的同一目录下

    # 如果压缩包已经存在，先删除它
    try:
        os.remove(zip_file_path)
    except FileNotFoundError:
        pass

    files = os.listdir(file_dir)
    if len(files) == 0:
        err = Html_Error("文件为空", "没有人提交文件")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面

    import shutil

    # 压缩文件夹
    shutil.make_archive(os.path.splitext(zip_file_path)[0], "zip", file_dir)

    # 创建响应并发送 ZIP 文件
    response = send_file(zip_file_path, as_attachment=True)
    response.headers["Content-Disposition"] = "attachment; filename=" + os.path.basename(zip_file_path)
    return response


@app.route("/class/<class_id>/delete_notification/<notification_id>")
@if_login
def delete_notification(class_id, notification_id):
    class_ = Class.query.filter_by(id=class_id).first()  # 获取课程信息
    if not class_:
        err = Html_Error("课程不存在", "课程不存在")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    notification = Notification.query.filter_by(id=notification_id).first()  # 获取通知信息
    if not notification:
        err = Html_Error("通知不存在", "通知不存在")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    if str(notification.class_id) != str(class_id):
        err = Html_Error("通知与课程不匹配", "通知与课程不匹配")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    if str(session["id"]) not in class_.administrators.split(","):
        err = Html_Error("权限不足", "你没有权限删除通知")  # 显示错误信息
        return err.get_html()  # 返回错误信息页面
    recursive_remove(notification.file_path)
    db.session.delete(notification)
    db.session.commit()
    return redirect("/class/" + str(class_id))  # 重定向到课程页面


@app.route("/create_class", methods=["GET", "POST"])
@if_login
def create_class():
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    if request.method == "POST":
        class_name = request.form["class_name"]
        members = request.form["members"]
        administrators = request.form["administrators"]
        if is_valid_input_str(class_name) and is_valid_input_str(members) and is_valid_input_str(administrators):
            pass
        else:
            err = Html_Error("输入错误", '含有非法字符<a href="/create_class">返回创建课程</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        if not class_name:
            err = Html_Error("不能为空", '课程名称不能为空<a href="/create_class">返回创建课程</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        class_id = random.randint(100000, 999999)  # 生成随机课程 ID
        while Class.query.filter_by(id=class_id).first():  # 防止 ID 重复
            class_id = class_id + 1
        try:
            class_administrators = [int(people.id)]
            class_members = []
            if administrators != "":
                for i in administrators.split("\n"):
                    if int(i) not in class_administrators:
                        class_administrators.append(int(i))
            if members != "":
                for i in members.split("\n"):
                    if int(i) not in class_members and int(i) not in class_administrators:
                        class_members.append(int(i))
        except ValueError:
            err = Html_Error("输入错误", '请输入正确的学号，并用换行分隔不同学号<a href="/create_class">返回创建课程</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        Class.new(class_id, class_name, class_administrators, class_members)
        return redirect("/class/" + str(class_id))  # 重定向到课程页面
    widget = open("templates/create_class.html", "r", encoding="utf-8").read()
    html = Html_index(people, widget)
    return html.get_html()  # 返回创建课程页面


# 反馈页面
@app.route("/feedback", methods=["GET", "POST"])
@if_login
def feedback():
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    if request.method == "POST":
        content = request.form["content"]
        if not content:
            err = Html_Error("内容不能为空", '内容不能为空<a href="/feedback">返回反馈</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        with open("data/feedback.txt", "a", encoding="utf-8") as f:
            f.write(people.username + ":" + people.name + ":" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ":" + content + "\n")  # 写入文件
        return redirect("/")
    else:
        page = """<form method="post" class="feedback-form"><textarea class="feedback-input" type="text" name="content" placeholder="请输入反馈内容"></textarea>
        <button type="submit" class="btn">提交</button><form>"""
        html = Html_index(people, page)
        return html.get_html()  # 返回反馈页面


# 个人信息
@app.route("/user", methods=["GET", "POST"])
@if_login
def user():
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    html = Html_index(people)
    return html.get_user_html()  # 返回个人信息页面


@app.route("/update_schedule", methods=["GET", "POST"])
@if_login
def update_schedule():
    people = Person.query.filter_by(id=session["id"]).first()  # 获取用户信息
    if request.method == "POST":
        ALLOWED_EXTENSIONS = ["xls"]
        file = request.files["file"]
        if file and "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS:
            file = file.read()
            try:
                content = file.decode("utf-8")
                # people.courses = parse_xls(content, False)
                err = Html_Error("文件选择错误", "请在教务处网页课表的右上角先选择打印,再选择导出.<br />(如果先选择导出,则无法进行解析)")
                return err.get_html()  # 返回错误信息页面
            except UnicodeDecodeError:
                content = file.decode("gbk")
                people.courses = parse_xls(content, True)
            db.session.commit()  # 提交数据库更改
            return redirect("/user")  # 重定向到个人信息页面
        else:
            err = Html_Error("??!", "请上传xls格式的文件,你的信息将不会被保存.")
            return err.get_html()
    widget = open("templates/upload.html", "r", encoding="utf-8").read()
    html = Html_index(people, widget)
    return html.get_html()


@app.route("/test", methods=["GET", "POST"])
def test():
    return render_template("index2.html")


# 图标路由
@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static/icon", "favicon.ico")  # 发送静态文件


# 用户登录
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        person = Person.query.filter_by(username=username, password=password).first()
        if person:  # 如果用户名和密码正确
            id = person.id  # 获取用户 ID
            key = generate_login_key(id)  # 生成登录密钥
            resp = make_response(redirect("/"))  # 重定向到主页
            resp.set_cookie("id", str(id), max_age=60 * 60 * 24 * 3)  # 设置登录 ID 作为 cookie
            resp.set_cookie("key", key, max_age=60 * 60 * 24 * 3)  # 设置登录密钥作为 cookie
            login_ip = request.remote_addr  # 获取登录 IP 地址
            if person.login_ip(login_ip):
                send_warning(person.email, person.name, login_ip)  # 发送警告邮件
            session["id"] = id  # 将用户 ID 存储在会话中
            return resp
        else:
            err = Html_Error("用户名或密码错误", '用户名或密码错误,或者还没有注册账户<br /><a href="/register">前往注册</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面

    try:
        id = request.cookies.get("id")  # 从 URL 中获取用户 ID
        key = request.cookies.get("key")  # 从 URL 中获取登录密钥
        pass_key = request.cookies.get("pass_key")  # 从 URL 中获取密码重置密钥
        if pass_key:  # 如果存在密码重置密钥
            err = Html_Error("啥?", "请不要手动跳转url嗷")  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        if generate_login_key(id) == key:  # 如果登录密钥正确
            session["id"] = id  # 将用户 ID 存储在会话中
            ips = Person.query.filter_by(id=id).first().ips
            if request.remote_addr in ips.split(","):  # 如果登录 IP 地址在 IP 地址列表中
                return redirect("/")  # 重定向到主页
    except Exception:
        pass  # 忽略错误
    return render_template("login.html")  # 渲染登录页面


@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        id = request.form["id"]
        name = request.form["name"]
        person = Person.query.filter_by(id=id, name=name).first()
        if not person:
            err = Html_Error("用户不存在", '用户不存在<a href="/login">返回登录</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        random_code = str(random.randint(100000, 999999))  # 生成随机验证码
        session["verify_code"] = random_code  # 将验证码存储在会话中
        session["id"] = id  # 将用户 ID 存储在会话中
        send_verify(person.email, person.name, random_code)  # 发送验证码邮件
        return redirect("/reset2")  # 重定向到重置密码页面 2
    else:
        if "id" in session or request.cookies.get("pass_key"):  # 如果已登录
            return redirect("/login")  # 重定向到登录页面
        else:
            return render_template("reset.html")  # 渲染重置密码页面 1


# 重置密码页面 2
@app.route("/reset2", methods=["GET", "POST"])
def reset2():
    if request.method == "POST":
        verify_code = request.form["verify-code"]
        username = request.form["username"]
        password = request.form["password"]
        if is_valid_username(username) and is_valid_password(password):  # 如果用户名和密码有效
            pass
        else:
            err = Html_Error("用户名或密码非法", '用户名只能包含字母（大小写都可以）、数字、下划线（_）和减号（-）<br />密码长度必须在8到20个字符之间,必须也只能包含大小写字母和数字<br /><a href="/reset2">重新输入用户名和密码</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        if verify_code == session["verify_code"]:  # 如果验证码正确
            id = session["id"]
            person = Person.query.filter_by(id=id).first()
            person.username = username  # 更新用户名
            person.password = password  # 更新密码
            session.pop("verify_code", None)  # 从会话中移除验证码
            person.ips = ""  # 清空 IP 地址列表
            db.session.commit()  # 提交数据库更改
            key = generate_login_key(id)  # 生成登录密钥
            resp = make_response(redirect("/"))  # 重定向到主页
            resp.set_cookie("id", str(id), max_age=60 * 60 * 24 * 3)  # 设置登录 ID 作为 cookie
            resp.set_cookie("key", key, max_age=60 * 60 * 24 * 3)  # 设置登录密钥作为 cookie
            login_ip = request.remote_addr  # 获取登录 IP 地址
            if person.login_ip(login_ip):
                send_warning(person.email, person.name, login_ip)  # 发送警告邮件
            return resp
        else:
            err = Html_Error("验证码错误", '验证码错误<a href="/reset_password">返回重置密码</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
    else:
        if "id" in session and "verify_code" in session:  # 如果已登录
            return render_template("reset2.html")  # 渲染重置密码页面 2
        else:
            resp = make_response(redirect("/login"))  # 创建响应对象并重定向到登录页面
            resp.set_cookie("pass_key", str(random.randint(100000, 999999)), max_age=60 * 3)
            return resp  # 重定向到登录页面


# 用户注册
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        id = request.form["id"]
        name = request.form["name"]
        email = request.form["email"]
        session["id"] = id  # 将用户 ID 存储在会话中
        session["name"] = name  # 将用户姓名存储在会话中
        session["email"] = email  # 将用户邮箱存储在会话中
        if not is_valid_email(email):  # 如果邮箱不合法
            err = Html_Error("邮箱格式错误", '邮箱格式错误<a href="/register">返回注册</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        person = Person.query.filter_by(id=id).first()  # 查询用户是否已注册
        if person:  # 如果已注册
            err = Html_Error("用户已注册", '用户已注册<a href="/login">返回登录</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        person = Person.query.filter_by(email=email).first()  # 查询邮箱是否已注册
        if person:  # 如果已注册
            err = Html_Error("邮箱已注册", '邮箱已注册<a href="/login">返回登录</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        random_code = str(random.randint(100000, 999999))  # 生成随机验证码
        session["verify_code"] = random_code  # 将验证码存储在会话中
        send_verify(email, name, random_code)  # 发送验证码邮件
        return redirect("/register2")  # 重定向到注册页面 2
    else:
        if request.cookies.get("pass_key"):  # 如果已登录
            return redirect("/login")  # 重定向到登录页面
        else:
            return render_template("register.html")  # 渲染注册页面 1


# 用户注册页面 2
@app.route("/register2", methods=["GET", "POST"])
def register2():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if is_valid_username(username) and is_valid_password(password):  # 如果用户名和密码有效
            pass
        else:
            err = Html_Error("用户名或密码非法", '用户名只能包含字母（大小写都可以）、数字、下划线（_）和减号（-）<br />,密码长度必须在8到20个字符之间,必须也只能包含大小写字母和数字<br /><a href="/register2">重新输入用户名和密码</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面
        verify_code = request.form["verify-code"]
        if verify_code == session["verify_code"]:  # 如果验证码正确
            person = Person(id=session["id"], name=session["name"], username=username, password=password, email=session["email"], ips="")  # 创建用户对象
            db.session.add(person)  # 添加到数据库
            db.session.commit()  # 提交数据库更改
            session.pop("id", None)  # 从会话中移除用户 ID
            session.pop("name", None)  # 从会话中移除用户姓名
            session.pop("email", None)  # 从会话中移除用户邮箱
            session.pop("verify_code", None)  # 从会话中移除验证码
            key = generate_login_key(person.id)  # 生成登录密钥
            resp = make_response(redirect("/"))  # 重定向到主页
            resp.set_cookie("id", str(person.id), max_age=60 * 60 * 24 * 3)  # 设置登录 ID 作为 cookie
            resp.set_cookie("key", key, max_age=60 * 60 * 24 * 3)  # 设置登录密钥作为 cookie
            login_ip = request.remote_addr  # 获取登录 IP 地址
            if person.login_ip(login_ip):
                send_warning(person.email, person.name, login_ip)  # 发送警告邮件
            session["id"] = person.id  # 将用户 ID 存储在会话中
            return resp
        else:
            err = Html_Error("验证码错误", '验证码错误<a href="/register2">返回注册</a>')  # 显示错误信息
            return err.get_html()  # 显示错误信息
    else:
        if "id" in session and "name" in session and "email" in session and "verify_code" in session:  # 如果已登录
            return render_template("register2.html")  # 渲染注册页面 2
        else:
            resp = make_response(redirect("/login"))  # 创建响应对象并重定向到登录页面
            resp.set_cookie("pass_key", str(random.randint(100000, 999999)), max_age=60 * 3)
            return resp  # 重定向到登录页面


# 用户注销
@app.route("/logout")
@if_login
def logout():
    session.pop("id", None)  # 从会话中移除用户 ID
    session.pop("name", None)  # 从会话中移除用户姓名
    session.pop("email", None)  # 从会话中移除用户邮箱
    session.pop("verify_code", None)  # 从会话中移除验证码
    session.pop("username", None)  # 从会话中移除用户名
    resp = make_response(redirect("/"))  # 创建响应对象并重定向到主页
    resp.set_cookie("id", "", expires=0)  # 清除登录 ID 作为 cookie
    resp.set_cookie("key", "", expires=0)  # 清除登录密钥作为 cookie
    return resp  # 返回修改后的响应对象


# 删除账户
@app.route("/user/rm", methods=["GET", "POST"])
@if_login
def rm_user():
    if request.method == "POST":
        # 再验证合法性
        id = request.cookies.get("id")  # 从 URL 中获取用户 ID
        key = request.cookies.get("key")  # 从 URL 中获取登录密钥
        if not id or not key:
            return redirect("/login")  # 重定向到登录页面
        if generate_login_key(id) != key:  # 如果登录密钥不正确
            return redirect("/login")  # 重定向到登录页面
        if "id" not in session:  # 如果用户未登录
            return redirect("/login")  # 重定向到登录页面
        if session["id"] != id:  # 如果用户 ID 不匹配
            return redirect("/login")  # 重定向到登录页面
        if request.cookies.get("pass_key"):  # 如果存在密码重置密钥
            return redirect("/login")  # 重定向到密码重置页面
        # 验证完了
        Person.query.filter_by(id=id).delete()  # 删除用户
        for class_ in Class.query.all():  # 删除用户在所有班级中的记录
            if str(session["id"]) in class_.students:
                class_.students.replace(str(session["id"]) + ",", "").replace(str(session["id"]), "")
            elif str(session["id"]) in class_.administrators:
                class_.administrators.replace(str(session["id"]) + ",", "").replace(str(session["id"]), "")
            class_.unsynced_peoples += str(session["id"]) + ","
        # TODO: 删通知
        db.session.commit()  # 提交数据库更改
        session.pop("id", None)  # 从会话中移除用户 ID
        session.pop("name", None)  # 从会话中移除用户姓名
        session.pop("email", None)  # 从会话中移除用户邮箱
        session.pop("verify_code", None)  # 从会话中移除验证码
        session.pop("username", None)  # 从会话中移除用户名
        resp = make_response(redirect("/"))  # 创建响应对象并重定向到主页
        resp.set_cookie("id", "", expires=0)  # 清除登录 ID 作为 cookie
        resp.set_cookie("key", "", expires=0)  # 清除登录密钥作为 cookie
        return resp  # 返回修改后的响应对象
    else:
        err = Html_Error("确认删除账户吗？", '再问你一遍,确认删除账户吗？<form method="post"><input class="btn" type="submit" value="确认"></form>')  # 显示确认删除账户信息页面
        return err.get_html()  # 返回确认删除账户信息页面


@app.route("/about")
def about():
    return redirect("https://github.com/zpb911km/monitorTool")


@app.errorhandler(Exception)
def handle_error(e):
    # 使用traceback格式化错误信息
    tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
    for n, line in enumerate(tb_lines):
        if "web_server" in line:
            tb_lines = tb_lines[n:]
            break
        if "werkzeug" in line:
            tb_lines = [""]
    tb_message = "".join(tb_lines)  # 错误信息
    if "(535, b'Error: authentication failed')" == str(e):
        tb_message = "邮件授权到期,请联系管理员"
    tb_message = tb_message.replace("\n", "<br>")
    err = Html_Error(f"{type(e).__name__}", f"错误：{str(e)}<br>信息：<div>{tb_message}</div>")  # 显示错误信息
    return err.get_html()  # 返回错误信息页面


if __name__ == "__main__":
    with app.app_context():  # 确保在应用上下文中运行
        create_tables()  # 创建数据库
    app.run(host="0.0.0.0", port=65506, debug=True)
