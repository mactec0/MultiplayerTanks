from sfml import sf


def create_rect(x, y, w, h, color):
    rect = sf.RectangleShape()
    rect.position = (x, y)
    rect.size = (w, h)
    rect.fill_color = color
    return rect


def get_mouse_pos(hwnd):
    mx = sf.Mouse.get_position(hwnd).x
    my = sf.Mouse.get_position(hwnd).y
    return hwnd.map_pixel_to_coords((mx, my))
