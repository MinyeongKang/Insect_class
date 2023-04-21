import datetime
import time

import pymysql as p
import requests
import xmltodict
import json
import sys
import random
from socket import *
from threading import *

from PyQt5.QtWidgets import *
from PyQt5 import uic


from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

import urllib.request
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import *

form_class = uic.loadUiType("login.ui")[0]

class log(QMainWindow,form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # ui 첫페이지 고정
        self.stackedWidget.setCurrentIndex(3)
        self.stackedWidget_2.setCurrentIndex(5)

        self.setWindowTitle('박보영과 함께하는 곤충농장')

        # 로그인에 필요한 이동
        self.join_btn.clicked.connect(self.join)
        self.move_login.clicked.connect(self.login_stack)
        self.join_page.clicked.connect(self.join_stack)
        self.login_action.clicked.connect(self.login)
        self.logout_btn.clicked.connect(self.login_stack)
        self.member = False

        # 학생페이지 버튼실행함수
        self.study_btn.clicked.connect(self.study)
        self.chat_btn.clicked.connect(self.chat)
        self.mypage_btn.clicked.connect(self.mypage)

        # 소켓 생성
        self.initialize_socket()

        # 학생 문의하기
        self.qna_btn.clicked.connect(self.qna)
        self.qna_send.clicked.connect(self.qnalist)

        # 학생 학습하기
        self.studylistWidget.itemClicked.connect(self.learning)
        self.studylistWidget.itemDoubleClicked.connect(self.learning)
        self.exam_test.clicked.connect(self.test)
        self.O_btn.clicked.connect(self.O)
        self.X_btn.clicked.connect(self.X)
        self.next_btn.clicked.connect(self.sendsever)
        self.Load_btn.clicked.connect(self.learningload)

        # 문제에 따른 메서드 합쳐주기
        self.total_btn.clicked.connect(lambda :self.totaltest('종합'))
        self.grade_btn.clicked.connect(lambda :self.totaltest('등급'))
        self.type_btn.clicked.connect(lambda :self.totaltest('종류'))
        self.learning_end.clicked.connect(self.learningsend)

        # 학생 상담하기
        self.chatsend_btn.clicked.connect(self.sendchat)

        # 스레드 실행
        self.listen_thread()

    def initialize_socket(self):

        ip = '10.10.21.125'
        port = 9797

        # TCP socket을 생성하고 server와 연결
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((ip, port))

    def login_stack(self):
        self.stackedWidget.setCurrentIndex(3)
        self.id_2.clear()
        self.ps_2.clear()

    def join_stack(self):
        self.stackedWidget.setCurrentIndex(0)

    # DB 연결
    def open_db(self):
        self.conn = p.connect(host='10.10.21.125', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.c = self.conn.cursor()

    def login(self):

        # 로그인후 마이페이지로 고정
        self.open_db()
        self.c.execute('SELECT ID,PS FROM student')

        self.id_data = self.c.fetchall()
        self.login_id = self.id_2.text()
        self.login_ps = self.ps_2.text()

        for i in self.id_data:
            if self.login_id == i[0] and self.login_ps == i[1]:
                print(self.login_id)
                self.stackedWidget.setCurrentIndex(1)
                self.c.execute(f"select name from student where ID ='{self.login_id}'")
                self.d = self.c.fetchall()
                print(self.d[0][0])
                self.name_label.setText(f"{self.d[0][0]}님 반갑습니다")
                return self.login_id

    def join(self):
        self.open_db()
        self.c.execute('SELECT * FROM student')
        self.b = self.c.fetchall()
        self.id = self.id_join.text()
        self.ps = self.ps_join.text()
        self.ps_look = self.ps_look.text()
        self.name = self.name_join.text()
        self.div = self.div_join.text()
        self.id_list = []

        for i in range(0,len(self.b)):
            self.id_list.append(self.b[i][0])
        print(self.id_list)

        if self.id != '' and self.ps != '' and self.ps_look != '' and self.name != '':
            QMessageBox.information(self, ' ', '확인중')
            if self.id in self.id_list:
                QMessageBox.warning(self, '아이디 중복', '중복 아이디 오류')
                print("중복입니다")
            else:
                QMessageBox.information(self, '통과 아이디', '중복확인 성공')
                print("아이디 통과")
                if self.ps != self.ps_look:
                    QMessageBox.warning(self, '비밀번호 오류', '오류 비밀번호')
                else:
                    QMessageBox.information(self, '회원가입 완료', '맞음 비밀번호')
                    self.c.execute("set SQL_SAFE_UPDATES = 0")
                    self.c.execute(f'insert into ap.student values("{self.id}","{self.ps}","{self.name}","{self.div}")')
                    self.conn.commit()
                    self.conn.close()
                    self.stackedWidget.setCurrentIndex(1)

        else:
            QMessageBox.warning(self, ' ','회원가입 성공')  # 이거나옴

        # 회원가입 성공시 초기화
        self.id_join.clear()
        self.ps_join.clear()
        # self.ps_look.clear()
        self.name_join.clear()
        self.div_join.clear()



    # 학습하기
    def study(self):
        self.studylistWidget.clear()
        self.stackedWidget_2.setCurrentIndex(1)

        # 인증키 저장
        key = "4Y1VQ%2BFCILQgfBdtfbv2AGShcA9czXwJPhSXne622ujf7MWF8FHODnOX%2B7QWvUxzm2e81Njv464DtuNT4OKygQ%3D%3D"
        # 인증키 정보가 들어간 url 저장
        url = f"http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctPrtctList?serviceKey={key}"

        content = requests.get(url).content                     # request 모듈을 이용해서 정보 가져오기(byte형태로 가져와지는듯)
        dict = xmltodict.parse(content)                         # xmltodict 모듈을 이용해서 딕셔너리화 & 한글화
        jsonString = json.dumps(dict, ensure_ascii=False)       # json.dumps를 이용해서 문자열화(데이터를 보낼때 이렇게 바꿔주면 될듯)
        jsonObj = json.loads(jsonString)                        # 데이터 불러올 때(딕셔너리 형태로 받아옴)

        for item in jsonObj['response']['body']['items']['item']:
            self.studylistWidget.addItem(item['insctofnmkrlngnm'])
            print(item['insctFamilyNm'])
            print(item)

        # 스크롤 하단 고정
        self.studylistWidget.scrollToBottom()

    # 곤충선택에 따른 이미지 내용 표시
    def learning(self):
        self.detaillist.clear()
        # 리스트위젯에서 선택한 곤충의 이름 표시하기
        a = self.studylistWidget.currentItem().text()
        print(a)

        self.open_db()
        # 선택한 곤충에 따른 이미지 송출을 위한 쿼리문
        selname = f"select image from ap.learn where name = '{a}'"
        self.c.execute(selname)
        self.image = self.c.fetchall()

        seldetail = f"select detail from ap.learn where name ='{a}'"
        self.c.execute(seldetail)
        self.detail = self.c.fetchall()


        selraiting = f"select rating from ap.learn where name = '{a}';"
        self.c.execute(selraiting)
        raiting = list(self.c.fetchone())
        # print(raiting[0])

        self.studyname_line.setText(raiting[0])

        for i in range(len(self.detail)):
            print(self.detail[i][0])
            self.detaillist.addItem(self.detail[i][0])

        for i in range(len(self.image)):
            print(self.image[i][0])
            # 사진띄우기용 라벨
            self.label_15.setText(self.image[i][0])
            self.detaillist.scrollToBottom()
            imageFroWeb = urllib.request.urlopen(self.image[i][0]).read()
            qPixmapVar = QPixmap(f"{self.image[i][0]}")
            qPixmapVar.loadFromData(imageFroWeb)
            qPixmapVar = qPixmapVar.scaled(self.label_15.width(),self.label_15.height(),Qt.KeepAspectRatio,Qt.SmoothTransformation)
            self.label_15.setPixmap(qPixmapVar)

    # # 문제풀이 시작
    def test(self):
        self.stackedWidget_2.setCurrentIndex(4)

    # 서버로부터 메세지 수신
    def receive_message(self, so):
        while True:
            try:
                # 받은메시지
                buf = so.recv(9999)
                self.h = json.loads(buf.decode())
                # print(self.h, "서버로부터 받은메세지")
                if not buf:
                    break
                elif '상담하기' in self.h:
                    self.chatlistWidget.addItem(f"{self.h[1]} : {self.h[2]}")
                elif '질문내역' in self.h:
                    self.qna()
                    self.listWidget.addItem(f"[{self.h[1]}]  [{self.h[2]}]  [{self.h[3]}]")
                    self.listWidget.scrollToBottom()
                elif '결과' in self.h:
                    self.scoring_list.addItem(f"문제유형 : {self.h[2]} \n 정답개수 : {self.h[3]} / {self.h[4]}")
                elif '채점' in self.h:
                    self.scoring.addItem(f"{self.h[1]} {self.h[2]} {self.h[3]}")
                    if self.index == len(self.testgradelist):
                        self.testlist.setText("시험종료")
                    else:
                        self.testlist.setText(self.testgradelist[self.index])
                        print(self.index,"!!!!!!!!!!!!!!!!")
                        print(self.index == len(self.testgradelist))
                        self.index += 1

                elif '부르기' in self.h:
                    print(self.h[2])
                    self.learning_list.addItem(self.h[2])
                elif '문제풀이' in self.h:
                    pass
                elif '문제출제' in self.h:
                    self.problem_solving()
                elif '메인페이지' in self.h:
                    self.totalloding()
                elif '총등급' in self.h:
                    # self.mygrade.setText(self.h[3])
                    self.lcdNumber.setSegmentStyle(2)
                    self.lcdNumber.display(self.h[2])
                    self.lcdNumber_2.setSegmentStyle(2)
                    self.lcdNumber_2.display(self.h[3])
                    print(self.h[2],self.h[3],"등급보여줘!!!!!!!!!")

            except:
                continue
    def listen_thread(self):
        t = Thread(target=self.receive_message, args=(self.client_socket,))
        t.start()

    # 문제출제 시작
    def problem_solving(self):
        self.testgradelist = self.h[1::]
        b = len(self.testgradelist)
        print(b, "문제개수!")
        for i in self.testgradelist:
            print(i)
        self.index = 0
        self.testlist.setText(self.testgradelist[self.index])
        print(self.index)
        self.index += 1

    # 마이페이지 진도
    def totalloding(self):
        print(self.h)
        a = int(self.h[2])
        b = int(self.h[3])
        c = (round((a / b) * 100))
        # print(c)
        if self.h[1] == '등급':
            # 등급유형
            self.check_bar.setValue(c)
        elif self.h[1] == '종류':
            # 종류유형
            self.check_bar_2.setValue(c)
        elif self.h[1] == '종합':
            # 종합유형
            self.check_bar_3.setValue(c)



    def O(self):
        self.answer_btn.setText("o")
    def X(self):
        self.answer_btn.setText("x")
    def chat(self):
        self.stackedWidget_2.setCurrentIndex(2)

    # 문제정답 전송
    def totaltest(self,aa):
        self.stackedWidget_2.setCurrentIndex(4)
        name = self.d[0][0]
        send_List = [aa, name]
        testlist = json.dumps(send_List)
        print(send_List, "서버에게 보내줘")
        self.client_socket.send(testlist.encode())

    # 학생용 상담내역 게시판 전송버튼 클릭시 실행되는 메서드
    def sendchat(self):
        name = self.d[0][0]
        message = self.chatline.text()

        send_List = ['상담하기', name, message]
        testlist = json.dumps(send_List)           # json.dumps로 리스트의 값들 바이트형으로 바꿔줌
        print(send_List, "서버에게 보내줘")
        self.client_socket.send(testlist.encode())  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌
        self.chatline.clear()

    def qna(self):
        self.stackedWidget_2.setCurrentIndex(0)

    # 학생용 문의하기 게시판 전송버튼 클릭시 실행되는 메서드
    def qnalist(self):
        self.stackedWidget_2.setCurrentIndex(0)
        qnaname = self.d[0][0]
        qnamessage = self.qna_line.text()

        now = datetime.datetime.now()
        date_str = now.strftime('%y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        print(date_str)
        print(time_str)

        qnasend_List = ['문의하기', qnaname, qnamessage,date_str]
        testlist = json.dumps(qnasend_List)
        print(qnasend_List,"서버에게 보내줘")
        self.client_socket.send(testlist.encode())
        self.qna_line.clear()
        self.listWidget.clear()

    # 학생용 문제풀이 답안지 전송 제출클릭시 실행되는 메서드
    def sendsever(self,signal):

        now = datetime.datetime.now()
        time_str = now.strftime('%H:%M:%S')
        print(time_str)

        name = self.d[0][0]
        question = self.testlist.text()
        answer = self.answer_btn.text()
        self.open_db()
        self.c.execute(f"select type from ap.exam where qu = '{question}'")
        exammessage = list(self.c.fetchone())
        print(exammessage[0])

        test_List = ['문제풀이',name,exammessage[0], question,answer,time_str]
        testlist = json.dumps(test_List)
        self.client_socket.send(testlist.encode())
        print(test_List,"서버에게 보내줘")
        self.answer_btn.clear()
        self.scoring.clear()


    # 학생 학습하기 버튼클릭시 학습내역 저장
    def learningsend(self):
        name = self.d[0][0]
        learningname = self.studylistWidget.currentItem().text()
        print(learningname)

        learning_List = ['학습완료', learningname, name]
        testlist = json.dumps(learning_List)
        self.client_socket.send(testlist.encode())
        print(learning_List, "서버에게 보내줘")

    # 학생 불러오기 버튼클릭시 학습내역 부르기
    def learningload(self):
        # self.learning_list.clear()
        name = self.d[0][0]
        learningload_List = ['불러오기', name]
        testlist = json.dumps(learningload_List)
        self.client_socket.send(testlist.encode())
        print(learningload_List, "서버에게 보내줘")

    # 나의 진행상황 및 학습내용
    def mypage(self):
        self.stackedWidget_2.setCurrentIndex(3)

        name = self.d[0][0]
        page_List = ['마이페이지', name]
        testlist = json.dumps(page_List)
        self.client_socket.send(testlist.encode())
        print(page_List, "서버에게 보내줘")

        page_List = ['나의등급', name]
        testlist = json.dumps(page_List)
        self.client_socket.send(testlist.encode())
        print(page_List, "서버에게 보내줘","@@@@@@@@@@@@@@@")

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = log()
    myWindow.show()
    app.exec_()
