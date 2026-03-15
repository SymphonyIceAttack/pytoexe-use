from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton
from panda3d.core import *
from direct.task import Task

class Game(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        self.disableMouse()
        self.camera.setPos(0,-40,15)
        self.camera.lookAt(0,0,0)

        # BLACK SCREEN
        self.title = OnscreenText(
            text="Made by Gurman",
            pos=(0,0),
            scale=0.1,
            fg=(1,1,1,1)
        )

        # start animation timer
        self.taskMgr.doMethodLater(3, self.show_menu, "menu")

    def show_menu(self, task):

        self.title.destroy()

        self.play = DirectButton(
            text="PLAY",
            scale=0.1,
            command=self.start_loading
        )

    def start_loading(self):

        self.play.destroy()

        self.loading = OnscreenText(
            text="Loading...",
            pos=(0,0),
            scale=0.1
        )

        self.taskMgr.doMethodLater(2, self.load_world, "load")

    def load_world(self, task):

        self.loading.destroy()

        # ground
        self.ground = loader.loadModel("models/environment")
        self.ground.reparentTo(render)
        self.ground.setScale(0.1)
        self.ground.setPos(-8,42,0)

        # car (placeholder)
        self.car = loader.loadModel("models/box")
        self.car.reparentTo(render)
        self.car.setScale(1,2,0.5)

        self.speed = 0

        # controls
        self.accept("w", self.forward)
        self.accept("s", self.backward)
        self.accept("a", self.left)
        self.accept("d", self.right)
        self.accept("space", self.brake)

        self.taskMgr.add(self.update, "update")

    def forward(self):
        self.speed = 0.5

    def backward(self):
        self.speed = -0.5

    def left(self):
        self.car.setH(self.car.getH()+5)

    def right(self):
        self.car.setH(self.car.getH()-5)

    def brake(self):
        self.speed = 0

    def update(self, task):

        self.car.setY(self.car, self.speed)

        # camera follow car
        self.camera.setPos(
            self.car.getX(),
            self.car.getY()-20,
            self.car.getZ()+10
        )
        self.camera.lookAt(self.car)

        return Task.cont


game = Game()
game.run()
