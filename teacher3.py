import pymysql as p
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import json
import requests
import xmltodict
from socket import *
from threading import *


# 인증키 저장
key = "4Y1VQ%2BFCILQgfBdtfbv2AGShcA9czXwJPhSXne622ujf7MWF8FHODnOX%2B7QWvUxzm2e81Njv464DtuNT4OKygQ%3D%3D"
# 인증키 정보가 들어간 url 저장
url = f"http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctPrtctList?serviceKey={key}"


content = requests.get(url).content                      # request 모듈을 이용해서 정보 가져오기(byte형태로 가져와지는듯)
dict = xmltodict.parse(content)                         # xmltodict 모듈을 이용해서 딕셔너리화 & 한글화
jsonString = json.dumps(dict, ensure_ascii=False)       # json.dumps를 이용해서 문자열화(데이터를 보낼때 이렇게 바꿔주면 될듯)
jsonObj = json.loads(jsonString)                        # 데이터 불러올 때(딕셔너리 형태로 받아옴)
bank = []
for item in jsonObj['response']['body']['items']['item']:
    bank.append((item['insctFamilyNm'],item['insctPcmtt'], item['insctofnmkrlngnm']))
	# print(item['insctFamilyNm'],item['insctPcmtt'], item['insctofnmkrlngnm'])
print(bank)


