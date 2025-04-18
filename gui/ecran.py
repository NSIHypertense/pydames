import glfw
import math
from OpenGL import GL
import imgui
from imgui.integrations.glfw import GlfwRenderer

from .scene import SceneTitre

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


_imgui_attributs = [
    "window_padding",
    "window_rounding",
    "window_min_size",
    "child_rounding",
    "popup_rounding",
    "frame_padding",
    "frame_rounding",
    "item_spacing",
    "item_inner_spacing",
    "cell_padding",
    "touch_extra_padding",
    "indent_spacing",
    "columns_min_spacing",
    "scrollbar_size",
    "scrollbar_rounding",
    "grab_min_size",
    "grab_rounding",
    "log_slider_deadzone",
    "tab_rounding",
    "tab_min_width_for_close_button",
    "display_window_padding",
    "display_safe_area_padding",
    "mouse_cursor_scale",
]


# source : https://github.com/ocornut/imgui/issues/6967#issuecomment-1793465530
def _imgui_scale_all_sizes(_style, style, hscale: float, vscale: float) -> None:
    """pyimgui is missing ImGuiStyle::ScaleAllSizes(); this is a reimplementation of it."""

    scale = max(hscale, vscale)

    def scale_it(attrname: str) -> None:
        value = getattr(_style, attrname)
        if isinstance(value, imgui.Vec2):
            value = imgui.Vec2(
                math.trunc(value.x * hscale), math.trunc(value.y * vscale)
            )
            setattr(style, attrname, value)
        else:
            setattr(style, attrname, math.trunc(value * scale))

    for attr in _imgui_attributs:
        scale_it(attr)

    # scale_it("separator_text_padding")  # not present in current pyimgui


def copier_style(style) -> imgui.GuiStyle:
    nouveau = imgui.GuiStyle.create()

    for attr in _imgui_attributs:
        setattr(nouveau, attr, getattr(style, attr))

    return nouveau


class Ecran:
    def __init__(self, longueur: int, largeur: int):
        self.longueur, self.largeur, self.__echelle = longueur, largeur, 0
        self.marche, self.i, self.fps, self.derniere_seconde = True, 0, 0, 0

        self.fenetre = glfw.create_window(longueur, largeur, "pydames", None, None)
        if not self.fenetre:
            glfw.terminate()
            raise Exception("Impossible de créer la fenêtre GLFW")

        glfw.make_context_current(self.fenetre)

        imgui.create_context()
        imgui.get_io().ini_file_name = "".encode()
        self.__style = copier_style(imgui.get_style())

        self.imgui_renderer = GlfwRenderer(self.fenetre)

        self.scene = SceneTitre()

    def poll(self) -> bool:
        glfw.poll_events()
        self.imgui_renderer.process_inputs()

        if glfw.window_should_close(self.fenetre) or (
            isinstance(self.scene, SceneTitre) and self.scene.quitter
        ):
            self.marche = False

        return self.marche

    def rendre(self):
        io = imgui.get_io()
        longueur, largeur = glfw.get_window_size(self.fenetre)
        echelle = max(min(longueur // 400, largeur // 400) / 2, 1)

        if self.__echelle != echelle:
            self.__echelle = echelle
            io.font_global_scale = echelle
            io.display_fb_scale = (echelle, echelle)
            _imgui_scale_all_sizes(self.__style, imgui.get_style(), echelle, echelle)

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        imgui.new_frame()
        self.scene.longueur, self.scene.largeur = longueur, largeur
        x, y = glfw.get_cursor_pos(self.fenetre)
        self.scene.curseur = (int(x), int(y))
        self.scene.clic = (
            glfw.get_mouse_button(self.fenetre, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
        )
        self.scene.rendre(glfw.get_time())

        imgui.set_next_window_position(0, 0)
        imgui.begin(
            "Debug", flags=imgui.WINDOW_NO_MOVE | imgui.WINDOW_ALWAYS_AUTO_RESIZE
        )
        imgui.text(f"fps: {self.fps:.1f}")
        imgui.end()
        imgui.render()

        self.imgui_renderer.render(imgui.get_draw_data())

        glfw.swap_buffers(self.fenetre)

        self.i += 1

        time = glfw.get_time()
        if time > self.derniere_seconde + 0.25:
            self.fps = self.i / (time - self.derniere_seconde)
            self.derniere_seconde = time
            self.i = 0

        if self.scene.prochaine_scene:
            self.scene.fini()
            self.scene = self.scene.prochaine_scene

    def fini(self):
        self.imgui_renderer.shutdown()
