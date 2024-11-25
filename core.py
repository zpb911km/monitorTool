from init import db, redirect
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import re
import pandas as pd
from flask import render_template
from datetime import datetime
import random


SPLITER = "(A"


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

    def raw_courses_name(self) -> list:
        full = []
        if self.courses is None:
            return ""
        for course_id in self.courses.split(",")[:-1]:
            course = Course.query.filter_by(id=course_id).first()
            if course is None:
                raise Exception("数据库冲突，请联系管理员")
            if len(full) == 0:
                full = course.raw_course()
            else:
                full = merge_list(full, course.raw_course())
        out = []
        for w in range(20):
            outd = []
            for d in range(7):
                outn = []
                for n in range(6):
                    if full[w][d][n] == "":
                        outn.append("")
                    else:
                        outn.append(self.name + "\n")
                outd.append(outn)
            out.append(outd)
        return out

    def raw_courses_count(self) -> list:
        full = []
        if self.courses is None:
            return ""
        for course_id in self.courses.split(",")[:-1]:
            course = Course.query.filter_by(id=course_id).first()
            if course is None:
                raise Exception("数据库冲突，请联系管理员")
            if len(full) == 0:
                full = course.raw_course()
            else:
                full = merge_list(full, course.raw_course())
        out = []
        for w in range(20):
            outd = []
            for d in range(7):
                outn = []
                for n in range(6):
                    if full[w][d][n] == "":
                        outn.append("")
                    else:
                        outn.append(str(len(full[w][d][n])))
                outd.append(outn)
            out.append(outd)
        return out

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
            widget += "第" + str(w + 1) + "周<br />" + '<table border="1" width="100%">'
            widget += '<tr><th width="14.2857142857%">星期日</th><th width="14.2857142857%">星期一</th><th width="14.2857142857%">星期二</th><th width="14.2857142857%">星期三</th><th width="14.2857142857%">星期四</th><th width="14.2857142857%">星期五</th><th width="14.2857142857%">星期六</th></tr>'

            for n in range(6):
                widget += '<tr height="50px">'
                for d in range(7):
                    widget += "<td>"
                    if full[w][d][n] == "":
                        widget += ""
                    else:
                        widget += f"{full[w][d][n]}"
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

    def clean_classes(self) -> None:
        if self.classes is None:
            return None
        ids = self.classes.split(",")
        id_useful = []
        for id in ids:
            class_ = Class.query.filter_by(id=id).first()
            if class_ is not None and id not in id_useful:
                id_useful.append(id)
        self.classes = ",".join(id_useful) + ","
        db.session.commit()


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
                if course.name != "" or course.teacher != "":
                    return False
            if courcations not in course.courcations.split(","):
                course.name = name
                course.teacher = teacher
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

    def raw_course(self) -> list:
        out = []
        for courcation_id in self.courcations.split(",")[:-1]:
            courcation = Courcation.query.filter_by(id=courcation_id).first()
            if courcation is None:
                continue
            if len(out) == 0:
                out = courcation.raw_courcation()
            else:
                out = merge_list(out, courcation.raw_courcation())
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

    def raw_courcation(self) -> list:
        out = [[[""] * 6 for _ in range(7)] for _ in range(20)]
        times = self.time_tables.split(",")
        for w in range(20):
            for d in range(7):
                for n in range(6):
                    time = f"{w}|{d}|{n}"
                    if time in times:
                        out[w][d][n] = "1"
        return out


