from socket import *
from threading import *
import pymysql as p
import json
import time
import datetime
import threading

# 서버
class ser:
    def __init__(self):
        self.clients=[]
        self.final_received_message = ""
        self.s_sock = socket(AF_INET,SOCK_STREAM)
        self.ip = ''
        self.port= 9797
        self.s_sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        self.s_sock.bind((self.ip,self.port))
        print("클라이언트 대기중...")
        self.s_sock.listen(100)
        self.accept_client()

    def accept_client(self):
        while True:
            client = c_socket, (ip,port) = self.s_sock.accept()
            if client not in self.clients:
                self.clients.append(client)
            print(ip,":",str(port),'가 연결되었습니다')
            # 받는 메시지 스레드로 받아옴
            cth = Thread(target=self.receive_messages,args=(c_socket,),daemon=True)
            cth.start()



    def receive_messages(self, c_socket):
        while True:
            try:
                # 받는메시지
                incoming_message = c_socket.recv(999)
                if not incoming_message:
                    break
            except:
                continue
            else:
                self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                                      db='ap', charset='utf8')
                self.cursor = self.conn.cursor()



                # 마지막에 받는 메시지를 채팅 db에 저장
                self.final_received_message = json.loads(incoming_message.decode())
                print(self.final_received_message)

                # 상담하기시 상담한 내용을 db에 저장 [1]은 이름 [2]는 메시지
                if '상담하기' in self.final_received_message:
                    self.cursor.execute(f"INSERT INTO consult values('{self.final_received_message[1]}','{self.final_received_message[2]}')")
                    self.conn.commit()
                # 문의하기 문의한 내용을 db에 저장 [1]은 이름 [2]는 문의내용 [3]은 문의한 연도,월,일
                elif '문의하기' in self.final_received_message:
                    self.cursor.execute(f"INSERT INTO qnaboard (ID,message,time) values('{self.final_received_message[1]}','{self.final_received_message[2]}','{self.final_received_message[3]}')")
                    self.conn.commit()

                    self.cursor.execute("select * from qnaboard")
                    # 해당학생의 모든 문의내역을 송신하는 메서드
                    self.q(c_socket)
                # 교수용클라이언트에서 답변내용을 서버에 송신하면 해당답변을 db에 저장함
                elif 'QnA' in self.final_received_message:
                    self.cursor.execute(f"update qnaboard set answer='{self.final_received_message[2]}' where message='{self.final_received_message[1]}'")
                    self.conn.commit()

                    self.cursor.execute("select * from qnaboard")
                    # 전체문의 내역을 선생용 클라이언트에 송신하는 메서드
                    self.tea(c_socket)
                # 문제업데이트를 선생용 클라이언트에서 요청했을 경우 문제를 추가
                elif '문제' == self.final_received_message[0]:
                    # qu는 문제내용 an은 o,x 정답 type은 등급,종류,종합의 문제유형
                    self.cursor.execute(f"INSERT INTO exam(qu,an,type) values('{self.final_received_message[1]}','{self.final_received_message[2]}','{self.final_received_message[3]}')")
                    self.conn.commit()

                    self.cursor.execute("select * from exam")
                    # 전체 문제내역을 선생용 클라이언트에 송신
                    self.prob(c_socket)


                # 마이페이지라는 메시지를 수신받으면
                # 메인페이지,푼유형,맞은갯수,푼 갯수 내역을 보내줌
                elif '마이페이지' in self.final_received_message:
                    self.my(c_socket)

                # 문제풀이시 db저장+ db에 맞은갯수 총 문제 푼 갯수 업데이트
                elif '문제풀이' in self.final_received_message:
                    # 문제풀이시 db에 시작한 시각을 db에 저장
                    n = datetime.datetime.now()
                    b = n.strftime('%H:%M')
                    # [1]은 이름 [2]는 문제유형(등급,종류,종합)
                    self.cursor.execute(f"select * from result2 where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                    self.ff = self.cursor.fetchall()
                    # (len=0)-해당유형문제를 푼적이 없을 경우 이름,유형,맞은갯수, 문제푼갯수, 시작시간을 db에 저장
                    if len(self.ff) == 0:

                        self.cursor.execute(f"INSERT INTO result2 (name,tp,hit,total,start) values('{self.final_received_message[1]}','{self.final_received_message[2]}',0,0,'{b}')")
                        self.conn.commit()
                        # qu는 문제 [3]도 문제 exam db에서 ee[0][1]은 o,x의 답이 나와있음
                        self.cursor.execute(f"select * from exam where qu='{self.final_received_message[3]}'")
                        self.ee = self.cursor.fetchall()
                        # 정답인 [0][1]과 학생용클라이언트가 작성한 ox체크([4])와 값을 비교
                        if self.ee[0][1] == self.final_received_message[4]:
                            print("정답")
                            # 정답일경우 hit은 맞은 갯수를 의미함 맞은갯수를 1증가시킴 [1]은 학생이름. [2]는 문제유형(등급,종류,종합)
                            self.cursor.execute(f"update result2 set hit=hit+1 where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                            self.conn.commit()
                            # total은 총 문제 푼 갯수, 총문제 푼갯수를 1증가시켜줌
                            self.cursor.execute(f"update result2 set total=total+1 where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                            self.conn.commit()
                        else:
                            print("오답")
                            # 오답일 경우 맞지 않았으므로 hit은 증가시키지 않고 total(푼갯수)를 증가시켜줌

                            self.cursor.execute(f"update result2 set total=total+1 where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                            self.conn.commit()

                    else:
                        # 해당유형의 문제를 1번이라도 푼경우 len(self.ff)!=0임
                        # 1번이라도 해당유형의 문제를 풀면 위의 조건식에서 이름과 유형이 인설트 돼있으므로 나머지 total과 hit을 증가시켜주는 업데이트 쿼리문만 진행
                        self.cursor.execute(f"select * from exam where qu='{self.final_received_message[3]}'")
                        self.ee = self.cursor.fetchall()
                        if self.ee[0][1] != self.final_received_message[4]:
                            print("오답")

                            self.cursor.execute(f"update result2 set total=total+1 where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                            self.conn.commit()
                        else:
                            print("정답")
                            self.cursor.execute(f"update result2 set hit=hit+1 where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                            self.conn.commit()

                            self.cursor.execute(f"update result2 set total=total+1 where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                            self.conn.commit()
                    # score는 실시간 채점부분으로 실시간 채점이후에 학생용클라이언트에 실시간으로 정답을 체크하여 송신함
                    self.score(c_socket)
                    # 유형별문제를 풀었을떄 유형문제를 풀떄 걸린시간 유형별문제의 채점결과를 학생 클라이언트에 송신함
                    self.repeat(c_socket)
                # 해당곤충의 학습완료를 하면 db에 저장, [2]는 이름 [1]은 곤충이름
                elif '학습완료' in self.final_received_message:
                    self.cursor.execute(f"INSERT INTO study values('{self.final_received_message[2]}','{self.final_received_message[1]}')")
                    self.conn.commit()

                # 학생 클라이언트가 학습결과를 불러오도록 요청했을떄 , 학습한 내역을 학생클라이언트에 보냄
                elif '불러오기' in self.final_received_message:
                    self.lo(c_socket)
                # 클라이언트가 등급문제를 요청했을 때 등급유형 문제를 ['문제출제',문제1,문제2..]형식으로 보냄
                elif '등급' == self.final_received_message[0]:
                    self.cs(c_socket)
                elif '종류' == self.final_received_message[0]:
                    self.cs1(c_socket)
                elif '종합' == self.final_received_message[0]:
                    self.cs2(c_socket)
                # 선생용 클라이언트에서 전체성적내용을 요청하면 선생용 클라이언트에 전체성적내용을 송신함
                elif 'result2 테이블'==self.final_received_message[0]:
                    self.result2(c_socket)
                # 학생용 클라이언트에서 3가지 유형에 대한 총점으로 등급을 받고 싶을때 오는 메시지/ 1개의 유형만을 풀었을떄도 그 점수를 기준으로 등급을 송신함
                elif '나의등급'==self.final_received_message[0]:
                    # 전체 총점을 기준으로 등급을 계산하여 보내줌
                    self.my_grade(c_socket)

                self.send_all_clients(c_socket)
        c_socket.close()







    # 문제 출제 메서드, 등급유형 문제를 클라이언트에 송신함
    def cs(self, socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        # 등급문제를 리스트에 담아서 ['문제출제',문제1,문제2..] 형식으로 보냄
        self.cursor.execute("select * from ap.exam where type = '등급'")
        a = self.cursor.fetchall()
        message = ['문제출제']
        for i in range(0, len(a)):
            message.append(a[i][0])
        print(message)
        sendall_message = json.dumps(message)
        socket.sendall(sendall_message.encode())

    def cs1(self, socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()

        self.cursor.execute("select * from ap.exam where type = '종류'")
        a = self.cursor.fetchall()
        message = ['문제출제']
        for i in range(0, len(a)):
            message.append(a[i][0])
        print(message)
        sendall_message = json.dumps(message)
        socket.sendall(sendall_message.encode())
    def cs2(self, socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()

        self.cursor.execute("select * from ap.exam where type = '종합'")
        a = self.cursor.fetchall()
        message = ['문제출제']
        for i in range(0, len(a)):
            message.append(a[i][0])
        print(message)
        sendall_message = json.dumps(message)
        socket.sendall(sendall_message.encode())
    # 마이페이지의 메시지가 왔을때 메인페이지,유형,맞은갯수,푼갯수 내역을 포문으로 보내줌
    def my(self,socket):
        conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        cursor = conn.cursor()
        cursor.execute(f"select * from result2 where name = '{self.final_received_message[1]}'")

        c=cursor.fetchall()
        c1=len(c)

        try:
            for i in range(0,c1):
                #[1]은 유형 [2]는 맞은 갯수 [3]은 총 푼 갯수 [4]는 점수 [8]은 등급
                message = ['메인페이지', f'{c[i][1]}', f'{c[i][2]}', f'{c[i][3]}',f'{c[i][4]}',f'{c[i][8]}']
                print(message, "메인페이지!!!!!!!!")
                sendall_message = json.dumps(message)
                socket.sendall(sendall_message.encode())
                time.sleep(0.1)
        except:
            pass
    # 학생용 클라이언트에서 나의 총점에 관한 등급을 요청하였을 때 실행되는 메서드
    def my_grade(self,socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        # 1은 이름
        self.cursor.execute(f"select * from result2 where name='{self.final_received_message[1]}'")
        total = self.cursor.fetchall()
        total_len=len(total)

        try:
            # 해당학생의 유형별 점수를 더함 /[0][4]는 등급점수 [1][4]는 종류점수 [2][4]는 종합점수
            # 해당 방법은 1개유형만 풀었을시 [1][4] [2][4]가 없기 때문에 오류가 발생
            # score=int(total[0][4])+int(total[1][4])+int(total[2][4])
            score=0
            # 길이를 활용하여 스코어에 해당유형점수를 계속 더해줌
            for i in range(0,total_len):
                score+=int(total[i][4])
            print(score,"점수점수")





            # 총 점수로 등급을 나누어줌
            if 0<=score<120:
                self.total_grade='D'
            elif score<=180:
                self.total_grade = 'C'
            elif score<=240:
                self.total_grade = 'B'
            elif score<=300:
                self.total_grade = 'A'
            # [1]은 이름 score는 총점수 total_grade는 등급
            message = ['총등급',f'{self.final_received_message[1]}',score,f'{self.total_grade}']
            print(message, "총등급!!!!!!!!")
            sendall_message = json.dumps(message)
            socket.sendall(sendall_message.encode())
        except Exception as e:
            print(e)
            pass








    # 선생용 클라이언트에서 전체 성적내용을 요청받으면 전체 성적내용을 송신함
    def result2(self,socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()

        self.cursor.execute("select * from result2")

        j = self.cursor.fetchall()
        j1 = len(j)
        try:
            # 전체성적을 선생용클라이언트에 송신해줌
            for i in range(0, j1):
                # [0]은 학생이름 [1]은 유형, [2]는 맞은갯수 3은 문제 푼 갯수 4는 점수 5는 시작시간 6은 끝난시간 7은 걸린시간 8은 등급
                message = ['전체성적', f'{j[i][0]}', f'{j[i][1]}', f'{j[i][2]}', f'{j[i][3]}', f'{j[i][4]}', f'{j[i][5]}', f'{j[i][6]}', f'{j[i][7]}',f'{j[i][8]}']
                print(message, "전체성적!!!!!!!!")
                sendall_message = json.dumps(message)
                socket.sendall(sendall_message.encode())
                time.sleep(0.1)
        except:
            pass

    # 문제 전체를 선생용에 송신
    def prob(self,socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()

        self.cursor.execute("select * from exam")

        r = self.cursor.fetchall()
        r1 = len(r)
        try:
            # 전체문제를 선생용클라이언트에 송신해줌
            for i in range(0, r1):
                # [0]은 문제내용 [1]은 정답, [2]는 문제의 유형
                message = ['전체문제', f'{r[i][0]}', f'{r[i][1]}', f'{r[i][2]}']
                print(message, "전체문제!!!!!!!!")
                sendall_message = json.dumps(message)
                socket.sendall(sendall_message.encode())
                time.sleep(0.1)
        except:
            pass



    # 선생용 클라이언트에서 문의내역을 서버에 보내고 전체문의 내역을 서버가 송신해주는 메서드
    def tea(self,socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        self.cursor.execute("select distinct * from qnaboard")

        g = self.cursor.fetchall()
        g1=len(g)
        try:
            # 전체문의내역을 선생용클라이언트에 송신해줌
            for i in range(0, g1):
                # [0]은 이름 [1]은 학생문의 내역, [2]는 날짜 [3]은 선생님이 답변한 문의
                message = ['전체문의', f'{g[i][0]}', f'{g[i][1]}', f'{g[i][2]}', f'{g[i][3]}']
                print(message, "전체문의!!!!!!!!")
                sendall_message = json.dumps(message)
                socket.sendall(sendall_message.encode())
                time.sleep(0.1)
        except:
            pass


    def q(self,socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        # qnaboard는 문의내역을 담는 db 해당 학생이름의 모든 문의내역을 학생에 송신함
        self.cursor.execute(f"select distinct * from qnaboard where ID = '{self.final_received_message[1]}'")

        b = self.cursor.fetchall()
        b1=len(b)

        try:
            for i in range(0,b1):
                # [0]은 이름 [1]은 메시지, [2]는 날짜
                message=['질문내역',f'{b[i][0]}',f'{b[i][1]}',f'{b[i][2]}']
                print(message, "질문내역!!!!!!!!")
                sendall_message = json.dumps(message)
                socket.sendall(sendall_message.encode())
                time.sleep(0.1)
        except:
            pass

    # 학생클라이언트가 학습결과를 요청했을 경우 실행되는 메서드
    def lo(self,socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        # distinct는 중복제거를 위함 [1]은 이름
        self.cursor.execute(f"select distinct insect from study where name='{self.final_received_message[1]}'")
        self.l = self.cursor.fetchall()
        self.la=len(self.l)

        try:
            # db에 이름 곤충이름
            #      이름 곤충이름
            # 식으로 기록이 되어 여러개의 행을 보내야 하기 때문에 반복문 사용했음, self.la는 해당학생이 학습완료한 행의 길이를 의미함
            # 이름과 곤충으로 이루어진 행을 보냄
            for i in range(0,self.la):
                message = ['부르기', f'{self.final_received_message[1]}',f'{self.l[i][0]}']
                print(message, "실시간채점!!!!!!!!")
                sendall_message = json.dumps(message)
                socket.sendall(sendall_message.encode())
                # 포문으로 메시지를 여러개 보내기떄문에 한개만 읽히는 것을 방지하기 위해 타임슬립을 걸었음
                time.sleep(0.3)
        except:
            pass

    # 실시간 채점부분, 1문제를 풀떄마다 학생용 클라이언트에 메시지를 송신함
    def score(self, socket):
        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        #[3]은 문제를 의미
        self.cursor.execute(f"select * from exam where qu='{self.final_received_message[3]}'")
        self.ee = self.cursor.fetchall()
        # 정답과 [4](학생이 입력한답)이 맞다면 self.hit=정답 틀리면 오답이됨
        if self.ee[0][1] == self.final_received_message[4]:
            self.hit='정답'
        else:
            self.hit = '오답'
        # [3]은 문제 [4]는 학생용 클라이언트가 체크한답 self.hit은 해당값이 정답인지 오답인지 종합해서 메시지를 학생에 송신
        message = ['채점',f'{self.final_received_message[3]}',f'{self.final_received_message[4]}', f'{self.hit}']
        print(message, "실시간채점!!!!!!!!")
        sendall_message = json.dumps(message)
        socket.sendall(sendall_message.encode())
    def send_all_clients(self, senders_socket):

        for client in self.clients:
            socket, (ip, port) = client
            # 마지막으로 받은 메시지를 전부 클라이언트에게 보냄
            try:


                message = [f"{self.final_received_message[0]}", f"{self.final_received_message[1]}",f"{self.final_received_message[2]}"]
                sendall_message = json.dumps(message)
                socket.sendall(sendall_message.encode())


            except:
                pass

    # 해당유형의 문제를 모두 풀었을때 채점결과와 문제푸는 데 걸린시간을 db에 저장하고 그결과를 학생용 클라이언트에 송신하는 메서드
    def repeat(self,socket):

        self.conn = p.connect(host='localhost', port=3306, user='root', password='1234',
                              db='ap', charset='utf8')
        self.cursor = self.conn.cursor()
        # 시험문제를 나타내는 exam db에서 종류유형의 문제만 뽑음
        self.cursor.execute("SELECT * FROM ap.exam where type='종류'")
        ta = self.cursor.fetchall()
        # 종류유형의 문제의 갯수인 len을 변수에 저장
        a=len(ta)
        # 시험문제를 나타내는 exam db에서 등급유형의 문제만 뽑음
        self.cursor.execute("SELECT * FROM ap.exam where type='등급'")
        tb = self.cursor.fetchall()
        b=len(tb)

        self.cursor.execute("SELECT * FROM ap.exam where type='종합'")
        tc = self.cursor.fetchall()
        c = len(tc)

        # 채점결과를 담는 db result에 등급유형의 문제에 이름이 학생이 로그인 아이디인 db를 변수에 저장
        self.cursor.execute(f"SELECT * FROM result2 where tp='등급' and name='{self.final_received_message[1]}'")
        aa = self.cursor.fetchall()

        self.cursor.execute(f"SELECT * FROM result2 where tp='종류' and name='{self.final_received_message[1]}'")
        bb = self.cursor.fetchall()

        self.cursor.execute(f"SELECT * FROM result2 where tp='종합' and name='{self.final_received_message[1]}'")
        cc = self.cursor.fetchall()

        print('등급',aa)
        print('종류',bb)
        print('종합',cc)
        try:
            # aa[0][3]은 등급문제에 total즉 문제 푼갯수를 의미함 '8'이런식이므로 값비교 위해 int 씌움/ b는 등급 유형의 총 문제 갯수를 의미함
            # 즉 이조건문은 등급문제를 모두 풀었을때를 의미함
            if int(aa[0][3]) == b:

                n = datetime.datetime.now()
                ba = n.strftime('%H:%M')
                # end는 해당유형의 문제를 풀었을때의 시간을 기록해서 db에 담음  [1]은 이름 [2]는 유형
                self.cursor.execute(f"update result2 set end='{ba}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()
                # aa[0][5]는 리시브메시지에서 시작시간을 insert한 값임, :을기준으로/ [14,20]이런식으로 리스트를 만듬
                five1=aa[0][5]
                five=five1.split(":")
                # 위에서 aa(등급)를 업데이트를 했으므로 등급부분을 세렉트로 다시 한 번 호출함
                self.cursor.execute(f"SELECT * FROM result2 where tp='등급' and name='{self.final_received_message[1]}'")
                aa = self.cursor.fetchall()
                # aa[0][6]은 위에서 update한 끝나는시각
                six1=aa[0][6]
                six=six1.split(":")
                # 끝나는 시각의 시간에 60을 곱하고 분은 더해주고 시작시간도 동일한 식으로 더해준 이후에
                # 끝나는 시각에서 시작하는시간을 빼줌 , 빼주면 걸린 시간(분)이 나오게 됨
                k=(int(six[0])*60+int(six[1]))-(int(five[0])*60+int(five[1]))

                # 걸린 시간(fin)에 걸린시간을 저장함
                self.cursor.execute(f"update result2 set fin='{k}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                # 위와 동일하게 업데이트를 했으므로 select로 aa를 다시 갱신해줌
                self.cursor.execute(f"SELECT * FROM result2 where tp='등급' and name='{self.final_received_message[1]}'")
                aa = self.cursor.fetchall()

                # aa[0][2]는 맞은갯수 aa[0][3]은 총갯수 총갯수로 맞은갯수를 나누어 점수를 추출함
                ma=int(aa[0][2])/int(aa[0][3])*100
                m=int(ma)
                # 점수인 sc칼럼에 점수를 db에 저장
                self.cursor.execute(f"update result2 set sc='{m}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                self.cursor.execute(f"SELECT * FROM result2 where tp='등급' and name='{self.final_received_message[1]}'")
                aa = self.cursor.fetchall()


                # 점수별로 등급을 정하여 grade라는 칼람에 등급저장
                if 0<=m<40:
                    self.m_aa='D'
                elif m<=60:
                    self.m_aa='C'
                elif m<=80:
                    self.m_aa='B'
                elif m<=100:
                    self.m_aa='A'

                self.cursor.execute(f"update result2 set grade='{self.m_aa}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                self.cursor.execute(f"SELECT * FROM result2 where tp='등급' and name='{self.final_received_message[1]}'")
                aa = self.cursor.fetchall()

                print(aa[0][3],"1232")
                self.aa_mes=1

                # 이름,문제유형,맞은갯수,푼갯수,점수,걸린시간,등급
                message = ['결과',f'{aa[0][0]}',f'{aa[0][1]}',f'{aa[0][2]}',f'{aa[0][3]}',f'{aa[0][4]}',f'{aa[0][7]}',f'{aa[0][8]}']
                print(message,"등급메시지~~~~~~~~~~~~~~")

                sendall_message = json.dumps(message)
                socket.sendall(sendall_message.encode())


            # 등급문제를 모두 다 풀고 종류문제를 다풀었을시에 발생하는 조건문 /
            # 걸린시간과 점수구하는 방법은 위와 동일함
            if int(aa[0][3])==b and int(bb[0][3]) == a:
                n1 = datetime.datetime.now()
                ba1 = n1.strftime('%H:%M')

                self.cursor.execute(f"update result2 set end='{ba1}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()
                five2 = bb[0][5]
                five3 = five2.split(":")

                self.cursor.execute(f"SELECT * FROM result2 where tp='종류' and name='{self.final_received_message[1]}'")
                bb = self.cursor.fetchall()

                six2 = bb[0][6]
                six3 = six2.split(":")

                kk = (int(six3[0]) * 60 + int(six3[1])) - (int(five3[0]) * 60 + int(five3[1]))

                self.cursor.execute(f"update result2 set fin='{kk}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                self.cursor.execute(f"SELECT * FROM result2 where tp='종류' and name='{self.final_received_message[1]}'")
                bb = self.cursor.fetchall()

                mb = int(bb[0][2]) / int(bb[0][3]) * 100
                mm = int(mb)

                self.cursor.execute(f"update result2 set sc='{mm}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                self.cursor.execute(f"SELECT * FROM result2 where tp='종류' and name='{self.final_received_message[1]}'")
                bb = self.cursor.fetchall()

                # 점수별로 등급을 정하여 grade라는 칼람에 등급저장
                if 0 <= mm < 40:
                    self.m_bb = 'D'
                elif mm <= 60:
                    self.m_bb = 'C'
                elif mm <= 80:
                    self.m_bb = 'B'
                elif mm <= 100:
                    self.m_bb = 'A'

                self.cursor.execute(f"update result2 set grade='{self.m_bb}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                self.cursor.execute(f"SELECT * FROM result2 where tp='종류' and name='{self.final_received_message[1]}'")
                bb = self.cursor.fetchall()


                print(bb[0][3],"asdasd")
                message2 = ['결과',f'{bb[0][0]}',f'{bb[0][1]}',f'{bb[0][2]}',f'{bb[0][3]}',f'{bb[0][4]}',f'{bb[0][7]}',f'{bb[0][8]}']
                print(message2, "종류메시지~~~~~~~~~~~~~~")

                sendall_message2 = json.dumps(message2)
                socket.sendall(sendall_message2.encode())

            # 종류문제를 다풀고 종합(cc)문제를 다풀었을 때의 조건문
            # 걸린시간, 점수구하는 식은 위와 동일함
            if int(bb[0][3]) == a and int(cc[0][3]) == c:
                print("11111")
                print(cc[0][3],"ccc")
                n2 = datetime.datetime.now()
                ba2 = n2.strftime('%H:%M')

                self.cursor.execute(f"update result2 set end='{ba2}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                five4 = cc[0][5]
                five5 = five4.split(":")

                self.cursor.execute(f"SELECT * FROM result2 where tp='종합' and name='{self.final_received_message[1]}'")
                cc = self.cursor.fetchall()

                six4 = cc[0][6]
                six5 = six4.split(":")

                kkk = (int(six5[0]) * 60 + int(six5[1])) - (int(five5[0]) * 60 + int(five5[1]))

                self.cursor.execute(f"update result2 set fin='{kkk}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                self.cursor.execute(f"SELECT * FROM result2 where tp='종합' and name='{self.final_received_message[1]}'")
                cc = self.cursor.fetchall()

                mc = int(cc[0][2]) / int(cc[0][3]) * 100
                mmm = int(mc)

                self.cursor.execute(f"update result2 set sc='{mmm}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                self.cursor.execute(f"SELECT * FROM result2 where tp='종합' and name='{self.final_received_message[1]}'")
                cc = self.cursor.fetchall()

                # 점수별로 등급을 정하여 grade라는 칼람에 등급저장
                if 0 <= mmm < 40:
                    self.m_cc = 'D'
                elif mmm <= 60:
                    self.m_cc = 'C'
                elif mmm <= 80:
                    self.m_cc = 'B'
                elif mmm <= 100:
                    self.m_cc = 'A'

                self.cursor.execute(f"update result2 set grade='{self.m_cc}' where name = '{self.final_received_message[1]}' and tp='{self.final_received_message[2]}'")
                self.conn.commit()

                self.cursor.execute(f"SELECT * FROM result2 where tp='종합' and name='{self.final_received_message[1]}'")
                cc = self.cursor.fetchall()


                print(cc[0][3],"ㅁㄴㅇㄴㅁㅇ")
                message3 = ['결과', f'{cc[0][0]}', f'{cc[0][1]}', f'{cc[0][2]}', f'{cc[0][3]}',f'{cc[0][4]}',f'{cc[0][7]}',f'{cc[0][8]}']
                print(message3,"종합메시지~~~~~~~~")

                sendall_message3 = json.dumps(message3)
                socket.sendall(sendall_message3.encode())
        except Exception as e:
            print(e)
            pass

if __name__=="__main__":
    ser()

