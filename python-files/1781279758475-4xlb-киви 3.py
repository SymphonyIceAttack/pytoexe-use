from winreg import error

from kivy.app import App
from kivy.uix.label import Label

from kivy.config import Config
Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'width', 400)
Config.set('graphics', 'height', 700)

from kivy.graphics import Color, Rectangle
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from time import sleep
from kivy.uix.textinput import TextInput
from kivy.storage.jsonstore import JsonStore
from kivy.uix.popup import Popup


LabelBase.register(name='Riffic',
                   fn_regular='ofont.ru_Riffic.ttf'
                   )


class MyApp(App):
    def build(self):
        self.pinat = 0
        self.wage = 0
        self.saveF = 0
        self.dpw = 0
        self.hpd = 0
        self.direction = "right"
        self.ix = 0.5
        self.time = 0
        self.running = False
        self.BG = FloatLayout()
        self.a = 1200
        self.by = -0.1
        # ??????????????????????
        self.is_shortened = False
        # ??????????????????????
        self.M_P_S = 0
        self.temp = 0
        #self.my_ear
        self.earned = 0
        self.settingF = 0

        self.store = JsonStore('data.json')


        with  self.BG.canvas.before:
            Color(.25, .5, .5, 1)
            self.rect = Rectangle(pos=self.BG.pos, size=self.BG.size)

        # Привязываем фон к BG
        self.BG.bind(pos=lambda obj, pos: setattr(self.rect, 'pos', pos))
        self.BG.bind(size=lambda obj, size: setattr(self.rect, 'size', size))



        self.my_title = Label(text="How much\ndo I earn\nwhile I'm shitting?",
                      font_size=40,
                      color=(1,1,.7,1),
                      font_name = 'Riffic',
                      halign = 'center',
                      valign = 'top',
                      text_size = (400, self.a)
                      )

        Clock.schedule_interval(self.update_text_size, 0.001)


        self.start = Button(text='Start',
                       font_size=60,
                       color=(0,0,0,1),
                       size_hint = (0.6,0.125),
                       pos_hint = {"center_x": 0.5, "center_y": self.by},
                       background_color = (1,1,0.7,0.7),
                       background_normal='',
                       on_press = self.starts
                       )

        self.saveb = Button(text='Save',
                           font_size=60,
                           color=(0, 0, 0, 1),
                           size_hint=(0.6, 0.125),
                           pos_hint={"center_x": 0.5, "center_y": self.by},
                           background_color=(1, 1, 0.7, 0.7),
                           background_normal='',
                           on_press=self.save
                           )

        self.overb = Button(text='Over',
                       font_size=60,
                       color=(0,0,0,1),
                       size_hint = (0.6,0.125),
                       pos_hint = {"center_x": 0.5, "center_y": self.by},
                       background_color = (1,1,0.7,0.7),
                       background_normal='',
                       on_press = self.over)

        Clock.schedule_interval(self.update_button, 0.001)

        self.watch = Label(text='00:00',
                     font_size=50,
                     color=(0, 0, 0, 1),
                     size_hint=(0.2, 0.1),
                     pos_hint={"center_x": 0.5, "center_y": 0.25}
                     )

        self.result = Label(text='',
                            font_size=75,
                            font_name='Riffic',
                            color=(1,1,.7,1),
                            size_hint=(0.2, 0.1),
                            pos_hint={"center_x": 0.5, "center_y": 0.5}
                            )


        self.toilet = Image(source='man-urinates-toilet-icon-vector-illustration_869472-914 (1).PNG',
            size_hint=(0.7, 0.7),
            pos_hint={"center_x": self.ix, "center_y": 0.5125}
        )

        self.settingsb = Button(text='',
                               font_size=40,
                               size_hint=(0.15, 0.15),
                               color=(0, 0, 0, 1),
                               pos_hint={"center_x": 0.09, "center_y": 0.06},
                               background_color = (1, 1, 1, 0.7),
                               background_normal = 'Windows_Settings_icon.svg (1).png',
                               background_down='free-icon-settings-126472.png',
                               on_press = self.settings

                               )

