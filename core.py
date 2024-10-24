from datetime import datetime, timedelta


SPLITER = '(A'


def display_color(rate: float):
    hsla = 'hsla('
    h = int(240 - 240*rate)
    if h < 0:
        h += 360
    elif h > 360:
        h -= 360
    s = 1  # 饱和度
    l = 0.3 + 0.2*rate  # 亮度
    a = 0.5  # 透明度
    hsla += str(h) + ',' + str(s*100) + '%,' + str(l*100) + '%' + ',' + str(a) + ')'
    return hsla


class Course:
    def __init__(self, weekday: int = None, number: int = None, source_t: str = None) -> None:
        if source_t is None:
            self.name = None
            self.id = None
            self.teacher = None
            self.location = {}
            return None
        string = source_t
        self.name = string.split(SPLITER)[0].strip()
        string = string.split(self.name)[1].strip()
        self.id = string.split('(')[1].split(')')[0].strip()
        string = string.split(')', 1)[1].strip()
        self.teacher = string.split('(')[1].split(')')[0].strip()
        string = string.split(')', 1)[1].strip()
        week_and_location = string.split('(', 1)[1].replace('))', ')').strip()
        self.location = {}
        if ',' in week_and_location:
            week = week_and_location.split(',')[0].strip()
            location = week_and_location.split(',')[1]
        else:
            week = week_and_location.split(')')[0].strip()
            location = ''
        weeks = []
        for weekp in week.split(' '):
            if '-' in weekp and ('单' in weekp or '双' in weekp):
                for w in range(int(weekp.split('-')[0]), int(weekp.split('-')[1].split('单')[0].split('双')[0]) + 1, 2):
                    weeks.append(w)
            elif '-' in weekp and '单' not in weekp and '双' not in weekp:
                for w in range(int(weekp.split('-')[0]), int(weekp.split('-')[1]) + 1):
                    weeks.append(w)
            else:
                weeks.append(int(weekp))
        for w in weeks:
            self.location[str(w) + '|' + str(weekday) + '|' + str(number)] = location

    def merge_into_list(self, courses: list) -> list:
        for course in courses:
            if course.id == self.id:
                self.location.update(course.location)
                courses.remove(course)
                courses.append(self)
                return courses
        courses.append(self)
        return courses

    def from_dict(self, data: dict) -> None:
        self.name = data["name"]
        self.id = data["id"]
        self.teacher = data["teacher"]
        self.location = data["location"]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "teacher": self.teacher,
            "location": self.location
        }