class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.String(256), primary_key=True)  # 设置长度为 256
    name = db.Column(db.String(256))  # 设置长度为 256
    administrators = db.Column(db.Text)  # 以逗号分隔的管理员 ID 字符串
    students = db.Column(db.Text)  # 以逗号分隔的学生 ID 字符串
    unsynced_peoples = db.Column(db.Text)  # 以逗号分隔的未同步人员 ID 字符串

    def sync_to_people(self) -> None:
        ids = self.unsynced_peoples.split(",")
        id_done = []
        for id in ids:
            person = Person.query.filter_by(id=id).first()
            if person is None:
                continue
            else:
                if person.classes is None:
                    person.classes = f"{self.id},"
                else:
                    if self.id not in person.classes.split(","):
                        person.classes += f"{self.id},"
                id_done.append(id)
        for id in id_done:
            ids.remove(id)
        self.unsynced_peoples = ",".join(ids)
        for admin_id in self.administrators.split(","):
            if admin_id in self.students:
                self.students = self.students.replace(admin_id + ",", "").replace(admin_id, "")
        db.session.commit()

    def new(id: str, name: str, administrators: list[str], students: list[str]) -> bool:
        admins = ",".join([admin_in.split(" ")[1].strip() for admin_in in administrators if admin_in != ""])
        members = ",".join([member_in.split(" ")[1].strip() for member_in in students if member_in != ""])
        unsynced = []
        for admin in admins.split(","):
            person = Person.query.filter_by(username=admin).first()
            if person is not None:
                person.classes += f"{id},"
            else:
                unsynced.append(admin)
        for member in members.split(","):
            person = Person.query.filter_by(username=member).first()
            if person is not None:
                person.classes += f"{id},"
            else:
                unsynced.append(member)
        unsynced_peoples = ",".join(unsynced)
        class_ = Class(id=id, name=name, administrators=admins, students=members, unsynced_peoples=unsynced_peoples)
        class_.sync_to_people()
        db.session.add(class_)
        db.session.commit()
        return True

    def schedule_name(self) -> str:
        schedule = []
        for student_id in self.students.split(","):
            student = Person.query.filter_by(id=student_id).first()
            if student is None:
                continue
            if len(schedule) == 0:
                schedule = student.raw_courses_name()
            else:
                schedule = merge_list(schedule, student.raw_courses_name())
        for admin_id in self.administrators.split(","):
            admin = Person.query.filter_by(id=admin_id).first()
            if admin is None:
                continue
            if len(schedule) == 0:
                schedule = admin.raw_courses_name()
            else:
                schedule = merge_list(schedule, admin.raw_courses_name())
        widget = ""
        for w in range(20):
            widget += "第" + str(w + 1) + "周<br />" + '<table border="1" width="100%">'
            widget += '<tr><th width="14.2857142857%">星期日</th><th width="14.2857142857%">星期一</th><th width="14.2857142857%">星期二</th><th width="14.2857142857%">星期三</th><th width="14.2857142857%">星期四</th><th width="14.2857142857%">星期五</th><th width="14.2857142857%">星期六</th></tr>'

            for n in range(6):
                widget += '<tr height="50px">'
                for d in range(7):
                    widget += "<td>"
                    if schedule[w][d][n] == "":
                        widget += ""
                    else:
                        widget += f"{schedule[w][d][n]}".replace("\n", "<br />")
                    widget += "</td>"
                widget += "</tr>"
            widget += "</table><br />"
        return widget

    def schedule_count(self) -> str:
        schedule = []
        for student_id in self.students.split(","):
            student = Person.query.filter_by(id=student_id).first()
            if student is None:
                continue
            if len(schedule) == 0:
                schedule = student.raw_courses_count()
            else:
                schedule = merge_list(schedule, student.raw_courses_count())
        for admin_id in self.administrators.split(","):
            admin = Person.query.filter_by(id=admin_id).first()
            if admin is None:
                continue
            if len(schedule) == 0:
                schedule = admin.raw_courses_count()
            else:
                schedule = merge_list(schedule, admin.raw_courses_count())
        widget = ""
        for w in range(20):
            widget += "第" + str(w + 1) + "周<br />" + '<table border="1" width="100%">'
            widget += '<tr><th width="14.2857142857%">星期日</th><th width="14.2857142857%">星期一</th><th width="14.2857142857%">星期二</th><th width="14.2857142857%">星期三</th><th width="14.2857142857%">星期四</th><th width="14.2857142857%">星期五</th><th width="14.2857142857%">星期六</th></tr>'

            for n in range(6):
                widget += '<tr height="50px">'
                for d in range(7):
                    widget += "<td>"
                    if schedule[w][d][n] == "":
                        widget += ""
                    else:
                        widget += f"{len(schedule[w][d][n])}"
                    widget += "</td>"
                widget += "</tr>"
            widget += "</table><br />"
        return widget

    def methods_page(self, people: Person) -> str:
        if str(people.id) in self.administrators:
            widget = open("templates/class_admin.html", "r", encoding="utf-8").read()
            widget = widget.replace("<!--class_id-->", self.id)
            students = []
            for student_id in self.students.split(","):
                student = Person.query.filter_by(id=student_id).first()
                if student:
                    students.append(student.name + " " + str(student.id))
                else:
                    students.append(f"未登录 {student_id}")
            admins = []
            for admin_id in self.administrators.split(","):
                admin = Person.query.filter_by(id=admin_id).first()
                if admin:
                    admins.append(admin.name + " " + str(admin.id))
                else:
                    admins.append(f"未登录 {admin_id}")
            widget = widget.replace("<!--admins-->", "\n".join(admins))
            widget = widget.replace("<!--len_admins-->", str(len(admins) + 1))
            widget = widget.replace("<!--students-->", "\n".join(students))
            widget = widget.replace("<!--len_students-->", str(len(students) + 1))
            widget = widget.replace("<!--notifications-->", Notification.get_html_widget(class_=self, people=None))
            html = Html_index(people, widget)
            return html.get_html()  # 返回课程管理页面
        elif str(people.id) in self.students:
            widget = open("templates/class_stu.html", "r", encoding="utf-8").read()
            widget = widget.replace("<!--class_id-->", self.id)
            html = Html_index(people, widget)
            return html.get_html()  # 返回课程成员页面
        else:
            people.classes = people.classes.replace(str(self.id) + ",", "").replace(str(self.id), "")
            db.session.commit()
            err = Html_Error("无权限访问", '无权限访问<a href="/">返回主页</a>')  # 显示错误信息
            return err.get_html()  # 返回错误信息页面

    def update_members(self, administrators: list[str], students: list[str]) -> None:
        for admin in administrators:
            person = Person.query.filter_by(id=int(admin.split(" ")[1])).first()
            if person is not None:
                person.classes = person.classes.replace(self.id + ",", "").replace(self.id, "")
        for member in students:
            person = Person.query.filter_by(id=int(member.split(" ")[1])).first()
            if person is not None:
                person.classes = person.classes.replace(self.id + ",", "").replace(self.id, "")
        admins = ",".join([admin_in.split(" ")[1].strip() for admin_in in administrators if admin_in != ""])
        members = ",".join([member_in.split(" ")[1].strip() for member_in in students if member_in != ""])
        unsynced = []
        for admin in admins.split(","):
            person = Person.query.filter_by(id=int(admin)).first()
            if person is not None:
                if self.id not in person.classes.split(","):
                    person.classes += f"{self.id},"
            else:
                unsynced.append(admin)
        for member in members.split(","):
            person = Person.query.filter_by(id=int(member)).first()
            if person is not None:
                if self.id not in person.classes.split(","):
                    person.classes += f"{self.id},"
            else:
                unsynced.append(member)
        unsynced_peoples = ",".join(unsynced)
        self.administrators = admins
        self.students = members
        self.unsynced_peoples = unsynced_peoples
        self.sync_to_people()
        db.session.commit()

    def dismiss(self) -> None:
        for student_id in self.students.split(","):
            student = Person.query.filter_by(id=student_id).first()
            if student is not None:
                student.classes = student.classes.replace(self.id + ",", "").replace(self.id, "")
        for admin_id in self.administrators.split(","):
            admin = Person.query.filter_by(id=admin_id).first()
            if admin is not None:
                admin.classes = admin.classes.replace(self.id + ",", "").replace(self.id, "")
        db.session.delete(self)
        db.session.commit()


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)  # 设置长度为 256
    title = db.Column(db.String(256))  # 设置长度为 256
    content = db.Column(db.Text)  # 通知内容`   `
    deadline = db.Column(db.DateTime)  # 截止日期
    confirmeds = db.Column(db.Text)  # 以逗号分隔的确认者 ID 字符串
    unconfirmeds = db.Column(db.Text)  # 以逗号分隔的未确认者 ID 字符串
    file_path = db.Column(db.String(256))  # 文件路径
    class_id = db.Column(db.String(256), db.ForeignKey("classes.id", ondelete="CASCADE"))

    def new(title: str, content: str, deadline: datetime, confirmeds: str, unconfirmeds: str, file_path: str, class_id: str) -> str:
        id = random.randint(-2147483648, 2147483647)
        while Notification.query.filter_by(id=id).first() is not None:
            id += 1
        notification = Notification(id=id, title=title, content=content, deadline=deadline, confirmeds=confirmeds, unconfirmeds=unconfirmeds, file_path=file_path, class_id=class_id)
        db.session.add(notification)
        db.session.commit()
        return str(id)

    def get_html_widget(class_: Class, people: Person | None = None) -> str:
        notifications = Notification.query.filter_by(class_id=class_.id).all()
        widget = ""
        for notification in notifications:
            days = (notification.deadline - datetime.now()).days
            if days < 30 and days >= 0:
                color = display_color(1 - days / 30)
            elif days < 0:
                color = "#555555"
            else:
                color = "#FFFFFF"
            widget += f'<div style="margin-bottom: 20px; border: none; padding: 10px; border-radius: 5px; box-shadow: 10px 10px 10px {color}; background-color: #272733; margin: 20px;">\n'
            widget += "<h2>来自" + class_.name + "的通知:</h2>\n"
            widget += "<h3>" + notification.title + "</h3>\n"
            widget += "<p>" + notification.content.replace("\n", "<br>").replace("\r", "") + "</p>\n"
            widget += "<p>截止时间：" + notification.str_deadline() + "</p>\n"

            if people is not None:
                widget += '<div style="text-align: right; padding-top: 10px;">'
                if people.id not in notification.confirmeds.split(","):
                    widget += f'<button id="confirm_status_change" style="padding: 5px 10px; background-color: #AF4C50; color: white; border: none;" onclick="confirmNotification(\'{class_.name}\', {notification.id}, this)">请确认收到通知</button>\n'
                else:
                    widget += f'<button id="confirm_status_change" style="padding: 5px 10px; background-color: #4CAF50; color: white; border: none;" onclick="disconfirmNotification(\'{class_.name}\', {notification.id}, this)">已确认收到通知</button>\n'
                widget += "</div>"
            else:
                widget += "<details><summary>已确认收到通知</summary><ul>"
                for id in notification.confirmeds.split(","):
                    if id == "":
                        continue
                    person = Person.query.filter_by(id=int(id)).first()
                    if person is not None:
                        widget += f"<li>{person.name}</li>"
                widget += "</ul></details>"
                widget += "<details><summary>未确认收到通知</summary><ul>"
                for id in notification.unconfirmeds.split(","):
                    person = Person.query.filter_by(id=int(id)).first()
                    if person is not None:
                        widget += f"<li>{person.name}</li>"
                widget += "</ul></details>"
            widget += "</div>\n"
            if people is not None:
                widget += "<script>"
                script = open("static/js/confirm.js", "r", encoding="utf-8").read()
                script = script.replace("<class>", str(class_.id))
                script = script.replace("<notification>", str(notification.id))
                widget += script
                widget += "</script>"
        return widget

    def str_deadline(self) -> str:
        return self.deadline.strftime("%Y-%m-%d %H:%M:%S")


