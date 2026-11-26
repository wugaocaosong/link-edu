"""Browser rehearsal using a disposable database, synthetic media and local provider doubles.

Build frontend first. Requires Python Playwright, Chromium and ffprobe.
"""
import argparse
import base64
import json
import logging
import queue
import subprocess
import sys
import tempfile
import threading
import zipfile
from pathlib import Path
from unittest.mock import patch

import websocket
from flask import send_from_directory
from flask_jwt_extended import create_access_token
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app import create_app
from extensions import db
from models import User
from services.study_review import issue_document
from study_models import StudyParticipant, StudyAttempt
from tenancy import personal_tenant_for


class LocalASR:
    def __init__(self, sid):
        self.queue = queue.Queue()
        self.sent = False

    def receive(self):
        try:
            return self.queue.get(timeout=.1)
        except queue.Empty:
            raise websocket.WebSocketTimeoutException()

    def audio(self, encoded):
        if not self.sent:
            self.queue.put(dict(type='final', transcript='小林，这一份是多少呢？', item_id='synthetic'))
            self.sent = True

    def finish(self):
        self.queue.put(dict(type='finished'))

    def close(self):
        pass

    def settle(self):
        pass

    def drain_expired(self, started, now):
        return now-started > 3


def check_media(package, directory, blind):
    with zipfile.ZipFile(package) as z:
        videos = [n for n in z.namelist() if n.endswith(('.webm','.mp4'))]
        assert videos
        if blind:
            assert len(z.namelist()) == 2 and len(Path(videos[0]).stem) == 32
        for name in videos:
            path = directory / Path(name).name
            path.write_bytes(z.read(name))
            probe = subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type',
                                             '-of','json',str(path)])
            assert {s['codec_type'] for s in json.loads(probe)['streams']} == {'audio','video'}


def rehearse(page, app, tmp):
    page.set_default_timeout(20000)
    button = lambda name: page.get_by_role('button', name=name, exact=True)
    for stage in ('pre','round1','round2','post'):
        page.get_by_label('已核对场次安排',exact=False).check()
        button('进入场次').click()
        if stage in ('pre','post'):
            button('检查设备').click()
            button('开始 5 分钟测评').click()
            button('标记机会 1').click()
            page.wait_for_timeout(3500)
            button('标记机会 2').click()
            button('提前结束').click()
            page.get_by_label('扮演者编号').fill('QA')
            page.get_by_label('现场异常与受影响的机会').fill('合成设备短场试跑')
            page.get_by_label('已回放核对',exact=False).check()
            with page.expect_download() as dl:
                button('导出盲评包并提交').click()
            check_media(dl.value.path(), tmp, True)
        else:
            page.get_by_role('link',name='进入虚拟学生课堂').click()
            page.locator('[data-tour="prepare"]').first.click()
            page.get_by_label('同意语音识别与 AI 评课').check()
            page.get_by_label('同意摄像头开启').check()
            page.get_by_role('dialog').get_by_role('button',name='开始授课').click()
            button('结束并评课').click(timeout=45000)
            page.get_by_role('link',name='填写独立自评').click()
            page.get_by_label('你想回看哪次师生回应？').fill('核对这次回答')
            page.get_by_label('距开课的时间',exact=False).fill('3')
            page.get_by_label('本场提前结束',exact=False).fill('缩时联调')
            button('保存独立自评').click()
            button('刷新报告').wait_for()
            with app.app_context():
                row=StudyAttempt.query.filter_by(stage=stage).one()
                assert len(row.packet['transcript'])>=2, row.packet
                report=issue_document(row.id, row.packet)
                path=tmp/'report.json'
                path.write_text(json.dumps(report))
                assert app.test_cli_runner().invoke(args=['study','issue',str(row.id),str(path)]).exit_code==0
            button('刷新报告').click()
            page.get_by_label('回看训练录像').wait_for()
            button('定位自评片段').click()
            with page.expect_download() as dl:
                button('导出本轮录像与记录').click()
            check_media(dl.value.path(),tmp,False)
            page.get_by_label('已阅读报告',exact=False).check()
            if stage=='round1':
                page.get_by_label('下一次准备改进的一件事').fill('先追问理由')
            button('完成本轮反馈').click()
        print(stage, 'OK', flush=True)
    page.get_by_text('全部场次已完成。').wait_for()


