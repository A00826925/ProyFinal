# La clase `Model` se hace cargo de los atributos a nivel del modelo, maneja los agentes. 
# Cada modelo puede contener múltiples agentes y todos ellos son instancias de la clase `Agent`.
from mesa import Agent, Model 


from mesa.space import SingleGrid, MultiGrid
# Con `SimultaneousActivation` hacemos que todos los agentes se activen de manera simultanea.
from mesa.time import SimultaneousActivation

# Vamos a hacer uso de `DataCollector` para obtener el grid completo cada paso (o generación) y lo usaremos para graficarlo.
from mesa.datacollection import DataCollector

# mathplotlib lo usamos para graficar/visualizar como evoluciona el autómata celular.
# %matplotlib inline
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
plt.rcParams["animation.html"] = "jshtml"
matplotlib.rcParams['animation.embed_limit'] = 2**128

# Definimos los siguientes paquetes para manejar valores númericos.
import numpy as np
import pandas as pd

# Definimos otros paquetes que vamos a usar para medir el tiempo de ejecución de nuestro algoritmo.
import time
import datetime
import random

from queue import Queue

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import operator

data = []
CONT = 0

"""
#Definición del grid
"""

def get_grid(model):


    #NOTA IMPORTANTE DEL GRID. como ahora no estamos haciendo posiciones al azar, todo empezara en posiciones predeterminadas, por lo que podemos poner cada semaforo individualmente, asi como puntos pivote donde
    # SI el carro va a girar, y llega a cierto X,Y = haga el giro.

    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
        cell_content, x, y = cell
        for content in cell_content:
          if isinstance(content, Carro):
            grid[x][y] = 4
          else:
            grid[x][y] = content.live
        
    return grid

time_end = time.time() + 20

#Agente semaforo
class Semaforo(Agent):

    def __init__(self, unique_id, pos, model, isFirst, otherX, otherY):

        super().__init__(unique_id, model)

        global time_end
        global CONT
        self.otherX = otherX
        self.otherY = otherY
        
        #otherX y OtherY es la posicion del semaforo al que va a estar viendo. todos en un carril pueden ver
        #a solo uno de otro carril porque seguiran el mismo patron por carril.

        #El semaforo va a tener 3 estados en su live. Estado 1 es rojo, estado 2 es amarillo, estado 3 es verde. 
        #El estado amarillo no afecta a otros semaforos, pero si a los carros, cuando es amarillo, estos paran su movimiento.
        #Cuando el semaforo esta en rojo, va a ser detectado por los semaforos de los carriles que cruzen a los actuales y estos cambiaran a verde.
        #El semaforo estara verde por una cierta cantidad de tiempo, igual para el estado amarillo. 
        #El rojo cambiara solo cuando un semaforo observado este en verde, por lo que permanecera en rojo el tiempo que
        # el otro semaforo este en verde + amarillo.

        #nosotros declaramos que linea empieza verde primero en el modelo.


        #si es primero
        if isFirst == True:
            #verde
            self.live = 3
            #self.next_state = 3
        else:
            #si no, rojo
            self.live = 1
            #self.next_state = 1
        
    def step(self):
        global data
        x, y = self.pos
        this_cell = self.model.grid.get_cell_list_contents([(self.otherX,self.otherY)])
        for content in this_cell:

          #si el content es otro semaforo
          if isinstance(content, Semaforo):
            if (self.live == 1 and content.live == 1):
                self.live = 3

                # si es verde, hacer esto:
            elif self.live == 3:
                
                #si es verde, y el tiempo es mayor a time_end, cambia a amarillo y agrega el tiempo de espera a amarillo.
                if CONT == 4:
                  self.live = 2

                #si es amarillo, hacer esto:
            elif self.live == 2:
                #cambiamos de amarillo a rojo, como el tiempo end es global, lo cambiamos a el timer del verde.
                if CONT == 7:
                  self.live = 1

          data.append({'tag':'semaforo','x':None,'z':None,'lights':self.live,'reference':self.unique_id})

            

