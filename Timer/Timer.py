"""タイマーを自作したい"""
from genericpath import exists
import threading
import time
import dataclasses
from typing import (Type,Callable)

from grpc import Call

@dataclasses.dataclass
class Alarm:
    alarm_time: float|None
    command: Callable
    delete: bool
    args: tuple | list
    kwargs: dict
    tag : str
    performed: bool = False
    effective: bool = True #アラームが有効かどうか
    conditional_expression: Callable[[float,float],bool]|None = None  # (last_time,current_time)を引数にとってboolを返す

class Timer:
    """タイマー(精度は0.01%程度？で、0.01秒に一度しか更新しない)

    Attributes
    -----------
    start_time : float
        タイマーの初期時間,by default 0
    reverse : bool
        時間が増える方向か減る方向か
    current_time : float
        set_current_timeを最後に動かした時点でのタイマーの時間
    is_running :bool
        タイマーが動いているか
    """

    def __init__(self, start_time: float = 0, reverse: bool = False):
        """タイマー

        Parameters
        ----------
        start_time : float, optional
            はじめのスタート時間, by default 0
        reverse : bool, optional
            時間が増える方向に進むか減るほうに進むか, by default False
        """
        self.start_time: float = start_time
        self.reverse: bool = reverse
        self.current_time: float = start_time
        self.is_running: bool = False
        self.last_update_time: float=time.time()
        self.last_current_time : float=start_time
        self.lock = threading.Lock()
        self.update_thread = threading.Thread(target=self.update)
        self.update_thread.daemon = True
        self.is_update = True #アップデートをするか
        self.alarm_list: list[Alarm] = []
        self.update_thread.start()
        self.was_new_update=False

    def __del__(self):
        self.stop_update()

    def update(self):
        try:
            while True:
                time.sleep(0.01)
                with self.lock:
                    if not self.is_update:
                        raise ValueError
                    if not self.is_running:
                        pass
                    else:
                        self.last_current_time=self.current_time
                        if not self.reverse:
                            self.current_time += time.time()-self.last_update_time
                        else:
                            self.current_time -= time.time()-self.last_update_time
                        self.last_update_time = time.time()
                        self.was_new_update=True
                # print(self.current_time)
        except:
            pass

    def stop_update(self):
        with self.lock:
            self.is_update = False

    def start(self):
        """止まっているタイマーを再開する
        """
        if self.is_running:
            pass
        else:
            self.is_running = True
            self.last_update_time = time.time()

    def stop(self):
        """タイマーを一時停止する
        """
        if not self.is_running:
            pass
        else:
            self.is_running = False

    def reset(self):
        """スタート時間に戻す
        """
        self.current_time = self.start_time
        for alarm in self.alarm_list[:]:
            alarm.performed = False
    
    def set_start_time(self,start_time):
        self.start_time=start_time
        
    def set_alarm(self, alarm):
        """alarmを追加する
        
        Parameters
        ----------
        alarm : Alarm
        """
        self.alarm_list.append(alarm)

    def do_alarm(self):
        """set_alarm関数でalarm_listに加えられた関数を実行する
        """
        if self.was_new_update:
            self.was_new_update=False
            for alarm in self.alarm_list[:]:
                flag=False
                #alarm_timeが設定されている場合の処理
                if not alarm.alarm_time is None:
                    if not self.reverse and self.current_time > alarm.alarm_time and not alarm.performed and alarm.effective:
                        flag=True
                    elif self.reverse and self.current_time < alarm.alarm_time and not alarm.performed and alarm.effective:
                        flag=True
                #条件式が設定されている場合の処理
                if not alarm.conditional_expression is None:
                    if alarm.conditional_expression(self.last_current_time,self.current_time):
                        flag=True
                if flag:
                    alarm.command(*alarm.args, **alarm.kwargs)
                    alarm.performed = True
                    if alarm.delete:
                        self.alarm_list.remove(alarm)
                            
    def get_time(self):
        return self.current_time


def print_test(timer:Timer):
    print(timer.get_time())

def cord(a,b):
    return int(a)!=int(b)

def test():
    timer = Timer(0, reverse=False)
    alarm=Alarm(None,print_test,False,(timer,),{},'',False,True,cord)
    timer.set_alarm(alarm)
    timer.start()
    while True:
        timer.do_alarm()
        if timer.get_time() > 3:
            break
    timer.reset()
    timer.stop_update()
    del timer


if __name__ == "__main__":
    test()
