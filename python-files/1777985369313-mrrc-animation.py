from manim import *

class AAAAA(Scene):
    def construct(self):
        title = Text('Mum,I love you',font_size=50)
        tittle = Text('妈妈，我爱你',font_size=50)
        aaa = Text('这是一个道歉视频。',font_size=50)
        aab = Text('请您以后不要再生气了。',font_size=50)
        aba = Text('谢谢！',font_size=50)
        abb = Text('再见！',font_size=50)
        s = Square(color = RED,fill_opacity = 1)
        c1 = Circle(color = RED,fill_opacity = 1)
        c2 = Circle(color = RED,fill_opacity = 1)
        s1 = Square(color = RED,fill_opacity = 0)
        group1 = VGroup(s,c1,c2)

        self.play(Write(title))
        self.wait(1)

        self.play(title.animate.to_edge(UP))
        tittle.move_to(title) 
        self.play(Transform(title,tittle))
        self.play(title.animate.to_edge(UL))
        self.wait(0.6)

        aaa.move_to(title,aligned_edge=LEFT)
        self.play(Transform(title,aaa))
        self.wait(1)

        self.play(title.animate.move_to(aab))
        self.play(Transform(title,aab))
        self.wait(1)

        self.play(Transform(title,aba))
        self.wait(0.5)

        self.play(Transform(title,abb))
        self.wait(0.3)

        self.play(FadeOut(title))

        
        c1.move_to(s.get_top())
        c2.move_to(s.get_right())
        group1.rotate(45*DEGREES)
        group1.move_to(s1.get_center())
        self.play(Write(group1))
        n=1
        while n <=6:
            self.play(group1.animate.scale(1.25),run_time = 1)
            self.play(group1.animate.scale(0.8),run_time = 1)
            n = n+1
        self.play(FadeOut(group1))
       
config.preview = True
scene = AAAAA()
scene.render()
         