class Schedule:
    def __init__(self, course_t: str = None) -> None:
        self.courses = self.parse_course_t(course_t)

    def update_course(self, courst_t: str = None) -> None:
        self.courses = self.parse_course_t(courst_t)

    def add_course(self, w: int, d: int, n: int, id: str, name: str, teacher: str, location: str) -> bool:
        try:
            course = Course()
            course.id = id
            course.name = name
            course.teacher = teacher
            course.location[str(w) + '|' + str(d) + '|' + str(n)] = location
            self.courses = course.merge_into_list(self.courses)
            return True
        except Exception:
            return False

    def parse_course_t(self, course_t: str) -> list[Course]:
        if course_t is None or course_t == '无':
            return []
        if '节次/周次' not in course_t:
            return []
        course_t = course_t.replace("\n", "")
        t_list = []
        t_list.append(course_t.split("第一节")[1].split('第二节')[0].split('\t')[1:])
        t_list.append(course_t.split("第三节")[1].split('第四节')[0].split('\t')[1:])
        t_list.append(course_t.split("第五节")[1].split('第六节')[0].split('\t')[1:])
        t_list.append(course_t.split("第七节")[1].split('第八节')[0].split('\t')[1:])
        t_list.append(course_t.split("第九节")[1].split('第十节')[0].split('\t')[1:])
        t_list.append(course_t.split("第十一节")[1].split('第十二节')[0].split('\t')[1:])
        for i in range(6):
            while len(t_list[i]) < 7:
                t_list[i].append(t_list[i][-1])
        courses = []
        for i in range(6):
            for j in range(7):
                cc = len(t_list[i][j].split(SPLITER)) - 1
                if '校区))' in t_list[i][j]:
                    course_this_time = t_list[i][j].split('校区))')
                else:
                    course_this_time = t_list[i][j].split('校区)')
                for k in range(cc):
                    course = Course(j + 1, i + 1, course_this_time[k].strip() + '校区))')
                    courses = course.merge_into_list(courses)
        return courses

    def from_dict(self, data: dict) -> None:
        if data['courses'] is None:
            self.courses = None
        for course_data in data["courses"]:
            course = Course()
            course.from_dict(course_data)
            self.courses.append(course)

    def to_dict(self) -> dict:
        return {
            "courses": [course.to_dict() for course in self.courses]
        }
    
    def get_time_table(self, name: str) -> list[tuple[int, int, int]]:
        time_table = []
        for course in self.courses:
            for time in course.location.keys():
                week, day, number = time.split('|')
                time_table.append((name, int(week), int(day), int(number)))
        return time_table
    
    def to_html(self) -> str:
        html = ''
        for w in range(1, 21):
            html += '第' + str(w) + '周<br />' + '<table border="1" width="100%">'
            html += '<tr><th width="14.2857142857%">星期日</th><th width="14.2857142857%">星期一</th><th width="14.2857142857%">星期二</th><th width="14.2857142857%">星期三</th><th width="14.2857142857%">星期四</th><th width="14.2857142857%">星期五</th><th width="14.2857142857%">星期六</th></tr>'
            for n in range(1, 7):
                html += '<tr height=\"50px\">'
                for d in range(1, 8):
                    html += '<td>'
                    for course in self.courses:
                        if str(w) + '|' + str(d) + '|' + str(n) in course.location.keys():
                            html += course.name + '<br>' + course.teacher + '<br>' + course.location[str(w) + '|' + str(d) + '|' + str(n)]
                            html += f'<br /><button class="class-delete-btn" onclick="window.location.href=\'/user/delete_course?id={course.id}&name={course.name}&teacher={course.teacher}&time={str(w) + "|" + str(d) + "|" + str(n)}\';">删除</a>'
                            break
                    else:
                        html += f'''
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
                                '''
                    html += '</td>'
                html += '</tr>'
            html += '</table><br>'
        return html
    
    def delete_course(self, id: str, name: str, teacher: str, time: str) -> bool:
        for course in self.courses:
            if course.id == id and course.name == name and course.teacher == teacher and str(time) in course.location.keys():
                course.location.pop(str(time))
                return True
        return False


class Person:
    def __init__(self, name: str = None, id: int = None) -> None:
        self.name = name
        self.id = id
        self.username = None
        self.password = None
        self.schedule = None

    def register(self, username: str, password: str, schedule: Schedule = None) -> None:
        self.username = username
        self.password = password
        self.schedule = schedule

    def from_dict(self, data: dict) -> None:
        if data == {}:
            return None
        self.name = data["name"]
        self.id = data["id"]
        self.username = data["username"]
        self.password = data["password"]
        if data["schedule"] is not None:
            self.schedule = Schedule()
            self.schedule.from_dict(data["schedule"])
        else:
            self.schedule = None

    def to_dict(self, include_schedule: bool = True) -> dict:
        if include_schedule:
            return {
                "name": self.name,
                "id": self.id,
                "username": self.username,
                "password": self.password,
                "schedule": self.schedule.to_dict() if self.schedule else None
            }
        else:
            return {
                "name": self.name,
                "id": self.id,
                "username": self.username,
                "password": self.password,
                "schedule": None
            }

    def update_schedule(self, raw_text: str) -> None:
        self.schedule = Schedule(raw_text)

    def get_time_table(self) -> list[tuple[str, int, int, int]]:
        if self.schedule is None:
            return []
        return self.schedule.get_time_table(self.name)