#agente carro
class Carro(Agent):

    def __init__(self, unique_id, pos, model, direccion, posDestino):

        super().__init__(unique_id, model)

        #si es primero
        self.live = 4
        self.xD, self.yD = posDestino
        self.canMove = True
        self.willTurn = random.randint(0, 1)
        self.revisa = True
        self.revisaNext = True
        self.HV = 0
        self.direccion = direccion
        global width
        global height

        if self.direccion == -1 or self.direccion == 1:
          #HV = 1 = horizontal, HV = 0 = vertical
          self.HV = 1
        else:
          self.HV = 0

    def step(self):
        global data
        self.x,self.y = self.pos
        self.canMove = True
        #la direccion hay que darla por ints

        #   1  =  izquierda
        #    -1  =  derecha
        #    -2  =  abajo
        #   2  =  arriba
        

        this_cell = self.model.grid.get_cell_list_contents([(self.x,self.y)])
        for content in this_cell:
          if isinstance(content,Semaforo):
                  if content.live == 1 or content.live == 2:
                    self.canMove = False
                  else:
                    self.canMove = True
                    self.revisaNext = False
        
        #MOVIMIENTO EN LAS LINEAS hori
        if self.HV == 1 and self.canMove == True:
          if self.direccion == 1:
            if self.revisa == True and self.y-2 > 0:
              this_cell = self.model.grid.get_cell_list_contents([(self.x,self.y-1)])
              for content in this_cell:
                  if isinstance(content,Carro):
                    self.canMove = False
                  else:
                    self.canMove = True
              this_cell = self.model.grid.get_cell_list_contents([(self.x,self.y-2)])
              for content in this_cell:
                  if isinstance(content,Carro):
                    self.canMove = False
                  else:
                    self.canMove = True

          elif self.direccion == -1:
            if self.revisa == True and self.y+2 < width-1:
              this_cell = self.model.grid.get_cell_list_contents([(self.x,self.y+1)])
              for content in this_cell:
                  if isinstance(content,Carro):
                    self.canMove = False
                  else:
                    self.canMove = True
              this_cell = self.model.grid.get_cell_list_contents([(self.x,self.y+2)])
              for content in this_cell:
                  if isinstance(content,Carro):
                    self.canMove = False
                  else:
                    self.canMove = True

                    
          if self.canMove == True:
            if self.y < self.yD:
              self.model.grid.move_agent(self,(self.x,self.y+1))
            elif self.y > self.yD:
              self.model.grid.move_agent(self,(self.x,self.y-1))
            elif self.x < self.xD:
              self.model.grid.move_agent(self,(self.x+1,self.y))
            elif self.x > self.xD:
              self.model.grid.move_agent(self,(self.x-1,self.y))


        #MOVIMIENTO EN LAS LINEAS verti
        elif self.HV == 0 and self.canMove == True:


          if self.direccion == 2:
            if self.revisa == True and self.x-2 > 0:
              this_cell = self.model.grid.get_cell_list_contents([(self.x-1,self.y)])
              for content in this_cell:
                  if isinstance(content,Carro):
                    self.canMove = False
                  else:
                    self.canMove = True
              this_cell = self.model.grid.get_cell_list_contents([(self.x-2,self.y)])
              for content in this_cell:
                  if isinstance(content,Carro):
                    self.canMove = False
                  else:
                    self.canMove = True

          elif self.direccion == -2:
            if self.revisa == True and self.x+2 < height-1:
              this_cell = self.model.grid.get_cell_list_contents([(self.x+1,self.y)])
              for content in this_cell:
                  if isinstance(content,Carro):
                    self.canMove = False
                  else:
                    self.canMove = True
              this_cell = self.model.grid.get_cell_list_contents([(self.x+2,self.y)])
              for content in this_cell:
                  if isinstance(content,Carro):
                    self.canMove = False
                  else:
                    self.canMove = True

                    

          if self.canMove == True:
            if self.x < self.xD:
              self.model.grid.move_agent(self,(self.x+1,self.y))
            elif self.x > self.xD:
              self.model.grid.move_agent(self,(self.x-1,self.y))
            elif self.y < self.yD:
              self.model.grid.move_agent(self,(self.x,self.y+1))
            elif self.y > self.yD:
              self.model.grid.move_agent(self,(self.x,self.y-1))
  
        data.append({'tag':'carro','x':self.pos[1],'z':self.pos[0],'lights':0,'reference':self.unique_id})

    def advance(self):
        self.revisa = self.revisaNext

"""##Modelo"""