class Html_index:
    def __init__(self, user: Person, main_area: str = "") -> None:
        self.user = user
        self.classes = []  # 初始化一个空列表，用于存储班级名称
        if user.classes is not None:  # 检查用户的班级信息是否存在
            class_ids = user.classes.split(",")  # 将班级 ID 字符串按逗号分割成列表
            for class_id in class_ids:  # 遍历班级 ID 列表
                class_ = Class.query.filter_by(id=class_id).first()  # 查询班级信息
                if class_ is not None:  # 检查班级是否存在
                    self.classes.append(class_)
        self.main_area = main_area

    def get_html(self) -> str:
        self.user.clean_classes()
        html = open("./templates/index.html", "r", encoding="utf-8").read()
        link = f'<a href="/user">{self.user.username}</a>'
        html = html.replace("<!--name-->", link)
        links = ""
        for class_ in self.classes:
            links += f'<li>\n<button class="sidebar-button" onclick="location.href=\'/class/{class_.id}\'">{class_.name}</button>\n</li>\n'
        html = html.replace("<!--Class List-->", links)
        html = html.replace("<!--Content-->", self.main_area)
        return html

    def get_index_html(self) -> str:
        widget = ""
        for class_ in self.classes:
            widget += Notification.get_html_widget(class_, self.user)
        self.main_area = widget
        return self.get_html()

    def get_user_html(self) -> str:
        main_area = open("./templates/userinfo.html", "r", encoding="utf-8").read()
        main_area = main_area.replace("<!--username-->", self.user.username)
        main_area = main_area.replace("<!--table-->", self.user.format_courses())
        main_area += '<a href="user/rm" style="color:red;font-size:16px;">销毁账号</a>'
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


