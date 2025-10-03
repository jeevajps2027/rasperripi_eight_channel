import asyncio
import serial
import json
import threading
import time
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
import sys

class SerialConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'serial_group'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.serial_connections = {}  # Store COM port connections
        self.serial_threads = {}      # Store threads per COM port
        self.previous_data = {}       # Store last message per COM port
        self.printed_lines = {}       # Track printed COM ports
        self.card_names = {}          # Store card name per COM port
        self.serial_lock = threading.Lock()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command')

        if command in ['start_serial', 'start_communication']:
            await self.start_serial_communication(data)

    async def start_serial_communication(self, data):
        com_port = data.get('com_port')
        baud_rate = data.get('baud_rate')
        parity = data.get('parity')
        stopbits = data.get('stopbit')
        bytesize = data.get('databit')
        card = data.get("card")

        self.card_names[com_port] = card  # Store card name for COM port

        if com_port in self.serial_connections:
            print(f"{com_port} is already running.")
            return

        if await self.configure_serial_port(com_port, baud_rate, parity, stopbits, bytesize):
            command_message = "MMMMMMMMMM"  # Example command to send
            self.serial_connections[com_port].write(command_message.encode('ASCII'))

            serial_thread = threading.Thread(
                target=self.serial_read_thread,
                args=(com_port,),
                daemon=True
            )
            self.serial_threads[com_port] = serial_thread
            serial_thread.start()

    async def configure_serial_port(self, com_port, baud_rate, parity, stopbits, bytesize):
        try:
            if not all([com_port, baud_rate, parity, stopbits, bytesize]):
                print("Missing parameters.")
                return False

            ser = serial.Serial(
                port=com_port,
                baudrate=int(baud_rate),
                bytesize=int(bytesize),
                timeout=None,
                stopbits=float(stopbits),
                parity=parity[0].upper()
            )
            self.serial_connections[com_port] = ser
            print(f"✅ Connected to {com_port}.")
            return True
        except (ValueError, serial.SerialException) as e:
            print(f"❌ Error opening {com_port}: {e}")
            return False

    def serial_read_thread(self, com_port):
        try:
            with self.serial_lock:
                ser = self.serial_connections.get(com_port)

            if ser is None:
                print(f"⚠️ Serial port {com_port} not found. Exiting thread.")
                return

            accumulated_data = ""

            while True:
                with self.serial_lock:
                    ser = self.serial_connections.get(com_port)

                if ser is None or not ser.is_open:
                    print(f"⚠️ Serial port {com_port} closed. Exiting thread.")
                    break

                if ser.in_waiting > 0:
                    received_data = ser.read(ser.in_waiting).decode('ASCII', errors='ignore')
                    accumulated_data += received_data

                    if '\r' in accumulated_data:
                        messages = accumulated_data.split('\r')
                        accumulated_data = messages.pop()

                        for message in messages:
                            message = message.strip()
                            if message and self.previous_data.get(com_port) != message:
                                self.previous_data[com_port] = message
                                length = len(message)

                                card_name = self.card_names.get(com_port, "UNKNOWN")
                                # print(f"{com_port} [{card_name}]: {message} (Length: {length})")

                                async_to_sync(self.channel_layer.group_send)(self.group_name, {
                                    'type': 'serial_message',
                                    'message': message,
                                    'com_port': com_port,
                                    'length': length,
                                    'card': card_name,
                                })

                time.sleep(0.1)
        except serial.SerialException as e:
            print(f"❌ Serial exception for {com_port}: {e}")
        except Exception as e:
            print(f"❌ Error in serial read thread for {com_port}: {str(e)}")
        finally:
            with self.serial_lock:
                ser = self.serial_connections.pop(com_port, None)
                self.serial_threads.pop(com_port, None)
            if ser and ser.is_open:
                ser.close()


    def print_com_port_data(self, com_port, message, length, card_name):
        """
        Print data for a COM port with card name and message length.
        """
        if com_port not in self.printed_lines:
            # print(f"{com_port} [{card_name}]: {message} (Length: {length})")
            self.printed_lines[com_port] = True
        else:
            # print(f"{com_port} [{card_name}]: {message} (Length: {length})")
            pass

        sys.stdout.flush()

    async def serial_message(self, event):
        await self.send(text_data=json.dumps({
            'com_port': event['com_port'],
            'message': event['message'],
            'length': event['length'],
            'card': event.get('card', 'UNKNOWN_CARD')
        }))




# communicate with plc using RS48

# import asyncio
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from pymodbus.client import ModbusSerialClient



# class PLCConsumer(AsyncWebsocketConsumer):
#     read_addresses = [4105, 4106, 4107]  # Read addresses
#     write_queue = asyncio.Queue()
    
#     async def connect(self):
#         """WebSocket connection handler."""
#         await self.accept()
#         print("✅ WebSocket connection established.")

#         # Initialize PLC client
#         self.client = None
#         self.reading_task = None
#         self.writing_task = None

#     async def disconnect(self, close_code):
#         """WebSocket disconnect handler."""
#         if self.client:
#             self.client.close()
#             print("🔌 PLC Disconnected.")
#         if self.reading_task:
#             self.reading_task.cancel()
#         if self.writing_task:
#             self.writing_task.cancel()


    
#     async def receive(self, text_data):
#         """Handles incoming WebSocket messages."""
#         data = json.loads(text_data)

