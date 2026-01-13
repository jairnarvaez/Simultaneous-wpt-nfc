import serial
import serial.tools.list_ports
import time
import argparse

class GeneradorDeTramas:
    def __init__(self, comandos):
        self.comandos = comandos

    @staticmethod
    def calcular_checksum(datos):
        suma = sum(datos)
        checksum = (0xFF - (suma % 0x100)) + 1
        return checksum

    def generar_trama(self, comando):
        if comando == self.comandos.get("Reset"):
            return comando  

        encabezado = [0x00, 0x00, 0xFF]
        cantidad_bytes_comando = len(comando)
        checksum_cantidad_bytes = (0xFF - (cantidad_bytes_comando % 0x100)) + 1
        checksum_comando = self.calcular_checksum(comando)
        trama = (encabezado +
                 [cantidad_bytes_comando] +
                 [checksum_cantidad_bytes] +
                 comando +
                 [checksum_comando] +
                 [0x00])
        return trama

    def listar_tramas(self):
        tramas_generadas = {}
        for nombre, comando in self.comandos.items():
            trama_completa = self.generar_trama(comando)
            trama_hex = ' '.join(format(byte, '02X') for byte in trama_completa)
            tramas_generadas[nombre] = trama_hex
        return tramas_generadas

class ComunicacionSerialPN532:
    def __init__(self, tramas, dispositivo, debug):
        self.tramas = tramas
        self.dispositivo = dispositivo
        self.puerto = None
        self.ser = None
        self.debug = debug  

    def _print_debug(self, mensaje):
        if self.debug:
            print(mensaje)

    def listar_puertos(self):
        puertos_disponibles = serial.tools.list_ports.comports()
        for i, puerto in enumerate(puertos_disponibles):
            print(f"{i + 1}: {puerto.device} ({puerto.description})")
        return puertos_disponibles

    def seleccionar_puerto(self, puertos):
        while True:
            try:
                opcion = int(input("Selecciona el número del puerto COM: "))
                if 1 <= opcion <= len(puertos):
                    return puertos[opcion - 1].device
                else:
                    self._print_debug("Opción inválida, intenta de nuevo.")
            except ValueError:
                self._print_debug("Por favor, ingresa un número válido.")

    def iniciar_comunicacion(self):
        puertos = self.listar_puertos()
        if not puertos:
            self._print_debug("No se encontraron puertos COM disponibles.")
            return   
        puerto = self.seleccionar_puerto(puertos)
        self._print_debug(f"Has seleccionado el puerto: {puerto}")
        self.ser = serial.Serial(puerto, 115200, timeout=1)

        if self.dispositivo == "receptor":
            self._print_debug("Iniciando comunicación como receptor...")
            self.enviar_trama('Reset')
            self.recibir_datos('Reset')

            self.enviar_trama('InJumpForDEP')
            self.recibir_datos('InJumpForDEP')

        if self.dispositivo == "transmisor":
            self._print_debug("Iniciando comunicación como transmisor...")
            self.enviar_trama('Reset')
            self.recibir_datos('Reset')

            self.enviar_trama('TgInitAsTarget')
            self.recibir_datos('TgInitAsTarget')

            self.enviar_trama('TgGetData')
            self.recibir_datos('TgGetData')

    def enviar_mensaje(self, mensaje):
            mensaje_bytes = mensaje.encode()
            mensaje_hex = [byte for byte in mensaje_bytes]
            comandos["TgSetData"] = [0xD4, 0x8E] + mensaje_hex
            generador = GeneradorDeTramas(comandos)
            tramas = generador.listar_tramas()
            self.tramas = tramas
            self.enviar_trama('TgSetData')
            self.recibir_datos('TgSetData')

    def recibir_mensaje(self):
            self.enviar_trama('InDataExchange')
            self.recibir_datos('InDataExchange')
    
    def enviar_trama(self, nombre_comando):
        trama = self.tramas.get(nombre_comando)
        if trama:
            self._print_debug(f"Enviando trama: {nombre_comando} -> {trama}")
            self.ser.write(bytearray.fromhex(trama))
        else:
            self._print_debug(f"Comando {nombre_comando} no encontrado.")

    def recibir_datos(self, nombre_comando):            
        while True:
            respuesta = self.ser.read(64)
            if respuesta: 
               respuesta_hex = ' '.join(format(byte, '02X') for byte in respuesta)
               self._print_debug(f"Respuesta recibida: {respuesta_hex}")

               if nombre_comando == "Reset" and respuesta_hex == "00 00 FF 00 FF 00 00 00 FF 02 FE D5 15 16 00":
                  self._print_debug("\nPN532 reseteado")
                  break

               if nombre_comando == "InJumpForDEP" and respuesta_hex == "00 00 FF 00 FF 00":
                  self._print_debug("ACK recibido")

               if nombre_comando == "InJumpForDEP" and respuesta_hex == "00 00 FF 13 ED D5 57 00 01 AA 99 88 77 66 55 44 33 22 11 00 00 00 09 01 22 00":
                  self._print_debug("InJumpForDEP ejectutado correctamente\n")
                  break                  

               if nombre_comando == "InDataExchange" and respuesta_hex == "00 00 FF 00 FF 00":
                  self._print_debug("ACK recibido")
                                    
               if nombre_comando == "InDataExchange" and respuesta_hex != "00 00 FF 00 FF 00":
                  self._print_debug("Mensaje Recibido")
                  datos_intermedios = respuesta[8:-2]
                  cadena = datos_intermedios.decode('utf-8', errors='ignore')  # Ignorar errores de decodificación
                  print("\nMensaje recibido: ")
                  print(f"{cadena}")
                  self._print_debug("InDataExchange ejectutado correctamente\n")
                  break

               if nombre_comando == "TgInitAsTarget" and respuesta_hex == "00 00 FF 00 FF 00":
                  self._print_debug("ACK Recibido")

               if nombre_comando == "TgInitAsTarget" and respuesta_hex != "00 00 FF 00 FF 00":
                  self._print_debug("TgInitAsTarget ejectutado correctamente\n")
                  break

               if nombre_comando == "TgGetData" and respuesta_hex == "00 00 FF 00 FF 00":
                  self._print_debug("ACK Recibido")

               if nombre_comando == "TgSetData" and respuesta_hex != "00 00 FF 00 FF 00":
                  self._print_debug("ACK Recibido")
                  break
                  
               if nombre_comando == "TgGetData" and respuesta_hex != "00 00 FF 00 FF 00":
                  self._print_debug("TgGetData ejectutado correctamente\n")
                  break
                  
            else:
                time.sleep(0.2)