def is_valid_input_str(input_str: str) -> bool:
    """验证输入字符串是否合法。
    输入字符串不能包含非法字符，特别是HTML和MySQL中可能被用于攻击的字符。

    参数:
        input_str (str): 要验证的输入字符串。

    返回:
        bool: 如果输入字符串格式合法，返回 True；否则返回 False。
    """
    # 定义非法字符
    illegal_characters = r"[<>'\";()&%$#@!\\\[\]{}=`~]+"

    # 检查是否包含非法字符
    if re.search(illegal_characters, input_str):
        return False

    return True


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

    更新说明:
        用户端直接返回sha256加密后的密码，不再进行验证。
    """
    return True


def parse_xls(file_content: str, is_gbk=False) -> str:
    """解析 Excel 文件内容。

    参数:
        file_content (str): Excel 文件内容。

    返回:

    """
    all_ids = []
    lst = file_content.split(SPLITER)
    for li in lst:
        try:
            int(li[0])
            if "A" + li.split(")")[0] not in all_ids:
                all_ids.append("A" + li.split(")")[0])
        except ValueError:
            pass
    for id in all_ids:
        course = Course.query.filter_by(id=id).first()
        if course is not None:
            course.name = ""
            course.teacher = ""
            for courcation_id in course.courcations.split(","):
                courcation = Courcation.query.filter_by(id=courcation_id).first()
                if courcation is not None:
                    courcation.location = ""
                    courcation.time_tables = ""
            course.courcations = ""
            db.session.commit()
    course_list = pd.read_html(file_content)[-2].values.tolist()
    course_ids = ""
    for n in range(6):
        for d in range(7):
            try:
                # print(course_list[2 * n][d + 1].strip(), d, n)
                course_ids += parse_course(course_list[2 * n][d + 1].strip(), d, n, is_gbk) + ","
            except AttributeError:
                pass
    ids = ""
    for course_id in course_ids.split(",")[:-1]:
        if course_id in ids.split(","):
            continue
        ids += course_id + ","
    return ids


def parse_course(source_t: str, weekday: int, number: int, is_gbk=False) -> str:
    source_t = source_t.replace("校区))", "校区)").replace("校区)", "校区))")
    if len(source_t.split(")) ")) > 1:
        out = ""
        for t in source_t.split(")) ")[:-1]:
            out += parse_course((t + "))").strip(), weekday, number, is_gbk) + ","
        out += parse_course(source_t.split(")) ")[-1].strip(), weekday, number, is_gbk)
        return out
    string = source_t.strip()
    name = string.split(SPLITER)[0].strip()
    string = string.replace(name, "").strip()
    id = string.split(" ")[0]
    string = string.replace(id, "").strip()
    id = id.replace("(", "").replace(")", "")
    teacher = string.split(" ")[0]
    string = string.replace(teacher, "").strip()
    teacher = teacher.replace("(", "").replace(")", "")
    if is_gbk:
        string = string.replace(",", "`").replace(" ", ",").replace("`", " ")
    time = string.split(" ")[0].replace("(", "").replace(")", "")
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
        for li in lists[1:]:
            if out is None:
                out = li
            else:
                out += li
        return out
    out = []
    length = -1
    for li in lists:
        if len(li) != length and length != -1:
            raise ValueError("列表长度不一致")
        length = len(li)
        if len(out) == 0:
            out = [None for _ in range(length)]
        for n, item in enumerate(li):
            out[n] = merge_list(out[n], item)
    return out


def display_color(rate: float):
    hsla = "hsla("
    h = int(240 - 240 * rate)
    if h < 0:
        h += 360
    elif h > 360:
        h -= 360
    s = 1  # 饱和度
    l = 0.3 + 0.2 * rate  # 亮度
    a = 0.5  # 透明度
    hsla += str(h) + "," + str(s * 100) + "%," + str(l * 100) + "%" + "," + str(a) + ")"
    return hsla