#===============================================================
        self.wageO = TextInput(hint_text = 'enter your salary...',
                               input_type='number',
                               input_filter='int',
                               size_hint=(0.5, 0.1),
                               pos_hint={"center_x": 0.5, "center_y": 0.7}
                               )

        self.wages = Label(text='your\nsalary',
                           font_size=40,
                           font_name='Riffic',
                           color=(1, 1, .7, 1),
                           size_hint=(0.2, 0.1),
                           pos_hint={"center_x": 0.27, "center_y": 0.72}
                           )

        self.dpwO = TextInput(hint_text = 'enter the number of working days per week...',
                               input_type='number',
                               input_filter='int',
                               size_hint=(0.5, 0.1),
                               pos_hint={"center_x": 0.5, "center_y": 0.55}
                               )

        self.dpws = Label(text='working days \nper week',
                           font_size=25,
                           font_name='Riffic',
                           color=(1, 1, .7, 1),
                           size_hint=(0.2, 0.1),
                           pos_hint={"center_x": 0.27, "center_y": 0.52}
                           )

        self.hpdO = TextInput(hint_text = 'enter the number of working hours per day...',
                               input_type='number',
                               input_filter='int',
                               size_hint=(0.5, 0.1),
                               pos_hint={"center_x": 0.5, "center_y": 0.4}
                               )

        self.hpds = Label(text='working hours\nper day',
                           font_size=25,
                           font_name='Riffic',
                           color=(1, 1, .7, 1),
                           size_hint=(0.2, 0.1),
                           pos_hint={"center_x": 0.27, "center_y": 0.32}
                           )


        self.error = Popup(title='Error',
                           content=Label(text="enter the data correctly"),
                           size_hint=(0.7, 0.3),
                           auto_dismiss=True,
                           )
# ===============================================================

        self.BG.add_widget(self.settingsb)
        self.BG.add_widget(self.toilet)
        self.BG.add_widget(self.start)
        self.BG.add_widget(self.my_title)


        return self.BG

