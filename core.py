from init import db, redirect
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import re
import pandas as pd
from flask import render_template


class Person(db.Model):
    __tablename__ = "persons"

    id = db.Column(db.Integer, primary_key=True, unique=True)  # 这里设为整数
    name = db.Column(db.String(256))  # 设置长度为 256
    username = db.Column(db.String(256), unique=True)  # 设置长度为 256
    password = db.Column(db.String(256))  # 设置长度为 256
    email = db.Column(db.String(256))  # 设置长度为 256
    ips = db.Column(db.Text)  # 以逗号分隔的 IP 地址字符串
    courses = db.Column(db.Text)  # 以逗号分隔的课程 ID 字符串
    classes = db.Column(db.Text)  # 以逗号分隔的班级 ID 字符串

    def login_ip(self, ip: str) -> None:
        warn = False
        if ", " in self.ips:
            self.ips = ip
            warn = True
        elif ip not in self.ips.split(", "):
            self.ips += f", {ip}"
            warn = True
        db.session.commit()
        return warn


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    name = db.Column(db.String(256))  # 设置长度为 256
    teacher = db.Column(db.String(256))  # 设置长度为 256
    courcations = db.Column(db.Text)  # 以逗号分隔的课程 ID 字符串

    def update(id: str, name: str, teacher: str, courcations: str) -> bool:
        course = Course.query.filter_by(id=id).first()
        if course is None:
            course = Course(id=id, name=name, teacher=teacher, courcations=courcations + ",")
            db.session.add(course)
        else:
            if course.name != name or course.teacher != teacher:
                return False
            course.courcations += courcations + ","
        db.session.commit()
        return True


class Courcation(db.Model):
    __tablename__ = "courcations"

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    location = db.Column(db.String(256))  # 设置长度为 256
    time_tables = db.Column(db.Text)  # 以逗号分隔的 (w, d, n) 元组(int, int, int) 字符串

    def update(id: str, location: str, time_tables: str) -> None:
        courcation = Courcation.query.filter_by(id=id).first()
        if courcation is None:
            courcation = Courcation(id=id, location=location, time_tables=time_tables)
            db.session.add(courcation)
        else:
            courcation.location = location
            courcation.time_tables = time_tables
        db.session.commit()


class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    name = db.Column(db.String(256))  # 设置长度为 256
    administrators = db.Column(db.Text)  # 以逗号分隔的管理员 ID 字符串
    students = db.Column(db.Text)  # 以逗号分隔的学生 ID 字符串
    notifications = db.Column(db.Text)  # 以逗号分隔的通知 ID 字符串


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    title = db.Column(db.String(256))  # 设置长度为 256
    content = db.Column(db.Text)  # 通知内容
    deadline = db.Column(db.DateTime)  # 截止日期
    confirmeds = db.Column(db.Text)  # 以逗号分隔的确认者 ID 字符串
    unconfirmeds = db.Column(db.Text)  # 以逗号分隔的未确认者 ID 字符串


class Html_index:
    def __init__(self, user: Person, main_area: str = "") -> None:
        self.user = user
        self.class_names = user.classes.split(", ") if user.classes is not None else []
        self.main_area = main_area

    def get_html(self) -> str:
        html = open("./templates/index.html", "r", encoding="utf-8").read()
        link = f'<a href="/user">{self.user.username}</a>'
        html = html.replace("<!--name-->", link)
        links = ""
        for class_name in self.class_names:
            links += f'<li>\n<button class="sidebar-button" onclick="location.href=\'/class/{class_name}\'">{class_name}</button>\n</li>\n'
        html = html.replace("<!--Class List-->", links)
        html = html.replace("<!--Content-->", self.main_area)
        return html

    def get_index_html(self) -> str:
        return self.get_html()

    def get_user_html(self) -> str:
        main_area = open("./templates/userinfo.html", "r", encoding="utf-8").read()
        main_area = main_area.replace("<!--username-->", self.user.username)
        self.main_area = main_area
        return self.get_html()


class Html_Error:
    def __init__(self, error: str, error_message: str) -> None:
        self.error = error
        self.error_message = error_message

    def get_html(self) -> str:
        html = open("./templates/Error.html", "r", encoding="utf-8").read()
        html = html.replace("<!--Err_title-->", self.error)
        html = html.replace("<!--Err_content-->", self.error_message)
        return html


def send_verify(to: str, name: str, verify_code: int):
    mail_info = open("data/mail_key", "r", encoding="utf-8").read().split("\n")
    from_addr = mail_info[0]
    password = mail_info[1]
    smtp_server = mail_info[2]

    head = "登录验证码"
    text = f"{name} 您好\n您的登录验证码为：{verify_code}\n登录成功后才会失效。\n切勿泄露给他人。"

    msg = MIMEText(text, "plain", "utf-8")

    # 邮件头信息
    msg["From"] = Header(from_addr)
    msg["To"] = Header(to)
    msg["Subject"] = Header(head)

    # 开启发信服务，这里使用的是加密传输
    server = smtplib.SMTP_SSL(smtp_server)
    server.connect(smtp_server, 465)
    server.login(from_addr, password)
    server.sendmail(from_addr, to, msg.as_string())
    server.quit()