form_class = uic.loadUiType("teacher.ui")[0]
class log(QMainWindow,form_class):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.stackedWidget.setCurrentIndex(3)
        # self.stackedWidget.setStyleSheet('background-color:lightcyan')
        self.setWindowTitle('박보영과 함께하는 곤충농장')
        self.join_btn.clicked.connect(self.join)
        self.move_login.clicked.connect(self.login_stack)
        self.join_page.clicked.connect(self.join_stack)

        # 소켓 생성
        self.initialize_socket()

        # 교사 페이지 관련 버튼
        self.login_action.clicked.connect(self.login) # 로그인

        self.question_update_btn.clicked.connect(self.question_update)#문제 올리는 페이지로 넘어감
        self.question_upload_btn.clicked.connect(self.question_upload)#문제 올리기 버튼 클릭시 db에 업로드 함.
        self.chat_btn_2.clicked.connect(self.cons) #실시간 상담하기 버튼 클릭시, 채팅 화면으로 이동
        self.qna_btn_2.clicked.connect(self.qna_show) #Q&A 버튼 클릭시 qna db를 불러옴
        # self.marks_btn.clicked.connect(self.show_mark)

        self.main_btn.clicked.connect(self.to_main)
        self.main_btn_2.clicked.connect(self.to_main)
        self.send_btn.clicked.connect(self.send_message)
        self.qna_table.cellClicked.connect(self.set_answer)
        self.answer_btn.clicked.connect(self.print_answer)
        self.lack_part_btn.clicked.connect(self.show_lackpart)


        self.member = False
        # DB 연결

    def show_lackpart(self):
        self.stackedWidget.setCurrentIndex(2)

        # self.cursor.execute(f'select *, round(hit / total, 1)*100 AS wrong from result2 where round(hit / total, 2)*100 <60 order by name')

        send_List = ['result2 테이블']
        clist = json.dumps(send_List)  # json.dumps로 리스트의 값들 바이트형으로 바꿔줌
        print(send_List, "@#@#")
        self.client_socket.send(clist.encode())  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌

        self.con2()

        # # self.cursor.execute(f'select * from result order by name')
        # errors = self.cursor.fetchall()
        # print(errors, '[errors]')
        # self.grade_table_2.setRowCount(len(errors))  # 테이블의 행 갯수를 rows의 길이로 정함
        # self.grade_table_2.setColumnCount(len(errors[0]))
        # for i in range(len(errors)):
        #     for j in range(len(errors[i])):
        #         self.grade_table_2.setItem(i, j, QTableWidgetItem(str(errors[i][j])))
        #
        # self.grade_table_2.resizeColumnsToContents()

    def show_mark(self):
        self.stackedWidget.setCurrentIndex(2)
        self.cursor.execute(f'select * from result order by name')
        results = self.cursor.fetchall()
        self.grade_table.setRowCount(len(results))  # 테이블의 행 갯수를 rows의 길이로 정함
        self.grade_table.setColumnCount(len(results[0]))
        for i in range(len(results)):
            for j in range(len(results[i])):
                self.grade_table.setItem(i, j, QTableWidgetItem(str(results[i][j])))

        self.grade_table.resizeColumnsToContents()


    def initialize_socket(self):
        ip = input("서버 IP를 입력해주세요(default=10.10.21.117): ")
        if ip == '':
            ip = '10.10.21.125'
        port = 9797

        # TCP socket을 생성하고 server와 연결
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((ip, port))
        print(ip, ':ipip')

    def cons(self):
        self.stackedWidget.setCurrentIndex(5)
        self.listen_thread()
        print('thread1 가 돌고있어요')

    def con2(self):
        self.listen_thread()
        print('thread2 이 돌고있어요')




    def send_message(self):
        # teacher_talk = self.lineEdit_teacher_talk.text()
        # self.chat_browser.addItem(teacher_talk)

        message = self.lineEdit_teacher_talk.text()
        name = self.d[0][0]
        send_List = ['상담하기', name, message]
        clist = json.dumps(send_List)  # json.dumps로 리스트의 값들 바이트형으로 바꿔줌
        print(send_List, "@#@#")

        self.client_socket.send(clist.encode())  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌
        self.lineEdit_teacher_talk.clear()
        # 리스트 위젯에 작성한 글 append해줌
        # self.lis.addItem(f"{name}:{message}")


    def to_main(self):
        self.stackedWidget.setCurrentIndex(4)


    def online_chat(self):
        self.stackedWidget.setCurrentIndex(5)
        self.lineEdit_teacher_talk.setText('공부는 잘 되가니?')

    def qna_show(self):
        self.cursor.execute(f'select * from qnaboard')
        qna_content = self.cursor.fetchall()
        self.qna_table.setRowCount(len(qna_content))  # 테이블의 행 갯수를 rows의 길이로 정함
        self.qna_table.setColumnCount(len(qna_content[0]))
        for i in range(len(qna_content)):
            for j in range(len(qna_content[i])):
                self.qna_table.setItem(i, j, QTableWidgetItem(str(qna_content[i][j])))

        self.qna_table.resizeColumnsToContents()



    def set_answer(self, row, column):
        item = self.qna_table.item(row, column)
        self.value = item.text()

    def print_answer(self):
        answered = self.lineEdit_answer_2.text()
        name = self.d[0][0]

        send_List = ['QnA', self.value, answered]
        clist = json.dumps(send_List)  # json.dumps로 리스트의 값들 바이트형으로 바꿔줌
        print(send_List, "@#@#")

        self.client_socket.send(clist.encode())  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌

        self.con2()

    def got_qna(self):
        ###
        try:
            answered = self.lineEdit_answer_2.text()
            print(answered, 'answer')
            self.cursor.execute(f'update qnaboard set answer = "{answered}" where message = "{self.value}"')
            self.conn.commit()

            self.cursor.execute(f'select * from qnaboard')

            qna_content = self.cursor.fetchall()
            self.qna_table.setRowCount(len(qna_content))  # 테이블의 행 갯수를 rows의 길이로 정함
            self.qna_table.setColumnCount(len(qna_content[0]))

            for i in range(len(qna_content)):
                for j in range(len(qna_content[i])):
                    self.qna_table.setItem(i, j, QTableWidgetItem(str(qna_content[i][j])))

            self.qna_table.resizeColumnsToContents()
            self.lineEdit_answer_2.clear()

        except:
            QMessageBox.information(self, 'Quit', f'등록하실 문의칸을 클릭해주세요.')


    def question_update(self):
        self.stackedWidget.setCurrentIndex(2)
        self.lineEdit_question.setText('닻무늬길앞잡이는딱정벌레과이다')
        self.lineEdit_answer.setText('o')
        self.lineEdit_kind.setText('종류')

    def question_upload(self):
        question = self.lineEdit_question.text()
        answer = self.lineEdit_answer.text()
        kind = self.lineEdit_kind.text()

        send_List = ['문제', question, answer, kind]
        clist = json.dumps(send_List)  # json.dumps로 리스트의 값들 바이트형으로 바꿔줌
        print(send_List, "@#@#")

        self.client_socket.send(clist.encode())  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌

        # self.cursor.execute(f'insert into exam (qu, an, type) values("{question}","{answer}","{kind}")')
        # self.conn.commit()
        # self.cursor.execute(f'select * from exam')
        # questions = self.cursor.fetchall()
        # print('pll: ', questions)

        self.lineEdit_question.clear()
        self.lineEdit_answer.clear()
        self.lineEdit_kind.clear()

        self.con2()


        # question_update_table
        # sql = f"SELECT * FROM inquiries"
        # cur.execute(sql)
        # requiry = cur.fetchall()
        # print(requiry)

        #### 테이블 위젯
        # self.question_update_table.setRowCount(len(questions))  # 테이블의 행 갯수를 rows의 길이로 정함
        # self.question_update_table.setColumnCount(len(questions[0]))
        # for i in range(len(questions)):
        #     for j in range(len(questions[i])):
        #         self.question_update_table.setItem(i, j, QTableWidgetItem(str(questions[i][j])))

        self.question_update_table.resizeColumnsToContents()


    def login_stack(self):
        self.stackedWidget.setCurrentIndex(3)
    def join_stack(self):
        self.stackedWidget.setCurrentIndex(0)

    def login(self):
        print("2222")
        self.conn = p.connect(host='10.10.21.125', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        self.cursor.execute('SELECT ID,PS FROM student')
        self.id_data=self.cursor.fetchall()

        self.login_id=self.id_2.text()
        # print(self.login_id)
        self.login_ps=self.ps_2.text()

        self.cursor.execute(f'select division from student where ID = "{self.login_id}"')
        divs = self.cursor.fetchall()
        print(divs, 'divssss')
        login = False
        for i in self.id_data:
            if self.login_id == i[0] and self.login_ps == i[1] and divs == (('교수',),):
                print(self.login_id,"sdsds")
                self.stackedWidget.setCurrentIndex(4)
                self.cursor.execute(f"select name from student where ID ='{self.login_id}'")
                self.d=self.cursor.fetchall()
                print(self.d[0][0])
                self.name_label.setText(f"{self.d[0][0]}님 안녕하세요")
                login = True
                return self.login_id
            else:
                pass

        if not login:
            QMessageBox.information(self, 'Quit', f'잘못된 로그인 정보 입니다.')

    def join(self):
        self.conn = p.connect(host='10.10.21.125', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        self.cursor.execute('SELECT * FROM student')
        self.b = self.cursor.fetchall()
        self.id=self.id_join.text()
        self.ps=self.ps_join.text()
        self.ps_look=self.ps_look.text()
        self.name=self.name_join.text()
        self.div = self.div_join.text()
        self.id_list=[]


        for i in range(0,len(self.b)):
            self.id_list.append(self.b[i][0])
        print(self.id_list)

        if self.id != '' and self.ps != '' and self.ps_look != '' and self.name != '':
            QMessageBox.information(self, '요건충족', 'dsadsa')
            if self.id in self.id_list:
                QMessageBox.warning(self, '아이디 중복', '중복 아이디 오류')
                print("중복!!!!!!!")
            else:
                QMessageBox.information(self, '통과 아이디', '중복확인 성공')
                print("아이디 통과 @@@@")
                if self.ps != self.ps_look:
                    QMessageBox.warning(self, '비밀번호 오류', '오류 비밀번호')
                else:
                    QMessageBox.information(self, '회원가입 완료', '맞음 비밀번호')
                    self.cursor.execute("set SQL_SAFE_UPDATES = 0")
                    # self.cursor.execute(f'update student set ID="{self.id}",비밀번호="{self.ps}" WHERE 이름="{self.name}"')
                    self.cursor.execute(f'insert into student values("{self.id}","{self.ps}","{self.name}","{self.div}")')
                    #
                    # self.cursor.execute("set SQL_SAFE_UPDATES = 1")
                    self.conn.commit()
                    self.conn.close()


        else:
            QMessageBox.warning(self, '필수요소', 'sdasdsa')  # 이거나옴


    def receive_message(self, so):
        self.qna_list = []
        question_list = []
        self.results = []
        while True:
            # 받은메시지
            buf = so.recv(999)
            # print(buf.decode(),"%%%%%")
            self.h=json.loads(buf.decode())

            print(self.h, 'receviedithahaha')
            if not buf:
                break
            elif '상담하기' in self.h:
                self.chat_browser.addItem(f"{self.h[1]}:{self.h[2]}")

            elif '전체문의' in self.h:
                self.qna_list.append(self.h)
                self.show_qnas()



            elif '전체문제' in self.h:

                question_list.append(self.h[1:])

                self.question_update_table.setRowCount(len(question_list))  # 테이블의 행 갯수를 rows의 길이로 정함
                self.question_update_table.setColumnCount(len(question_list[0]))
                for i in range(len(question_list)):
                    for j in range(len(question_list[i])):
                        self.question_update_table.setItem(i, j, QTableWidgetItem(str(question_list[i][j])))

                self.question_update_table.resizeColumnsToContents()


            elif '전체성적' in self.h:
                self.results.append(self.h[1:])

                self.grade_table_2.setRowCount(len(self.results))  # 테이블의 행 갯수를 rows의 길이로 정함
                self.grade_table_2.setColumnCount(len(self.results[0]))
                for i in range(len(self.results)):
                    for j in range(len(self.results[i])):
                        self.grade_table_2.setItem(i, j, QTableWidgetItem(str(self.results[i][j])))

                # self.grade_table_2.resizeColumnsToContents()
                self.grade_table_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


            # self.final_received_message = json.loads(incoming_message.decode())

    #
    # def statistics_show(self):
    #     self.results

    def show_qnas(self):
        self.qna_table.setRowCount(len(self.qna_list))  # 테이블의 행 갯수를 rows의 길이로 정함
        self.qna_table.setColumnCount(len(self.qna_list[0]))
        for i in range(len(self.qna_list)):
            for j in range(len(self.qna_list[i])):
                self.qna_table.setItem(i, j, QTableWidgetItem(str(self.qna_list[i][j])))

        self.qna_table.resizeColumnsToContents()
        self.lineEdit_answer_2.clear()


    def listen_thread(self):
        # 받는 메시지 스레드
        t = Thread(target=self.receive_message, args=(self.client_socket,), daemon=True)
        t.start()



if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)

    #WindowClass의 인스턴스 생성
    myWindow = log()

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()