class Class:
    def __init__(self, name: str = None, owner: Person = None, students: list[Person] = None) -> None:
        self.name = name
        self.owner = owner
        self.students = []
        _id_list = []
        if students is not None:
            for student in students:
                if student.id not in _id_list:
                    self.students.append(student)
                    _id_list.append(student.id)
        else:
            self.students = []

    def from_dict(self, data: dict) -> None:
        if data == {}:
            return None
        self.name = data["name"]
        self.owner = Person()
        self.owner.from_dict(data["owner"])
        self.students = []
        for student in data["students"]:
            person = Person()
            person.from_dict(student)
            self.students.append(person)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "owner": self.owner.to_dict(False),
            "students": [student.to_dict(False) for student in self.students]
        }
    
    def reload_students(self, students: list[Person]) -> None:
        self.students = []
        _id_list = []
        for student in students:
            if student.id not in _id_list:
                self.students.append(student)
                _id_list.append(student.id)

    def get_time_table_with_name(self, users: list[Person]):
        full_time_table = []
        for _ in range(1, 21):
            _1 = []
            for _ in range(1, 8):
                _2 = []
                for _ in range(1, 7):
                    _2.append([])
                _1.append(_2)
            full_time_table.append(_1)
        for student in self.students:
            for user in users:
                if student.id == user.id:
                    student = user
                    break
            time_table = student.get_time_table()
            for name, week, day, number in time_table:
                full_time_table[week - 1][day - 1][number - 1].append(name)
                # if full_time_table[week - 1][day - 1][number - 1] == []:
                #     full_time_table[week - 1][day - 1][number - 1].append("信1")
        return full_time_table

    def get_time_table_with_count(self, users: list[Person]):
        full_time_table = []
        for _ in range(1, 21):
            _1 = []
            for _ in range(1, 8):
                _2 = []
                for _ in range(1, 7):
                    _2.append(0)
                _1.append(_2)
            full_time_table.append(_1)
        for student in self.students:
            for user in users:
                if student.id == user.id:
                    student = user
                    break
            time_table = student.get_time_table()
            for _, week, day, number in time_table:
                full_time_table[week - 1][day - 1][number - 1] += 1
        return full_time_table
    
    def update_members(self, members: list[Person]) -> None:
        new_students = []
        for student in self.students:
            for member in members:
                if student.id == member.id:
                    new_students.append(member)
                    break
            else:
                new_students.append(student)
        self.students = new_students

    def time_table_to_html(self, users: list[Person], with_name: bool = False):
        if with_name:
            full_time_table = self.get_time_table_with_name(users)
        else:
            full_time_table = self.get_time_table_with_count(users)
        html = ''
        for w in range(1, 21):
            html += '第' + str(w) + '周<br />' + '<table border="1" width="100%"><tbody align="center" valign="center">'
            html += '<tr><th width="14.2857142857%">星期日</th><th width="14.2857142857%">星期一</th><th width="14.2857142857%">星期二</th><th width="14.2857142857%">星期三</th><th width="14.2857142857%">星期四</th><th width="14.2857142857%">星期五</th><th width="14.2857142857%">星期六</th></tr>'
            for n in range(1, 7):
                html += '<tr height=\"50px\">'
                if isinstance(full_time_table[w - 1][0][n - 1], list):
                    for d in range(1, 8):
                        rate = len(full_time_table[w - 1][d - 1][n - 1]) / len(self.students)
                        html += '<td style=\"background-color:' + display_color(rate) + '\">'
                        html += '<div class="cell">'
                        for name in full_time_table[w - 1][d - 1][n - 1]:
                            html += name + '<br>'
                        html += '</div></td>'
                elif isinstance(full_time_table[w - 1][0][n - 1], int):
                    for d in range(1, 8):
                        rate = full_time_table[w - 1][d - 1][n - 1] / len(self.students)
                        html += '<td style=\"background-color:' + display_color(rate) + '\">'
                        html += str(full_time_table[w - 1][d - 1][n - 1])
                        html += '</td>'
                html += '</tr>'
            html += '</tbody></table><br>'
        return html