def send_warning(to: str, name: str, ip: str):
    mail_info = open("data/mail_key", "r", encoding="utf-8").read().split("\n")
    from_addr = mail_info[0]
    password = mail_info[1]
    smtp_server = mail_info[2]
    users = ""
    all_people = Person.query.all()
    for person in all_people:
        if person.ips is not None:
            if ip in person.ips.split(", "):
                users += f"{person.name}({person.username})\n"

    head = "新地址登录警告"
    text = f"{name} 您好\n你的账户在 {ip} 登录，请注意安全。\n如非本人操作，请及时修改密码。\n其他从此ip登录的用户如下：\n{users}"

    msg = MIMEText(text, "plain", "utf-8")

    # 邮件头信息
    msg["From"] = Header(from_addr)
    msg["To"] = Header(to)
    msg["Subject"] = Header(head)

    # 开启发信服务，这里使用的是加密传输
    server = smtplib.SMTP_SSL(smtp_server)
    server.connect(smtp_server, 465)
    server.login(from_addr, password)
    server.sendmail(from_addr, to, msg.as_string())
    server.quit()


def is_valid_email(email: str) -> bool:
    """验证电子邮件格式是否合法。

    参数:
        email (str): 要验证的电子邮件地址。

    返回:
        bool: 如果电子邮件格式合法，返回 True；否则返回 False。
    """
    pattern = r"^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)*@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$"
    return re.match(pattern, email) is not None


def is_valid_username(username: str) -> bool:
    """验证用户名格式是否合法。
    用户名不能包含非法字符，特别是HTML和MySQL中可能被用于攻击的字符。

    参数:
        username (str): 要验证的用户名。

    返回:
        bool: 如果用户名格式合法，返回 True；否则返回 False。
    """
    # 定义非法字符
    illegal_characters = r"[<>'\";()&%$#@!\\\[\]{}=`~]+"

    # 检查是否包含非法字符
    if re.search(illegal_characters, username):
        return False

    # 检查合法字符范围（字母、数字、下划线、破折号和中文）
    pattern = r"^[\u4e00-\u9fa5a-zA-Z0-9_-]{1,20}$"

    return re.match(pattern, username) is not None


def is_valid_password(password: str) -> bool:
    """验证密码格式是否合法。
    长度：密码长度必须在8到20个字符之间。
    小写字母：密码必须至少包含一个小写字母（a-z）。
    大写字母：密码必须至少包含一个大写字母（A-Z）。
    数字：密码必须至少包含一个数字（0-9）。

    参数:
        password (str): 要验证的密码。

    返回:
        bool: 如果密码格式合法，返回 True；否则返回 False。
    """
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9_-]{8,20}$"
    return re.match(pattern, password) is not None


def parse_xls(file_content: str) -> str:
    """解析 Excel 文件内容。

    参数:
        file_content (str): Excel 文件内容。

    返回:

    """
    course_list = pd.read_html(file_content)[-2].values.tolist()
    course_ids = ""
    for n in range(6):
        for d in range(7):
            try:
                # print(course_list[2 * n][d + 1].strip(), d, n)
                course_ids += parse_course(course_list[2 * n][d + 1].strip(), d, n) + ","
            except AttributeError:
                pass
    print(course_ids)
    return course_ids


def parse_course(source_t: str, weekday: int, number: int) -> str:
    if len(source_t.split(")) ")) > 1:
        out = ""
        for t in source_t.split(")) ")[:-1]:
            out += parse_course((t + "))").strip(), weekday, number) + ","
        out += parse_course(source_t.split(")) ")[-1].strip(), weekday, number)
        return out
    string = source_t.strip()
    name = string.split(" ")[0]
    string = string.replace(name, "").strip()
    id = string.split(" ")[0]
    string = string.replace(id, "").strip()
    id = id.replace("(", "").replace(")", "")
    teacher = string.split(" ")[0]
    string = string.replace(teacher, "").strip()
    teacher = teacher.replace("(", "").replace(")", "")
    time = string.split(" ")[0].replace("(", "")
    weeks = []
    for weekp in time.split(","):
        if "-" in weekp and ("单" in weekp or "双" in weekp):
            for w in range(int(weekp.split("-")[0]), int(weekp.split("-")[1].split("单")[0].split("双")[0]) + 1, 2):
                weeks.append(w)
        elif "-" in weekp and "单" not in weekp and "双" not in weekp:
            for w in range(int(weekp.split("-")[0]), int(weekp.split("-")[1]) + 1):
                weeks.append(w)
        else:
            weeks.append(int(weekp))
    location = string.replace("(" + time + " ", "").strip()[:-1]
    print(name)
    print(id)
    print(teacher)
    print(weeks)
    print(location)
    courcation_id = id + location
    courcation_location = location
    courcation_time_tables = ""
    for week in weeks:
        courcation_time_tables += f"{week}|{weekday}|{number},"
    courcation_time_tables = courcation_time_tables[:-1]
    Courcation.update(courcation_id, courcation_location, courcation_time_tables)
    while not Course.update(id, name, teacher, courcation_id):
        id += "+"
    return id