class Interseccion(Model):
    def __init__(self, width, height):
        self.semaforos=4
        self.grid = MultiGrid(width, height, True)
        self.schedule = SimultaneousActivation(self)
        self.carros=0

        semaforo1 = Semaforo(1, (int(width/2)-2,int(height/2)-1), self, False, int(width/2),int(height/2-2))
        self.grid.place_agent(semaforo1, (int(width/2)-2,int(height/2)-1))
        self.schedule.add(semaforo1)

        semaforo2 = Semaforo(2, (int(width/2),int(height/2-2)), self, True, int(width/2)-2,int(height/2)-1)
        self.grid.place_agent(semaforo2, (int(width/2),int(height/2-2)))
        self.schedule.add(semaforo2)

        semaforo3 = Semaforo(3, (int(width/2+1),int(height/2)), self, False, int(width/2-1),int(height/2+1))
        self.grid.place_agent(semaforo3, (int(width/2+1),int(height/2)))
        self.schedule.add(semaforo3)

        semaforo4 = Semaforo(4, (int(width/2-1),int(height/2+1)), self, True, int(width/2)-2,int(height/2)-1)
        self.grid.place_agent(semaforo4, (int(width/2-1),int(height/2+1)))
        self.schedule.add(semaforo4)

        self.datacollector = DataCollector(
            model_reporters={"Grid": get_grid})
        
    def step(self):
        global contid
        global totalCarros

        prob = random.randrange(1,4)

        if prob == 1 and self.carros<totalCarros:
          self.carros += 1
          contid = contid+1
          mylist = [(int(height/2),0), (height-1,int(width/2)), (int(height/2-1),int(width-1)), (0,int(width/2)-1)]
          
          (x, y) = random.choice(mylist)
          
          if x == int(height/2):
            mylistC = [(0,int(width/2)), (int(height/2),width-1), (height-1,int(width/2)-1)]
            xd, yd = random.choice(mylistC)
            carro = Carro(contid, (x,y), self, -1, (xd,yd))
            self.grid.place_agent(carro, (x,y))
            self.schedule.add(carro)
          elif x == int(height-1):
            mylistC = [(0,int(width/2)), (int(height/2-1),0), (int(height/2),width-1)]
            xd, yd = random.choice(mylistC)
            carro = Carro(contid, (x,y), self, 2, (xd,yd))
            self.grid.place_agent(carro, (x,y))
            self.schedule.add(carro)
          elif x == int(height/2-1):
            mylistC = [(0,int(width/2)), (int(height/2-1),0), (height-1,int(width/2-1))]
            xd, yd = random.choice(mylistC)
            carro = Carro(contid, (x,y), self, 1, (xd,yd))
            self.grid.place_agent(carro, (x,y))
            self.schedule.add(carro)
          else:
            mylistC = [(int(height/2)-1,0), (height-1,int(width/2-1)), (int(height/2),width-1)]
            xd, yd = random.choice(mylistC)
            carro = Carro(contid, (x,y), self, -2, (xd,yd))
            self.grid.place_agent(carro, (x,y))
            self.schedule.add(carro)

        
        self.datacollector.collect(self)
        self.schedule.step()

#Datos Iniciales
tiempoEjecucion = 1.0
width = 20 #Ancho predeterminado
height = 20 #alto predeterminado
contid = 5
totalCarros = 10
model = Interseccion(width, height)

def updatePositions():
    global model, CONT, data
    if (CONT< 8): #Sigue en el turno del semaforo N
        data.clear()
        model.step()
        CONT+=1
    else:
        data.clear()
        model.step()
        CONT = 0
    return data

def positionsToJSON(ps):
    posDICT = []
    for p in ps:
      info = {
          "x": p['x'],
          "z": p['z'],
          "tag": p['tag'],
          "luces": p['lights'],
          "reference": p['reference']
      }
      posDICT.append(info)
    print(posDICT)
    return json.dumps(posDICT)

class Server(BaseHTTPRequestHandler):
    
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), json.dumps(post_data))
        
        dataDict = updatePositions()
        self._set_response()
        resp = "{\"data\":" + positionsToJSON(dataDict) + "}"
        self.wfile.write(resp.encode('utf-8'))


def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting httpd...\n") # HTTPD is HTTP Daemon!
    try:
        print("Hola crayola \n")
        httpd.serve_forever()
    except KeyboardInterrupt:   # CTRL+C stops the server
        pass
    httpd.server_close()
    logging.info("Stopping httpd...\n")

if __name__ == '__main__':
    from sys import argv
    
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()