def main(tmp, arm):
    class Config:
        TESTING=True
        SQLALCHEMY_DATABASE_URI='sqlite:///'+(tmp/'rehearsal.db').as_posix()
        JWT_SECRET_KEY='temporary-local-fraction-study-rehearsal'
    app=create_app(Config)
    dist=ROOT/'frontend/dist'
    @app.get('/<path:path>')
    def frontend(path):
        return send_from_directory(dist,path if (dist/path).is_file() else 'index.html')
    with app.app_context():
        db.create_all()
        user=User(account='qa-study',name='试跑',password_hash='unused')
        db.session.add(user);db.session.flush()
        tenant=personal_tenant_for(user)
        db.session.add(StudyParticipant(tenant_id=tenant.id,user_id=user.id,code='QA01',
                                       experience=False,arm=arm,first_form='A' if arm=='multimodal' else 'B'))
        db.session.commit()
        token=create_access_token(identity=str(user.id))
    server=make_server('127.0.0.1',0,app,threaded=True)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=pw.chromium.executable_path,
                args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--autoplay-policy=no-user-gesture-required'])
            ctx=browser.new_context(permissions=['microphone','camera'])
            ctx.add_init_script(f"localStorage.setItem('link_token',{json.dumps(token)})")
            ctx.add_init_script("""navigator.mediaDevices.getUserMedia = async ({audio,video})=>{
                const tracks=[];
                if(video){
                    const canvas=document.createElement('canvas');canvas.width=320;canvas.height=240;
                    const c=canvas.getContext('2d'); const draw=()=>{c.fillStyle='#7f6253';c.fillRect(0,0,320,240);c.fillStyle='white';c.fillText(String(performance.now()),10,26)};
                    draw();const t=canvas.captureStream(15).getVideoTracks()[0];
                    const timer=setInterval(draw,66);const stop=t.stop.bind(t);t.stop=()=>{clearInterval(timer);stop()};tracks.push(t)
                }
                if(audio){
                    const ctx=new AudioContext();await ctx.resume();const dest=ctx.createMediaStreamDestination();
                    const osc=ctx.createOscillator();osc.connect(dest);osc.start();
                    const t=dest.stream.getAudioTracks()[0];const stop=t.stop.bind(t);
                    t.stop=()=>{if(t.readyState!=='ended'){osc.stop();ctx.close();stop()}};tracks.push(t)
                }
                return new MediaStream(tracks)
            }""")
            page=ctx.new_page()
            page.on('dialog',lambda d:d.accept())
            page.on('pageerror',lambda error:print('page error:',error,flush=True))
            page.goto(f'http://127.0.0.1:{server.server_port}/study')
            try:
                rehearse(page,app,tmp)
            except Exception:
                print(page.locator('body').inner_text()[-2200:], flush=True)
                raise
            browser.close()
    finally:
        server.shutdown()
        with app.app_context():
            db.engine.dispose()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm',choices=['transcript','multimodal'],default='multimodal')
    args=parser.parse_args()
    description={'configured':True,'pricing_confirmed':True,'provider':'fixture'}
    budget={'stopped':False,'warning':False,'pricing_confirmed':True}
    def answer(system,data,*args):
        return {'action':'answer','student_id':data['named_student'],'text':'我觉得是一半。'}
    def speak(text,sid,voice,cancel,callback):
        callback(base64.b64encode(b'\x10\x02'*12000).decode(),24000)
    with (tempfile.TemporaryDirectory() as temp, patch('services.classroom_runtime.ASR',LocalASR),
          patch('services.classroom_runtime.chat_stream',answer),patch('services.classroom_runtime.speak',speak),
          patch('classroom_routes.describe',return_value=description),
          patch('services.classroom_budget.status',return_value=budget),
          patch('services.classroom_runtime.budget_status',return_value=budget)):
        main(Path(temp), args.arm)
