import glfw
from OpenGL import GL
import imgui
from imgui.integrations.glfw import GlfwRenderer

from . scene import SceneDamier

# def blend_argb(a, b):
#     return (
#         int((a[0] * a[3] / 255) + (b[0] * b[3] * (255 - a[3]) / 255) / (255 * 255)),
#         int((a[1] * a[3] / 255) + (b[1] * b[3] * (255 - a[3]) / 255) / (255 * 255)),
#         int((a[2] * a[3] / 255) + (b[2] * b[3] * (255 - a[3]) / 255) / (255 * 255)),
#         int((a[3] + (b[3] * (255 - a[3]) / 255)))
#     )

def init():
    if not glfw.init():
        raise Exception("Impossible d'initialiser GLFW")

def fini():
    glfw.terminate()

class Ecran:
    def __init__(self, longueur: int, largeur: int):
        self.longueur, self.largeur = longueur, largeur
        self.marche, self.i, self.fps, self.derniere_seconde = True, 0, 0, 0

        self.fenetre = glfw.create_window(longueur, largeur, "pydames", None, None)
        if not self.fenetre:
            glfw.terminate()
            raise Exception("Impossible de créer la fenêtre GLFW")

        glfw.make_context_current(self.fenetre)

        imgui.create_context()
        self.imgui_renderer = GlfwRenderer(self.fenetre)

        self.scene = SceneDamier()
    
    def poll(self) -> bool:
        glfw.poll_events()
        self.imgui_renderer.process_inputs()
        if glfw.window_should_close(self.fenetre):
            self.marche = False
        return self.marche

    def rendre(self):
        time = glfw.get_time()
        if time > self.derniere_seconde + 0.25:
            self.fps = self.i / (time - self.derniere_seconde)
            self.derniere_seconde = time
            self.i = 0

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        self.scene.rendre(glfw.get_time())
        imgui.new_frame()
        imgui.begin("Debug")
        imgui.text(f"fps: {self.fps:.1f}")
        imgui.end()
        imgui.render()
        self.imgui_renderer.render(imgui.get_draw_data())

        glfw.swap_buffers(self.fenetre)

        self.i += 1

    def __del__(self):
        self.imgui_renderer.shutdown()