#======================================================================

    def starts(self,instance):
        print('старт начал свою работу')
        self.BG.remove_widget(self.settingsb)
        if self.toilet.parent is None:
            self.BG.add_widget(self.toilet)
            self.BG.remove_widget(self.result)

        if self.watch.parent:
            self.BG.remove_widget(self.watch)

        if self.store.exists('user_data'):
            data = self.store.get('user_data')

            self.wage = data['wage']
            self.dpw = data['dpw']
            self.hpd = data['hpd']

            print('wage из даннх =',self.wage)


        if self.dpw == 0 and self.hpd == 0 and self.wage == 0:

            self.ix = self.toilet.pos_hint["center_x"]
            Clock.schedule_interval(self.move_toilet, 0.01)

            self.BG.remove_widget(self.start)
            self.saveF = 1
            self.BG.add_widget(self.saveb)
            self.my_title.text = 'enter your details'

            Clock.schedule_interval(self.move_toilet, 0.01)


            if hasattr(self, 'result') and self.result.parent:
                self.BG.remove_widget(self.result)

        print('is_shortened=', self.is_shortened, 'self.ix=',self.ix)


        print(self.dpw, self.hpd, self.wage)
        if self.dpw > 0 and self.hpd > 0 and self.wage > 0:
            self.ix = 1.0000009

        if  not self.is_shortened and self.ix > 1:

            self.toilet.source = 'man-urinates-toilet-icon-vector-illustration_869472-914.png'

            self.start.text = 'Stop'
            self.my_title.text = 'How much\ndo I earn\nwhile I`m shitting?'
            self.is_shortened = True
            self.time = 0
            self.BG.add_widget(self.watch)


            #==========
            if not self.running:
                self.running = True
                Clock.schedule_interval(self.timestart, 0.1)


        elif self.dpw != 0 and self.hpd != 0 and self.wage != 0:

            self.M_P_S = (self.wage / self.dpw / self.hpd / 60 / 60)

            self.my_title.text = '!Congratulations! \n You have earned: '
            self.BG.remove_widget(self.start)
            self.BG.add_widget(self.overb)

            self.BG.add_widget(self.result)

            print('M_P_S=',self.M_P_S, 'self.time=',self.ix )
            self.earned = self.M_P_S * self.time
            self.result.text = f"{self.earned:.2f}"

            self.BG.remove_widget(self.toilet)
            self.is_shortened = False
            self.BG.remove_widget(self.watch)


            print('старт закончил свою работу')


    def save(self,instance):
        print('сейв начал свою работу')

        if not self.wageO.text.strip():
            self.error.open()
            return

        if not self.hpdO.text.strip():
            self.error.open()
            return

        if not self.dpwO.text.strip():
            self.error.open()
            return

        self.wage = float(self.wageO.text)
        self.dpw = float(self.dpwO.text)
        self.hpd = float(self.hpdO.text)

        if self.wage <= 0:
            self.error.open()
            self.wage = ''

            return

        if self.dpw < 1 or self.dpw > 7:
            self.error.open()
            self.dpw = ''
            return

        if self.hpd < 1 or self.hpd > 24:
            self.error.open()
            self.hpd = ''
            return

        self.store.put('user_data',
                       wage=self.wage,
                       dpw=self.dpw,
                       hpd=self.hpd,
                       M_P_S=self.M_P_S,
                       )

        if self.store.exists('user_data'):
            data = self.store.get('user_data')

            self.wage = data['wage']
            self.dpw = data['dpw']
            self.hpd = data['hpd']


        self.M_P_S = (self.wage / self.dpw / self.hpd / 60 / 60)

        if self.saveF == 1:

            self.BG.remove_widget(self.wageO)

            self.BG.remove_widget(self.dpwO)

            self.BG.remove_widget(self.hpdO)

            self.BG.add_widget(self.start)
            self.BG.remove_widget(self.saveb)
            self.my_title.text = 'How much\ndo I earn\nwhile I`m shitting?'



        if self.settingsb.parent is None:
            self.BG.add_widget(self.settingsb)
        self.toilet.pos_hint = {"center_x": 0.5, "center_y": 0.5125}

        print('сейв закончил свою работу')


    def  over(self,instance):
        self.BG.remove_widget(self.result)
        self.toilet.source='man-urinates-toilet-icon-vector-illustration_869472-914 (1).PNG'
        self.BG.add_widget(self.toilet)
        self.my_title.text = "How much\ndo I earn\nwhile I'm shitting?"
        self.BG.remove_widget(self.overb)
        self.BG.add_widget(self.start)
        self.start.text = 'Start'
        self.BG.add_widget(self.settingsb)


    def settings(self, instance):
        if self.settingF == 0:

            self.BG.remove_widget(self.result)
            self.BG.remove_widget(self.start)
            self.BG.remove_widget(self.toilet)

            self.my_title.text = 'settings'
            self.my_title.font_size = '75'

            self.BG.add_widget(self.wages)
            self.BG.add_widget(self.hpds)
            self.BG.add_widget(self.dpws)
            self.saveF = 0
            self.BG.add_widget(self.saveb)

            if self.store.exists('user_data'):
                data = self.store.get('user_data')

                self.wage = data['wage']
                self.dpw = data['dpw']
                self.hpd = data['hpd']

            else:
                # Данных нет, используем значения по умолчанию
                print("Нет сохранённых данных")
                self.wage = 0
                self.dpw = 0
                self.hpd = 0

            self.wageO.text = str(self.wage)
            self.wageO.pos_hint = {"center_x": 0.7, "center_y": 0.7125}
            self.BG.add_widget(self.wageO)

            self.dpwO.text = str(self.dpw)
            self.dpwO.pos_hint = {"center_x": 0.7, "center_y": 0.5125}
            self.BG.add_widget(self.dpwO)

            self.hpdO.text = str(self.hpd)
            self.hpdO.pos_hint = {"center_x": 0.7, "center_y": 0.3125}
            self.BG.add_widget(self.hpdO)
            self.settingF = 1

            # if self.ix == 0.5:
            #      self.ix = 2


        elif self.settingF == 1:
            self.my_title.text = 'How much\ndo I earn\nwhile I`m shitting?'
            self.my_title.font_size = '40'
            self.BG.remove_widget(self.wages)
            self.BG.remove_widget(self.hpds)
            self.BG.remove_widget(self.dpws)

            self.BG.remove_widget(self.wageO)
            self.BG.remove_widget(self.dpwO)
            self.BG.remove_widget(self.hpdO)
            self.BG.remove_widget(self.saveb)

            self.BG.add_widget(self.start)
            self.BG.add_widget(self.toilet)

            self.wageO.pos_hint = {"center_x": 0.5, "center_y": 0.7125}
            self.dpwO.pos_hint = {"center_x": 0.5, "center_y": 0.5125}
            self.hpdO.pos_hint = {"center_x": 0.5, "center_y": 0.3125}

            self.settingF = 0

            # if self.ix == 0.5:
            #     self.ix = 2


    def update_text_size(self, dt):
        if self.a > 800:
            self.a -= 20
            self.my_title.text_size = (400, self.a)


    def update_button(self, dt):
        if self.a <= 800:

            if self.by < 0.125:
                self.by += 0.01
                self.start.pos_hint = {"center_x": 0.5, "center_y": self.by}
                self.overb.pos_hint = {"center_x": 0.5, "center_y": self.by}
                self.saveb.pos_hint = {"center_x": 0.5, "center_y": self.by}

    def timestart(self, dt):
        self.time += dt

        minutes = int(self.time // 60)
        seconds = int(self.time % 60 )

        self.watch.text = f'{minutes:02d}:{seconds:02d}'

    def move_toilet(self, dt):
        if self.ix <= 1.4 and self.direction == "right":
            self.ix += 0.01
            self.toilet.pos_hint = {"center_x": self.ix, "center_y": 0.5125}

            if self.ix > 1.4:
                self.direction = "left"

                self.BG.add_widget(self.wageO)
                self.BG.add_widget(self.dpwO)
                self.BG.add_widget(self.hpdO)

            if self.ix > 1.4 and self.direction == "left":
                 self.ix -= 0.4
        else:
            Clock.unschedule(self.move_toilet)



if __name__ == '__main__':
    MyApp().run()