class Notification:
    def __init__(self, title: str = None, content: str = None, deadline: str = None, class_name: str = None, confirmed_users: list[Person] = None, need_submit: bool = False) -> None:
        self.title = title
        self.content = content
        self.deadline = datetime.strptime(deadline, r'%Y-%m-%dT%H:%M') if deadline is not None else None
        self.class_name = class_name
        if need_submit:
            self.content += f'<br><a href=\"/class/{self.class_name}/submitfiles\">提交文件入口</a>\n'
        self.confirmed_users = confirmed_users if confirmed_users is not None else []

    def from_dict(self, data: dict) -> None:
        if data == {}:
            return None
        self.title = data["title"]
        self.content = data["content"]
        self.deadline = datetime.strptime(data["deadline"], r'%Y-%m-%dT%H:%M') if data["deadline"] is not None else None
        self.class_name = data["class_name"]
        self.confirmed_users = []
        for user in data["confirmed_users"]:
            person = Person()
            person.from_dict(user)
            self.confirmed_users.append(person)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "deadline": self.deadline.strftime(r'%Y-%m-%dT%H:%M'),
            "class_name": self.class_name,
            "confirmed_users": [user.to_dict(False) for user in self.confirmed_users]
        }
    
    def add_confirmed_user(self, user: Person) -> None:
        if user not in self.confirmed_users:
            self.confirmed_users.append(user)

    def remove_confirmed_user(self, user: Person) -> None:
        for u in self.confirmed_users:
            if u.id == user.id:
                self.confirmed_users.remove(u)
                break

    def str_deadline(self) -> str:
        return self.deadline.strftime(r'%Y-%m-%d %H:%M')

    def to_html(self, username: str) -> str:
        days = (self.deadline - datetime.now()).days
        if days < 30 and days >= 0:
            color = display_color(1 - days / 30)
        elif days < 0:
            color = '#555555'
        else:
            color = '#FFFFFF'
        html = ''
        html += f'<div style="margin-bottom: 20px; border: none; padding: 10px; border-radius: 5px; box-shadow: 10px 10px 10px {color}; background-color: #272733; margin: 20px;">\n'
        html += '<h2>来自' + self.class_name + '的通知:</h2>\n'
        html += '<h3>' + self.title + '</h3>\n'
        html += '<p>' + self.content.replace('\n', '<br>').replace('\r', '') + '</p>\n'
        html += '<p>截止时间：' + self.str_deadline() + '</p>\n'
        html += '<div style="text-align: right; padding-top: 10px;">'
        if username not in [user.username for user in self.confirmed_users]:
            html += f'<button style="padding: 5px 10px; background-color: #AF4C50; color: white; border: none;" onclick="window.location.href=\'/class/{self.class_name}/confirm/{self.title}\'">请确认收到通知</button>\n'
        else:
            html += f'<button style="padding: 5px 10px; background-color: #4CAF50; color: white; border: none;" onclick="window.location.href=\'/class/{self.class_name}/disconfirm/{self.title}\'">已确认收到通知</button>\n'
        html += '</div></div>\n'
        return html
    
    def to_confirmed_html(self, classes: list[Class]) -> str:
        days = (self.deadline - datetime.now()).days
        if days < 30 and days >= 0:
            color = display_color(1 - days / 30)
        elif days < 0:
            color = '#555555'
        else:
            color = '#FFFFFF'
        for class_ in classes:
            if class_.name == self.class_name:
                current_class = class_
                break
        else:
            raise ValueError('Class not found')
        html = ''
        html += f'<div style="margin-bottom: 20px; border: none; padding: 10px; border-radius: 5px; box-shadow: 10px 10px 10px {color}; background-color: #272733; margin: 20px;">\n'
        html += '<h3>' + self.title + '</h3>\n'
        html += '<p>' + self.content.replace('\n', '<br>').replace('\r', '') + '</p>\n'
        html += '<p>截止时间：' + self.str_deadline() + '</p>\n'
        html += '<details><summary>已确认名单</summary><ul>\n'
        confirmed_ids = []
        for user in self.confirmed_users:
            html += f'<li>{user.name}</li>\n'
            confirmed_ids.append(user.id)
        html += '</ul></details>\n'
        html += '<details><summary>未确认名单</summary><ul>\n'
        for user in current_class.students:
            if user.id not in confirmed_ids:
                html += f'<li>{user.name}</li>\n'
        html += '</ul></details>\n'
        html += '<div style="text-align: right; padding-top: 10px;">'
        html += f'<button style="padding: 5px 10px; background-color: #AF4C50; color: white; border: none;" onclick="window.location.href=\'/class/{self.class_name}/delete_notification/{self.title}\'">删除通知</button>\n'
        html += '</div></div>\n'
        return html


class Html_index:
    def __init__(self, user: Person, class_names: list[str], main_area: str = '', **kwargs) -> None:
        self.user = user
        self.class_names = class_names
        self.main_area = main_area

    def get_html(self) -> str:
        html = open('./templates/index.html', 'r', encoding='utf-8').read()
        link = f'<a href="/user/{self.user.username}">{self.user.username}</a>'
        html = html.replace('<!--name-->', link)
        links = ''
        for class_name in self.class_names:
            links += f'<li>\n<button class=\"sidebar-button\" onclick=\"location.href=\'/class/{class_name}\'\">{class_name}</button>\n</li>\n'
        html = html.replace('<!--Class List-->', links)
        html = html.replace('<!--Content-->', self.main_area)
        return html
    

class Html_Error:
    def __init__(self, error: str, error_message: str) -> None:
        self.error = error
        self.error_message = error_message
    
    def get_html(self) -> str:
        html = open('./templates/Error.html', 'r', encoding='utf-8').read()
        html = html.replace('<!--Err_title-->', self.error)
        html = html.replace('<!--Err_content-->', self.error_message)
        return html


if __name__ == "__main__":
    pass
