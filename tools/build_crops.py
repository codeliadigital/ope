"""Recorta imágenes de los resúmenes (resumenes-md/img/) para las preguntas con imagen
de los tests de los temas, tapando las etiquetas que darían la respuesta.

Coordenadas en fracciones de la imagen original: (x0, y0, x1, y1).
Cada máscara se rellena con el color medio de su borde y puede llevar un rótulo.

Uso:  python tools/build_crops.py
"""
import os

from PIL import Image, ImageDraw, ImageFont, ImageStat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "resumenes-md", "img")
OUT = os.path.join(ROOT, "img", "preguntas")

CROPS = {
    "t20-angulos.jpg": ("tema-20-1.jpg", (0.0, 0.17, 1.0, 1.0), [
        ((0.065, 0.305, 0.20, 0.355), ""), ((0.065, 0.485, 0.20, 0.535), ""),
        ((0.065, 0.685, 0.21, 0.735), ""), ((0.065, 0.865, 0.21, 0.915), "")]),
    "t26-agarre.jpg": ("tema-26-1.jpg", (0.0, 0.20, 0.5, 1.0), [((0.375, 0.43, 0.49, 0.545), "")]),
    "t28-barlow.jpg": ("tema-28-2.jpg", (0.0, 0.50, 0.31, 0.84), []),
    "t40-ruidos.jpg": ("tema-40-3.jpg", (0.0, 0.0, 1.0, 1.0), [
        ((0.225, 0.045, 0.385, 0.155), "1"), ((0.155, 0.265, 0.315, 0.375), "2"),
        ((0.135, 0.425, 0.305, 0.545), "3"), ((0.70, 0.67, 0.885, 0.795), "4"),
        ((0.685, 0.855, 0.865, 0.975), "5")]),
    "t41-electrodos.jpg": ("tema-41-2.jpg", (0.0, 0.22, 1.0, 1.0), []),
    "t43-valgo.jpg": ("tema-43-2.jpg", (0.02, 0.19, 0.22, 0.80), []),
    "t44-hernia.jpg": ("tema-44-2.jpg", (0.55, 0.14, 1.0, 1.0), []),
    "t44-hemorroides.jpg": ("tema-44-3.jpg", (0.50, 0.0, 0.76, 0.76), []),
    "t44-colostomia.jpg": ("tema-44-4.jpg", (0.07, 0.165, 0.33, 0.335), []),
    "t45-weber.jpg": ("tema-45-5.jpg", (0.345, 0.27, 0.665, 0.68), []),
    "t47-chvostek.jpg": ("tema-47-3.jpg", (0.02, 0.245, 0.49, 0.67), [((0.33, 0.53, 0.49, 0.67), "")]),
    "t47-insulina.jpg": ("tema-47-1.jpg", (0.325, 0.12, 0.82, 1.0), [
        ((0.325, 0.30, 0.445, 0.80), ""), ((0.615, 0.635, 0.69, 0.70), ""),
        ((0.785, 0.635, 0.82, 0.70), "")]),
    "t50-raquidea.jpg": ("tema-50-2.jpg", (0.50, 0.07, 1.0, 0.93), []),
    "t53-upp.jpg": ("tema-53-1.jpg", (0.585, 0.27, 0.79, 0.655), []),
}


def border_color(img, box):
    x0, y0, x1, y1 = box
    strips = [img.crop((x0, max(0, y0 - 3), x1, y0)), img.crop((x0, y1, x1, min(img.height, y1 + 3)))]
    vals = [ImageStat.Stat(s).median for s in strips if s.width and s.height]
    return tuple(int(sum(v[i] for v in vals) / len(vals)) for i in range(3))


def main():
    try:
        font = ImageFont.truetype("arialbd.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    for name, (src, crop, masks) in CROPS.items():
        img = Image.open(os.path.join(SRC, src)).convert("RGB")
        W, H = img.size
        d = ImageDraw.Draw(img)
        for (mx0, my0, mx1, my1), label in masks:
            box = (int(mx0 * W), int(my0 * H), int(mx1 * W), int(my1 * H))
            if label:
                d.rounded_rectangle(box, radius=10, fill=(255, 255, 255), outline=(29, 61, 92), width=3)
                d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), label, fill=(29, 61, 92), font=font, anchor="mm")
            else:
                d.rectangle(box, fill=border_color(img, box))
        out = img.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
        out.thumbnail((900, 700))
        out.save(os.path.join(OUT, name), quality=82, optimize=True)
    print(len(CROPS), "recortes en img/preguntas/")


if __name__ == "__main__":
    main()
