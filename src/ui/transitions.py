"""
TurboShare — Page transition animations.

Provides fade and slide transitions between pages in the
QStackedWidget.  Uses QPropertyAnimation with smooth easing curves.
"""

from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup,
    QSequentialAnimationGroup, QAbstractAnimation, QByteArray,
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect


def _ensure_opacity_effect(widget: QWidget) -> QGraphicsOpacityEffect:
    """Attach a QGraphicsOpacityEffect if one doesn't exist."""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    return effect


def fade_transition(
    old_widget: QWidget | None,
    new_widget: QWidget,
    duration: int = 300,
    on_finished=None,
) -> QParallelAnimationGroup:
    """Cross-fade from *old_widget* to *new_widget*.

    Returns the animation group (caller should keep a reference alive).
    """
    group = QParallelAnimationGroup()

    # Fade out old
    if old_widget is not None:
        old_effect = _ensure_opacity_effect(old_widget)
        fade_out = QPropertyAnimation(old_effect, QByteArray(b"opacity"))
        fade_out.setDuration(duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(fade_out)

    # Fade in new
    new_effect = _ensure_opacity_effect(new_widget)
    new_effect.setOpacity(0.0)
    fade_in = QPropertyAnimation(new_effect, QByteArray(b"opacity"))
    fade_in.setDuration(duration)
    fade_in.setStartValue(0.0)
    fade_in.setEndValue(1.0)
    fade_in.setEasingCurve(QEasingCurve.Type.InCubic)
    group.addAnimation(fade_in)

    if on_finished:
        group.finished.connect(on_finished)

    group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    return group


def slide_left_transition(
    stacked_widget,
    old_index: int,
    new_index: int,
    duration: int = 400,
    on_finished=None,
):
    """Slide the old page out to the left and new page in from the right."""
    old_widget = stacked_widget.widget(old_index)
    new_widget = stacked_widget.widget(new_index)

    width = stacked_widget.width()

    # Position new widget off-screen to the right
    new_widget.setGeometry(width, 0, width, stacked_widget.height())
    new_widget.show()

    group = QParallelAnimationGroup(stacked_widget)

    # Slide old widget left
    if old_widget:
        anim_old = QPropertyAnimation(old_widget, QByteArray(b"pos"))
        anim_old.setDuration(duration)
        anim_old.setStartValue(old_widget.pos())
        anim_old.setEndValue(QPoint(-width, 0))
        anim_old.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(anim_old)

    # Slide new widget in
    anim_new = QPropertyAnimation(new_widget, QByteArray(b"pos"))
    anim_new.setDuration(duration)
    anim_new.setStartValue(QPoint(width, 0))
    anim_new.setEndValue(QPoint(0, 0))
    anim_new.setEasingCurve(QEasingCurve.Type.OutCubic)
    group.addAnimation(anim_new)

    def _on_done():
        stacked_widget.setCurrentIndex(new_index)
        if old_widget:
            old_widget.move(0, 0)
        if on_finished:
            on_finished()

    group.finished.connect(_on_done)
    group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    return group
