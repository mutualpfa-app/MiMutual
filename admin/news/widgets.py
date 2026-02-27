"""
Widget de drag & drop para campos de URL de imagen en el admin de Django.
"""
from django.forms.widgets import TextInput
from django.utils.html import escape, mark_safe


class ImageDropWidget(TextInput):
    """
    Reemplaza el TextInput del campo image_url con una zona de arrastrar-y-soltar.
    Al soltar un archivo, lo sube al endpoint de upload y llena el input con la URL resultante.
    También permite tipear la URL manualmente.
    """

    upload_url = "/admin/news/news/upload-image/"

    class Media:
        css = {"all": ("news/css/image_drop.css",)}
        js = ("news/js/image_drop.js",)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs["placeholder"] = "Ingresá una URL o arrastrá una imagen"
        input_html = super().render(name, value, attrs, renderer)

        preview_html = ""
        if value:
            safe_url = escape(value)
            preview_html = (
                f'<div class="image-drop-preview">'
                f'<img src="{safe_url}" alt="Preview de imagen" />'
                f"</div>"
            )

        return mark_safe(
            f'<div class="image-drop-widget" data-upload-url="{self.upload_url}">'
            f"{input_html}"
            f'<div class="image-drop-zone">'
            f'<div class="image-drop-zone__inner">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24"'
            f' fill="none" stroke="currentColor" stroke-width="1.5"'
            f' stroke-linecap="round" stroke-linejoin="round">'
            f'<polyline points="16 16 12 12 8 16"></polyline>'
            f'<line x1="12" y1="12" x2="12" y2="21"></line>'
            f'<path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path>'
            f"</svg>"
            f"<p>Arrastrá una imagen aquí</p>"
            f"<small>o hacé click para seleccionar &mdash; JPG, PNG, WebP, GIF &bull; máx. 5MB</small>"
            f"</div>"
            f'<div class="image-drop-zone__overlay">Soltá para subir</div>'
            f"</div>"
            f'<div class="image-drop-status"></div>'
            f"{preview_html}"
            f"</div>"
        )