#         if data.get("command") == "start_PLC":
#             # Extract parameters
#             com_port = data.get("com_port")
#             baud_rate = int(data.get("baud_rate"))
#             bytesize = int(data.get("databit"))
#             stopbits = float(data.get("stopbit"))
#             parity = data.get("parity").upper()

#             if com_port:
#                 if not self.client or not self.client.connected:
#                     await self.connect_to_plc(com_port, baud_rate, bytesize, stopbits, parity)
#                 else:
#                     print("✅ Already connected to PLC.")
#                     await self.send(json.dumps({"status": "success", "message": "Already connected to PLC."}))
#             else:
#                 await self.send(json.dumps({"status": "error", "message": "Invalid PLC parameters."}))

#         elif data.get("action") == "write":
#             address = data["address"]  # No offset subtraction
#             value = data["value"]
#             await self.write_queue.put((address, value))

#         elif data.get("action") == "read":
#             address = data["address"]
#             print('your recived addresss is thisssssssssssssssssssssss:',address)

#             read_data = await self.read_from_plc(address)
#             # print('your recived data is thissssssssssssss ::',read_data)
#             if read_data is not None:
#                 await self.send(json.dumps({"status": "success", "address": address, "value": read_data}))
#                 # print(f"📡 Read Addresssssssssssssssssssssssss {address}: {read_data}")
            

#     async def connect_to_plc(self, com_port, baud_rate, bytesize, stopbits, parity):
#         """Connect to the PLC dynamically."""
#         print(f"🔄 Connecting to PLC on {com_port} at {baud_rate} baud...")

#         self.client = ModbusSerialClient(
#             port=com_port,
#             baudrate=baud_rate,
#             stopbits=stopbits,
#             bytesize=bytesize,
#             parity=parity,
#             timeout=1
#         )

#         if self.client.connect():
#             print("✅ PLC connected successfully!")
#             await self.send(json.dumps({"status": "success", "message": "PLC connected successfully."}))

#             # Start read & write tasks
#             self.reading_task = asyncio.create_task(self.read_loop())
#             self.writing_task = asyncio.create_task(self.process_write_queue())
#         else:
#             print("❌ Failed to connect to PLC.")
#             await self.send(json.dumps({"status": "error", "message": "Failed to connect to PLC."}))

#     async def process_write_queue(self):
#         """Processes the write queue and writes data to the PLC."""
#         while True:
#             address, value = await self.write_queue.get()

#             try:
#                 print(f"📝 Writing - Address: {address}, Value: {value}")
#                 result = self.client.write_register(address, value)

#                 if result.isError():
#                     print(f"⚠️ Write failed at address {address}")
#                 else:
#                     print(f"✅ Write successful at address {address}")

#             except Exception as e:
#                 print(f"❌ Error writing to PLC: {e}")

#     async def read_from_plc(self, address):
#         """Reads data from the PLC at the given address."""

#         try:
#             result = self.client.read_holding_registers(address, count=1)
            
#             if result.isError():
#                 print(f"⚠️ Read failed at address {address}")
#                 return None

#             return result.registers[0]  # Return the read value
#         except Exception as e:
#             print(f"❌ Error reading PLC address {address}: {e}")
#             return None

            

#     async def read_loop(self):
#         """Continuously reads specified addresses from the PLC."""
#         while True:
#             if not self.client.connected:
#                 print("❌ PLC not connected for reading. Retrying...")
#                 await asyncio.sleep(2)
#                 continue

#             for address in self.read_addresses:
#                 try:
#                     result = self.client.read_holding_registers(address, count=1)
#                     if result.isError():
#                         print(f"⚠️ Address {address} not ready. Skipping...")
#                         continue

#                     read_data = result.registers[0]
#                     await self.send(json.dumps({
#                         "status": "success",
#                         "address": address,
#                         "value": read_data
#                     }))
#                     # print(f"📡 Read Address {address}: {read_data}")

#                 except Exception as e:
#                     print(f"❌ Error reading from PLC at address {address}: {e}")

#                 await asyncio.sleep(1)




# from pymodbus.client import ModbusTcpClient
# import json
# import time
# import os

# PLC_IP = "192.168.3.250"
# PLC_PORT = 502
# SLAVE_ID = 1
# SCAN_START = 0
# SCAN_END = 500
# BATCH_SIZE = 10
# SCAN_DELAY = 1  # seconds

# def save_active_coils(addresses):
#     file_path = os.path.join(os.path.dirname(__file__), "active_coils.json")
#     with open(file_path, "w") as f:
#         json.dump({"active_coils": addresses}, f)

# def safe_read_coils(client, address, count):
#     try:
#         return client.read_coils(address, count=count, slave=SLAVE_ID)
#     except Exception as e:
#         print(f"❌ Error reading coils at {address}: {e}")
#         return None

# client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
# if client.connect():
#     print("✅ Connected to PLC")
#     try:
#         while True:
#             active = []
#             for addr in range(SCAN_START, SCAN_END + 1, BATCH_SIZE):
#                 count = min(BATCH_SIZE, SCAN_END - addr + 1)
#                 result = safe_read_coils(client, addr, count)
#                 if result and not result.isError():
#                     for i, val in enumerate(result.bits):
#                         if val:
#                             active.append(addr + i)
#                             print(f"✅ address {addr + i} = 1")
#             save_active_coils(active)
#             print("-" * 40)
#             time.sleep(SCAN_DELAY)
#     except KeyboardInterrupt:
#         print("⛔ Stopped by user.")
#     finally:
#         client.close()
#         print("🔌 Disconnected")
# else:
#     print("❌ PLC connection failed.")