mensaje = ""
mensaje_bytes = mensaje.encode()
mensaje_hex = [byte for byte in mensaje_bytes]

comandos = {
    "Reset": [0x55, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x03, 0xFD, 0xD4,
              0x14, 0x01, 0x17, 0x00],
    "InJumpForDEP": [0xD4, 0x56, 0x01, 0x00, 0x00],
    "TgInitAsTarget": [
        0xD4, 0x8C, 0x00, 0x08, 0x00, 0x12, 0x34, 0x56, 0x40, 0x01, 0xFE,
        0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xC0, 0xC1, 0xC2, 0xC3, 0xC4,
        0xC5, 0xC6, 0xC7, 0xFF, 0xFF, 0xAA, 0x99, 0x88, 0x77, 0x66, 0x55,
        0x44, 0x33, 0x22, 0x11, 0x00, 0x00
    ],
    "TgGetData": [0xD4, 0x86],
    "InDataExchange": [0xD4, 0x40, 0x01, 0x10],
    "TgSetData": [0xD4, 0x8E] + mensaje_hex
}


parser = argparse.ArgumentParser(description="Captura argumentos desde la consola.")
parser.add_argument("variable", type=str, help="Variable obtenida desde la consola")  
args = parser.parse_args()
print(f"La variable obtenida desde la consola es: {args.variable}")


generador = GeneradorDeTramas(comandos)
tramas = generador.listar_tramas()
nfc = ComunicacionSerialPN532(tramas, dispositivo=f"{args.variable}", debug=False)
nfc.iniciar_comunicacion()

if args.variable == "transmisor":
    while True:
        mensaje = input("Mensaje: ")
        nfc.enviar_mensaje(mensaje)

if args.variable == "receptor":
    while True:
        nfc.recibir_mensaje()
