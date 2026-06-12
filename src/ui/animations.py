"""
TurboShare — Lottie animation widget.

Wraps QWebEngineView to render Lottie JSON animations using a locally
bundled lottie-web.min.js.  No network access required.
"""

from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

from src.core.config import JS_DIR, ANIMATIONS_DIR


class LottieWidget(QWebEngineView):
    """A QWebEngineView that plays a Lottie animation."""

    def __init__(
        self,
        animation_name: str = "",
        width: int = 200,
        height: int = 200,
        loop: bool = True,
        parent=None,
    ):
        super().__init__(parent)

        self.setFixedSize(width, height)
        self._loop = loop
        self._animation_name = animation_name

        # Transparent background
        self.setStyleSheet("background: transparent;")
        self.page().setBackgroundColor(Qt.GlobalColor.transparent)

        # Disable unnecessary features
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        if animation_name:
            self.load_animation(animation_name)

    def load_animation(self, animation_name: str) -> None:
        """Load and play a Lottie animation by name.

        The name maps to ``assets/animations/{name}.json``.
        """
        self._animation_name = animation_name
        lottie_js = JS_DIR / "lottie-web.min.js"
        anim_json = ANIMATIONS_DIR / f"{animation_name}.json"

        if not lottie_js.is_file():
            self.setHtml(self._fallback_html(animation_name))
            return

        # Read the animation JSON inline to avoid file:// CORS issues
        anim_data = "{}"
        if anim_json.is_file():
            anim_data = anim_json.read_text(encoding="utf-8")

        loop_str = "true" if self._loop else "false"

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; }}
  body {{ background: transparent; overflow: hidden; }}
  #lottie {{ width: 100%; height: 100%; }}
</style>
</head>
<body>
<div id="lottie"></div>
<script src="{lottie_js.as_uri()}"></script>
<script>
  var animData = {anim_data};
  lottie.loadAnimation({{
    container: document.getElementById('lottie'),
    renderer: 'svg',
    loop: {loop_str},
    autoplay: true,
    animationData: animData
  }});
</script>
</body>
</html>"""

        self.setHtml(html, QUrl.fromLocalFile(str(JS_DIR / "index.html")))

    def set_animation(self, animation_name: str) -> None:
        """Switch to a different animation."""
        self.load_animation(animation_name)

    def play(self) -> None:
        self.page().runJavaScript("if(typeof lottie!=='undefined') lottie.play();")

    def stop(self) -> None:
        self.page().runJavaScript("if(typeof lottie!=='undefined') lottie.stop();")

    def pause(self) -> None:
        self.page().runJavaScript("if(typeof lottie!=='undefined') lottie.pause();")

    def _fallback_html(self, name: str) -> str:
        """Simple fallback when lottie-web.min.js is missing."""
        return f"""<!DOCTYPE html>
<html>
<head><style>
  body {{
    margin: 0; display: flex; align-items: center; justify-content: center;
    height: 100vh; background: transparent; color: #00D4AA;
    font-family: Inter, sans-serif; font-size: 14px;
  }}
  .pulse {{
    width: 60px; height: 60px; border-radius: 50%;
    background: rgba(0,212,170,0.2); animation: pulse 2s ease infinite;
  }}
  @keyframes pulse {{
    0%,100% {{ transform: scale(0.8); opacity: 0.5; }}
    50% {{ transform: scale(1.2); opacity: 1; }}
  }}
</style></head>
<body><div class="pulse"></div></body>
</html>"""
