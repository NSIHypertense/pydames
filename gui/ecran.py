import colorsys
import math

import glfw
from OpenGL import GL
import imgui
from imgui.integrations.glfw import GlfwRenderer

from .scene import SceneTitre, creer_programme_shader

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

_imgui_couleurs = [
    # imgui.COLOR_TEXT,
    imgui.COLOR_TEXT_DISABLED,
    imgui.COLOR_WINDOW_BACKGROUND,
    imgui.COLOR_CHILD_BACKGROUND,
    imgui.COLOR_POPUP_BACKGROUND,
    imgui.COLOR_BORDER,
    imgui.COLOR_BORDER_SHADOW,
    imgui.COLOR_FRAME_BACKGROUND,
    imgui.COLOR_FRAME_BACKGROUND_HOVERED,
    imgui.COLOR_FRAME_BACKGROUND_ACTIVE,
    imgui.COLOR_TITLE_BACKGROUND,
    imgui.COLOR_TITLE_BACKGROUND_ACTIVE,
    imgui.COLOR_TITLE_BACKGROUND_COLLAPSED,
    imgui.COLOR_MENUBAR_BACKGROUND,
    imgui.COLOR_SCROLLBAR_BACKGROUND,
    imgui.COLOR_SCROLLBAR_GRAB,
    imgui.COLOR_SCROLLBAR_GRAB_HOVERED,
    imgui.COLOR_SCROLLBAR_GRAB_ACTIVE,
    imgui.COLOR_CHECK_MARK,
    imgui.COLOR_SLIDER_GRAB,
    imgui.COLOR_SLIDER_GRAB_ACTIVE,
    imgui.COLOR_BUTTON,
    imgui.COLOR_BUTTON_HOVERED,
    imgui.COLOR_BUTTON_ACTIVE,
    imgui.COLOR_HEADER,
    imgui.COLOR_HEADER_HOVERED,
    imgui.COLOR_HEADER_ACTIVE,
    imgui.COLOR_SEPARATOR,
    imgui.COLOR_SEPARATOR_HOVERED,
    imgui.COLOR_SEPARATOR_ACTIVE,
    imgui.COLOR_RESIZE_GRIP,
    imgui.COLOR_RESIZE_GRIP_HOVERED,
    imgui.COLOR_RESIZE_GRIP_ACTIVE,
    imgui.COLOR_TAB,
    imgui.COLOR_TAB_HOVERED,
    imgui.COLOR_TAB_ACTIVE,
    imgui.COLOR_TAB_UNFOCUSED,
    imgui.COLOR_TAB_UNFOCUSED_ACTIVE,
    imgui.COLOR_PLOT_LINES,
    imgui.COLOR_PLOT_LINES_HOVERED,
    imgui.COLOR_PLOT_HISTOGRAM,
    imgui.COLOR_PLOT_HISTOGRAM_HOVERED,
    imgui.COLOR_TABLE_HEADER_BACKGROUND,
    imgui.COLOR_TABLE_BORDER_STRONG,
    imgui.COLOR_TABLE_BORDER_LIGHT,
    imgui.COLOR_TABLE_ROW_BACKGROUND,
    imgui.COLOR_TABLE_ROW_BACKGROUND_ALT,
    imgui.COLOR_TEXT_SELECTED_BACKGROUND,
    imgui.COLOR_DRAG_DROP_TARGET,
    imgui.COLOR_NAV_HIGHLIGHT,
    imgui.COLOR_NAV_WINDOWING_HIGHLIGHT,
    imgui.COLOR_NAV_WINDOWING_DIM_BACKGROUND,
    imgui.COLOR_MODAL_WINDOW_DIM_BACKGROUND,
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

        self._programme = creer_programme_shader(
            "shader/quad_vert.glsl", "shader/titre_frag.glsl"
        )
        self._uniform_t = GL.glGetUniformLocation(self._programme, "t")
        self._uniform_fenetre_taille = GL.glGetUniformLocation(
            self._programme, "fenetre_taille"
        )

        imgui.create_context()
        imgui.get_io().ini_file_name = "".encode()

        style = imgui.get_style()
        for i in _imgui_couleurs:
            c = style.colors[i]
            hsv = colorsys.rgb_to_hsv(*c[:3])
            hsv = ((hsv[0] + 0.06) % 1.0, hsv[1] * 1.4, hsv[2] * max(hsv[2], 0.25))
            rgb = colorsys.hsv_to_rgb(*hsv)
            rgb = (*rgb[:2], min(rgb[2] + 0.02, 1.0))
            style.colors[i] = (*rgb, c[3])

        self.__style = copier_style(style)

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
        t = glfw.get_time()

        longueur, largeur = glfw.get_window_size(self.fenetre)
        echelle = max(min(longueur // 400, largeur // 400) / 2, 1)

        if self.__echelle != echelle:
            self.__echelle = echelle
            io.font_global_scale = echelle
            io.display_fb_scale = (echelle, echelle)
            _imgui_scale_all_sizes(self.__style, imgui.get_style(), echelle, echelle)

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        GL.glViewport(0, 0, longueur, largeur)
        GL.glUseProgram(self._programme)
        GL.glUniform1f(self._uniform_t, t)
        GL.glUniform2f(self._uniform_fenetre_taille, longueur, largeur)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
        GL.glUseProgram(0)

        imgui.new_frame()
        self.scene.longueur, self.scene.largeur = longueur, largeur
        x, y = glfw.get_cursor_pos(self.fenetre)
        self.scene.curseur = (int(x), int(y))
        self.scene.clic = (
            glfw.get_mouse_button(self.fenetre, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
        )
        self.scene.rendre(t)

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
