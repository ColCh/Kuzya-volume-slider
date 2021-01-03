import asyncio
import sys
import typing
import logging
import webbrowser

import pyqrcode

import app_websocket
import win32_volume_utils
from win32_volume_utils import (VolumeController, get_process_displayed_name)
from get_local_ip import get_local_ip

APP_HOST = get_local_ip(mode='v4')
APP_PORT = 8080

USER_INTERFACE = "http://{}:{}".format(APP_HOST, APP_PORT)

# -------------- initial echo
print('/*******************************************')
print(' *             HELLO KUZYA                 *')
print(' *           THIS IS YOUR URL              *')
print(f'  ---->      {USER_INTERFACE}      <---- ')
print(' *******************************************/')

print('')
print('')
print('')

url = pyqrcode.create(USER_INTERFACE)
url.png('kuzya_volume_slider.png',
        scale=6,
        module_color=[0, 0, 0, 128],
        background=[0xff, 0xff, 0xcc])
# ------------- echo end

# redirect logs into file for PyInstaller bundle and open browser with this page
if getattr(sys, 'frozen', False):
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='kuzya_volume_slider.log', level=logging.INFO)
    webbrowser.open_new_tab(USER_INTERFACE)
else:
    logger = logging.getLogger('main_module')
    ch = logging.StreamHandler()
    logging.basicConfig(
        handlers=[ch],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
    )

# FIXME: async function from sync function
volume_changed_queue = list()


def handle_win32_volume_change(volume_controller: VolumeController):
    volume_level = volume_controller.volume
    controller_name = volume_controller.display_name
    logger.info(f'{controller_name} volume level changed to {volume_level}')
    volume_changed_queue.append(volume_controller)


volume_controllers: typing.Dict[str, VolumeController] = dict()
volume_controllers_levels: typing.Dict[str, float] = dict()

main_volume_controller = VolumeController(
    win_volume=win32_volume_utils.get_audio_endpoint_volume(),
    win_identifier='entire system volume',
    display_name='system volume',
)

# always exists
volume_controllers[main_volume_controller.id] = main_volume_controller
volume_controllers_levels[
    main_volume_controller.id] = main_volume_controller.volume


async def emit_sliders():
    await app_websocket.sio.emit('sliders', [
        volume_controller.as_dict()
        for (id, volume_controller) in volume_controllers.items()
    ])


@app_websocket.sio.event
async def connect(sid, environ):
    logger.info('send current sliders for connected user')
    await emit_sliders()


@app_websocket.sio.event
async def volumeChanged(sid, data):
    logger.info('volume changed event from frontend')
    logger.info(data)
    if data['id'] not in volume_controllers:
        logger.info('no such controller in collection')
        return
    volume_controller = volume_controllers[data['id']]
    volume_controller.volume = data['currentValue']


async def start_app():
    logger.info('start main app')
    while (True):
        logger.info('do volume scan')
        volume_scan_result = win32_volume_utils.scan_volume_sessions()

        logger.info('handle {} added channels'.format(
            len(volume_scan_result['added'])))
        for added_volume_channel in volume_scan_result['added']:
            controller_uuid = VolumeController.get_uuid_by_win_identifier(
                added_volume_channel.Identifier)

            if controller_uuid in volume_controllers:
                continue

            controller_displayed_name = get_process_displayed_name(
                added_volume_channel.Process
            ) if added_volume_channel.Process else 'system sounds'

            volume_controller = VolumeController(
                win_volume=added_volume_channel.SimpleAudioVolume,
                win_identifier=added_volume_channel.Identifier,
                display_name=controller_displayed_name,
            )

            volume_controllers[volume_controller.id] = volume_controller
            volume_controllers_levels[
                volume_controller.id] = volume_controller.volume

            logger.info('add new volume controller')
            logger.info(volume_controller.as_dict())

        logger.info('handle {} removed channels'.format(
            len(volume_scan_result['removed'])))
        for removed_volume_channel in volume_scan_result['removed']:

            controller_uuid = VolumeController.get_uuid_by_win_identifier(
                added_volume_channel.Identifier)

            if controller_uuid not in volume_controllers:
                continue

            volume_controller = volume_controllers[controller_uuid]

            logger.info('delete volume controller')
            logger.info(volume_controller.as_dict())

            del volume_controllers[controller_uuid]
            del volume_controllers_levels[controller_uuid]

        to_scan_for_changed_volume = [main_volume_controller]
        logger.info('handle {} may be changed volume levels'.format(
            len(volume_scan_result['other'])))
        for other_volume_channel in volume_scan_result['other']:

            controller_uuid = VolumeController.get_uuid_by_win_identifier(
                added_volume_channel.Identifier)

            if controller_uuid not in volume_controllers:
                logger.info(f'skip controller {controller_uuid} (not exists)')
                continue

            volume_controller = volume_controllers[controller_uuid]

            to_scan_for_changed_volume.append(volume_controller)

        for volume_controller in to_scan_for_changed_volume:

            current_volume_controller_volume = volume_controller.volume

            if volume_controller.id not in volume_controllers_levels:
                logger.info(
                    f'skip controller {volume_controller.id} (not exists)')
                continue

            if current_volume_controller_volume == volume_controllers_levels[
                    volume_controller.id]:
                logger.info(
                    f'skip controller {volume_controller.id} (volume is same)')
                continue

            logger.info('{} volume changed from {} to {}'.format(
                volume_controller.display_name,
                volume_controllers_levels[volume_controller.id],
                current_volume_controller_volume))

            volume_controllers_levels[
                volume_controller.id] = current_volume_controller_volume

            await app_websocket.sio.emit('adjustVolume',
                                         volume_controller.as_dict())

        await emit_sliders()

        await asyncio.sleep(1)
    pass


async def start_webapp():
    logger.info('start webapp')
    app_websocket.set_html_file_initial_data({
        "host": APP_HOST,
        "port": APP_PORT,
    })
    await app_websocket.runner.setup()
    site = app_websocket.web.TCPSite(app_websocket.runner, APP_HOST, APP_PORT)
    await site.start()


async def main():
    logger.info('start main()')
    await asyncio.gather(start_webapp(), start_app())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)
