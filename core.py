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

    def format_courses(self) -> str:
        full = []
        if self.courses is None:
            return ""
        for course_id in self.courses.split(",")[:-1]:
            course = Course.query.filter_by(id=course_id).first()
            if course is None:
                raise Exception("数据库冲突，请联系管理员")
            if len(full) == 0:
                full = course.format_course()
            else:
                full = merge_list(full, course.format_course())
        widget = ""
        for w in range(20):
            widget += "第" + str(w + 1) + "周<br />" + '<table border="1">'
            widget += '<tr><th width="14.2857142857%">星期日</th><th width="14.2857142857%">星期一</th><th width="14.2857142857%">星期二</th><th width="14.2857142857%">星期三</th><th width="14.2857142857%">星期四</th><th width="14.2857142857%">星期五</th><th width="14.2857142857%">星期六</th></tr>'

            for n in range(6):
                widget += '<tr height="50px">'
                for d in range(7):
                    widget += "<td>"
                    if full[w][d][n] == "":
                        widget += f"""
                                    <form action="/user/add_course" method="post">
                                        <input class="class-input" type="hidden" name="week" value="{w}">
                                        <input class="class-input" type="hidden" name="weekday" value="{d}">
                                        <input class="class-input" type="hidden" name="number" value="{n}">
                                        <input class="class-input" type="text" name="id" placeholder="课程id">
                                        <input class="class-input" type="text" name="name" placeholder="课程名">
                                        <input class="class-input" type="text" name="teacher" placeholder="教师">
                                        <input class="class-input" type="text" name="location" placeholder="上课地点">
                                        <br />
                                        <input class="class-btn" type="submit" value="添加">
                                    </form>
                                """
                    else:
                        widget += f"{full[w][d][n]}"
                        widget += f'<br /><button class="class-delete-btn" onclick="window.location.href=\'/user/delete_course?id={self.id}&course_id={full[w][d][n]}\';">删除</a>'
                    widget += "</td>"
                widget += "</tr>"
            widget += "</table><br />"
        replace_dict = {}
        for course_id in self.courses.split(",")[:-1]:
            course = Course.query.filter_by(id=course_id).first()
            replace_dict[course_id] = course.name + "<br />" + course.teacher + "<br />"
        for key, value in replace_dict.items():
            widget = widget.replace(key, value)
        return widget


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
            if courcations not in course.courcations.split(","):
                course.courcations += courcations + ","
        db.session.commit()
        return True

    def format_course(self) -> list:
        out = []
        for courcation_id in self.courcations.split(",")[:-1]:
            courcation = Courcation.query.filter_by(id=courcation_id).first()
            if courcation is None:
                continue
            if len(out) == 0:
                out = courcation.format_courcation()
            else:
                out = merge_list(out, courcation.format_courcation())
        return out


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

    def format_courcation(self) -> list:
        out = [[[""] * 6 for _ in range(7)] for _ in range(20)]
        times = self.time_tables.split(",")
        for w in range(20):
            for d in range(7):
                for n in range(6):
                    time = f"{w}|{d}|{n}"
                    if time in times:
                        out[w][d][n] = f"{self.id}"
        return out


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
        main_area = main_area.replace("<!--table-->", self.user.format_courses())
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
    ids = ""
    for course_id in course_ids.split(",")[:-1]:
        if course_id in ids.split(","):
            continue
        ids += course_id + ","
    return ids


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
                weeks.append(w - 1)
        elif "-" in weekp and "单" not in weekp and "双" not in weekp:
            for w in range(int(weekp.split("-")[0]), int(weekp.split("-")[1]) + 1):
                weeks.append(w - 1)
        else:
            weeks.append(int(weekp) - 1)
    location = string.replace("(" + time + " ", "").strip()[:-1]
    # print(name)
    # print(id)
    # print(teacher)
    # print(weeks)
    # print(location)
    courcation_id = id + location
    courcation_location = location
    Courcation.query.filter_by(id=courcation_id).first()
    if Courcation.query.filter_by(id=courcation_id).first() is None:
        courcation_time_tables = ""
    else:
        courcation_time_tables = Courcation.query.filter_by(id=courcation_id).first().time_tables
    for week in weeks:
        courcation_time_tables += f"{week}|{weekday}|{number},"
    courcation_time_tables = courcation_time_tables
    Courcation.update(courcation_id, courcation_location, courcation_time_tables)
    while not Course.update(id, name, teacher, courcation_id):
        id += "+"
    return id


def merge_list(*lists) -> list:
    """合并多个整数维度列表。
    0维列表就是元素相加"""
    if not isinstance(lists[0], list):
        out = lists[0]
        for l in lists[1:]:
            if out is None:
                out = l
            else:
                out += l
        return out
    out = []
    length = -1
    for l in lists:
        if len(l) != length and length != -1:
            raise ValueError("列表长度不一致")
        length = len(l)
        if len(out) == 0:
            out = [None for _ in range(length)]
        for n, item in enumerate(l):
            out[n] = merge_list(out[n], item)
    return out
