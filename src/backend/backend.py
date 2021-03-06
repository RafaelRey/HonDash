import asyncio
import json
import threading

import websockets

from devices.kpro.kpro import Kpro
from devices.odometer import Odometer
from devices.setup_file import SetupFile
from devices.style import Style
from devices.time import Time
from version import __version__


class Backend:
    def __init__(self):
        self._load_user_preferences()
        self._init_resources()
        self._init_websocket()

    def stop(self):
        self.websocket.stop()

    def _init_websocket(self):
        self.websocket = Websocket(self)

    def _init_resources(self):
        self.time = Time()
        self.odo = Odometer()
        self.kpro = Kpro()

    def _load_user_preferences(self):
        """
        In order to read only once from the setup file
        we will load in memory some user preferences that we are gonna use later on.
        """
        self.setup_file = SetupFile()

        self.style = Style(
            self.setup_file.json.get("style").get("tpsLowerThreshold"),
            self.setup_file.json.get("style").get("tpsUpperThreshold"),
            self.setup_file.json.get("style").get("elapsedSeconds"),
        )

        self.iat_unit = self.setup_file.json.get("iat", {}).get("unit", "celsius")
        self.ect_unit = self.setup_file.json.get("ect", {}).get("unit", "celsius")
        self.vss_unit = self.setup_file.json.get("vss", {}).get("unit", "kmh")
        self.o2_unit = self.setup_file.json.get("o2", {}).get("unit", "afr")
        self.odo_unit = self.setup_file.json.get("odo", {}).get("unit", "km")
        self.map_unit = self.setup_file.json.get("map", {}).get("unit", "bar")
        self.an0_unit = self.setup_file.json.get("an0", {}).get("unit", "volts")
        self.an1_unit = self.setup_file.json.get("an1", {}).get("unit", "volts")
        self.an2_unit = self.setup_file.json.get("an2", {}).get("unit", "volts")
        self.an3_unit = self.setup_file.json.get("an3", {}).get("unit", "volts")
        self.an4_unit = self.setup_file.json.get("an4", {}).get("unit", "volts")
        self.an5_unit = self.setup_file.json.get("an5", {}).get("unit", "volts")
        self.an6_unit = self.setup_file.json.get("an6", {}).get("unit", "volts")
        self.an7_unit = self.setup_file.json.get("an7", {}).get("unit", "volts")

        self.an0_formula = self.setup_file.get_formula("an0")
        self.an1_formula = self.setup_file.get_formula("an1")
        self.an2_formula = self.setup_file.get_formula("an2")
        self.an3_formula = self.setup_file.get_formula("an3")
        self.an4_formula = self.setup_file.get_formula("an4")
        self.an5_formula = self.setup_file.get_formula("an5")
        self.an6_formula = self.setup_file.get_formula("an6")
        self.an7_formula = self.setup_file.get_formula("an7")

    def update(self):
        """ load the websocket with updated info """
        if not self.kpro.status:  # if kpro is down try to reconnect
            self.kpro.find_and_connect()
        self.odo.save(self.kpro.vss["kmh"])
        self.style.update(self.kpro.tps)
        return {
            "bat": self.kpro.bat,
            "gear": self.kpro.gear,
            "iat": self.kpro.iat[self.iat_unit],
            "tps": self.kpro.tps,
            "ect": self.kpro.ect[self.ect_unit],
            "rpm": self.kpro.rpm,
            "vss": self.kpro.vss[self.vss_unit],
            "o2": self.kpro.o2[self.o2_unit],
            "cam": self.kpro.cam,
            "mil": self.kpro.mil,
            "fan": self.kpro.fanc,
            "bksw": self.kpro.bksw,
            "flr": self.kpro.flr,
            "eth": self.kpro.eth,
            "scs": self.kpro.scs,
            "fmw": self.kpro.firmware,
            "map": self.kpro.map[self.map_unit],
            "an0": self.an0_formula(self.kpro.analog_input(0))[self.an0_unit],
            "an1": self.an1_formula(self.kpro.analog_input(1))[self.an1_unit],
            "an2": self.an2_formula(self.kpro.analog_input(2))[self.an2_unit],
            "an3": self.an3_formula(self.kpro.analog_input(3))[self.an3_unit],
            "an4": self.an4_formula(self.kpro.analog_input(4))[self.an4_unit],
            "an5": self.an5_formula(self.kpro.analog_input(5))[self.an5_unit],
            "an6": self.an6_formula(self.kpro.analog_input(6))[self.an6_unit],
            "an7": self.an7_formula(self.kpro.analog_input(7))[self.an7_unit],
            "time": self.time.get_time(),
            "odo": self.odo.get_mileage()[self.odo_unit],
            "style": self.style.status,
            "ver": __version__,
        }

    def setup(self):
        """Return the current setup"""
        return self.setup_file.load_setup()

    def save(self, new_setup):
        """Save a new setup"""
        self.setup_file.save_setup(new_setup)
        self.setup_file.rotate_screen(new_setup["screen"]["rotate"])
        self._load_user_preferences()  # refresh the backend too

    def reset(self):
        """Reset to the default setup"""
        self.setup_file.reset_setup()
        self._load_user_preferences()  # refresh the backend too


class Websocket:
    clients_connected = set()
    backend = None

    def __init__(self, backend):
        self.backend = backend
        self.websocket = websockets.serve(self._websocket_handler, "0.0.0.0", 5678)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.websocket)
        threading.Thread(target=self.loop.run_forever).start()

    async def _websocket_handler(self, websocket, path):
        await self._register(websocket)  # register this client to keep tracking of it
        consumer_task = asyncio.ensure_future(self._consumer_handler(websocket))
        producer_task = asyncio.ensure_future(self._producer_handler(websocket))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    async def _consumer_handler(self, websocket):
        """Here is where messages from clients are processed"""
        async for message in websocket:
            data = json.loads(message)
            if data["action"] == "setup":
                await websocket.send(json.dumps({"setup": self.backend.setup()}))
            elif data["action"] == "save":
                self.backend.save(data["data"])
                # send refresh action to all the frontends so the new changes are applied
                await self._send_all_clients(json.dumps({"action": "refresh"}))
            elif data["action"] == "reset":
                self.backend.reset()
                # send refresh action to all the frontends so the new changes are applied
                await self._send_all_clients(json.dumps({"action": "refresh"}))

    async def _producer_handler(self, websocket):
        """Keeps sending updated kpro data forever"""
        while True:
            await websocket.send(json.dumps({"data": self.backend.update()}))
            await asyncio.sleep(0.1)

    async def _send_all_clients(self, message):
        """Broadcast to all the clients"""
        if self.clients_connected:  # asyncio.wait doesn't accept an empty list
            await asyncio.wait([user.send(message) for user in self.clients_connected])

    async def _register(self, websocket):
        """Appends a new client to the connected clients list"""
        self.clients_connected.add(websocket)

    def stop(self):
        self.websocket.ws_server.close()
        self.loop.call_soon_threadsafe(self.loop.stop)


if __name__ == "__main__":
    # if the file is getting executed then start the backend behaviour
    backend = Backend()
