import json
import logging

from aiohttp import web
import socketio

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)


@sio.event
def connect(sid, environ):
    logger.info("connect {}".format(sid))


@sio.event
def disconnect(sid):
    logger.info('disconnect {}'.format(sid))


html_file_initial_data = dict()


def set_html_file_initial_data(new_initial_data):
    global html_file_initial_data

    # если нельзя перевести в json - кинет ошибку
    json.dumps(new_initial_data)

    html_file_initial_data = new_initial_data
    logger.info('set new initial data from {} to {}'.format(
        html_file_initial_data, new_initial_data))


async def index(request):
    global html_file_initial_data

    with open('page.html', encoding='utf-8') as f:
        file_text_raw = f.read()
        file_text_replaced = file_text_raw.replace(
            '$INITIAL_DATA$', json.dumps(html_file_initial_data))
        return web.Response(text=file_text_replaced, content_type='text/html')


app.router.add_get('/', index)

runner = web.AppRunner(app)

__all__ = [sio, app, runner, set_html_file_initial_data]
