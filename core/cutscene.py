from __future__ import annotations

from typing import Any, Callable
import math


class CutsceneAction:
    """Base class for all cutscene actions in a timeline sequence."""

    def __init__(self) -> None:
        """Initialise base action."""
        self.started: bool = False
        self.finished: bool = False

    def start(self, context: dict[str, Any]) -> None:
        """Called once when the action begins."""
        self.started = True

    def update(self, dt: float, context: dict[str, Any]) -> bool:
        """Advance action execution. Return True when finished."""
        return True

    def finish(self, context: dict[str, Any]) -> None:
        """Called when action concludes or is skipped."""
        self.finished = True


class MoveCameraTo(CutsceneAction):
    """Interpolate camera center coordinates to a target position over duration."""

    def __init__(self, target_x: float, target_y: float, duration: float = 1.0) -> None:
        """Initialise camera pan target and duration."""
        super().__init__()
        self.target_x = target_x
        self.target_y = target_y
        self.duration = max(0.001, duration)
        self.elapsed: float = 0.0
        self.start_x: float = 0.0
        self.start_y: float = 0.0

    def start(self, context: dict[str, Any]) -> None:
        """Record initial camera coordinates."""
        super().start(context)
        cam = context.get("camera")
        if cam is not None:
            self.start_x = getattr(cam, "x", 0.0)
            self.start_y = getattr(cam, "y", 0.0)

    def update(self, dt: float, context: dict[str, Any]) -> bool:
        """Interpolate camera towards target."""
        self.elapsed += dt
        t = min(1.0, self.elapsed / self.duration)
        cam = context.get("camera")
        if cam is not None:
            cam.x = self.start_x + (self.target_x - self.start_x) * t
            cam.y = self.start_y + (self.target_y - self.start_y) * t
        if t >= 1.0:
            self.finish(context)
            return True
        return False

    def finish(self, context: dict[str, Any]) -> None:
        """Snap camera directly to target position."""
        super().finish(context)
        cam = context.get("camera")
        if cam is not None:
            cam.x = self.target_x
            cam.y = self.target_y


class MoveEntityTo(CutsceneAction):
    """Move a physics or visual entity towards a target position at constant speed."""

    def __init__(self, entity_id: str, target_x: float, target_y: float, speed: float = 60.0) -> None:
        """Initialise entity move parameters."""
        super().__init__()
        self.entity_id = entity_id
        self.target_x = target_x
        self.target_y = target_y
        self.speed = max(1.0, speed)

    def update(self, dt: float, context: dict[str, Any]) -> bool:
        """Step entity position towards target."""
        entities = context.get("entities", {})
        entity = entities.get(self.entity_id) if isinstance(entities, dict) else None
        if entity is None:
            self.finish(context)
            return True

        body = getattr(entity, "body", None)
        cx = body.position.x if body is not None else getattr(entity, "x", self.target_x)
        cy = body.position.y if body is not None else getattr(entity, "y", self.target_y)

        dx = self.target_x - cx
        dy = self.target_y - cy
        dist = math.hypot(dx, dy)
        step = self.speed * dt

        if dist <= step or dist < 0.5:
            self.finish(context)
            return True

        nx = cx + (dx / dist) * step
        ny = cy + (dy / dist) * step
        if body is not None:
            body.position = (nx, ny)
            body.velocity = ((dx / dist) * self.speed, (dy / dist) * self.speed)
        else:
            setattr(entity, "x", nx)
            setattr(entity, "y", ny)
        return False

    def finish(self, context: dict[str, Any]) -> None:
        """Snap entity directly to target coordinates."""
        super().finish(context)
        entities = context.get("entities", {})
        entity = entities.get(self.entity_id) if isinstance(entities, dict) else None
        if entity is not None:
            body = getattr(entity, "body", None)
            if body is not None:
                body.position = (self.target_x, self.target_y)
                body.velocity = (0.0, 0.0)
            else:
                setattr(entity, "x", self.target_x)
                setattr(entity, "y", self.target_y)


class PlayAnimation(CutsceneAction):
    """Trigger an animation state on an entity."""

    def __init__(self, entity_id: str, anim_name: str, loop: bool = False, duration: float = 0.0) -> None:
        """Initialise animation action parameters."""
        super().__init__()
        self.entity_id = entity_id
        self.anim_name = anim_name
        self.loop = loop
        self.duration = duration
        self.elapsed: float = 0.0

    def start(self, context: dict[str, Any]) -> None:
        """Set entity animation state."""
        super().start(context)
        entities = context.get("entities", {})
        entity = entities.get(self.entity_id) if isinstance(entities, dict) else None
        if entity is not None and hasattr(entity, "set_animation"):
            entity.set_animation(self.anim_name, self.loop)

    def update(self, dt: float, context: dict[str, Any]) -> bool:
        """Wait for duration if specified, otherwise complete immediately."""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finish(context)
            return True
        return False


class ShowEmote(CutsceneAction):
    """Display a floating emote bubble above an entity."""

    def __init__(self, entity_id: str, emote_type: str, duration: float = 1.5) -> None:
        """Initialise emote action."""
        super().__init__()
        self.entity_id = entity_id
        self.emote_type = emote_type
        self.duration = duration
        self.elapsed: float = 0.0

    def start(self, context: dict[str, Any]) -> None:
        """Attach emote bubble to entity via dialogue or manager."""
        super().start(context)
        emotes = context.get("emote_manager")
        entities = context.get("entities", {})
        entity = entities.get(self.entity_id) if isinstance(entities, dict) else None
        if emotes is not None and hasattr(emotes, "spawn_bubble"):
            emotes.spawn_bubble(self.entity_id, entity, self.emote_type, self.duration)

    def update(self, dt: float, context: dict[str, Any]) -> bool:
        """Advance emote timer."""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finish(context)
            return True
        return False


class ShowDialogue(CutsceneAction):
    """Present a dialogue box line and wait until advanced by user or cutscene."""

    def __init__(
        self,
        speaker_id: str,
        speaker_name: str,
        text_key: str,
        default_text: str = "",
        portrait_key: str = ""
    ) -> None:
        """Initialise dialogue action line."""
        super().__init__()
        self.speaker_id = speaker_id
        self.speaker_name = speaker_name
        self.text_key = text_key
        self.default_text = default_text
        self.portrait_key = portrait_key

    def start(self, context: dict[str, Any]) -> None:
        """Open dialogue box with line."""
        super().start(context)
        dbox = context.get("dialogue_box")
        if dbox is not None and hasattr(dbox, "show_message"):
            dbox.show_message(
                self.speaker_id,
                self.speaker_name,
                self.text_key,
                self.default_text,
                self.portrait_key
            )

    def update(self, dt: float, context: dict[str, Any]) -> bool:
        """Wait until dialogue box closes."""
        dbox = context.get("dialogue_box")
        if dbox is None or not getattr(dbox, "is_open", False):
            self.finish(context)
            return True
        return False

    def finish(self, context: dict[str, Any]) -> None:
        """Close dialogue box if still open."""
        super().finish(context)
        dbox = context.get("dialogue_box")
        if dbox is not None and hasattr(dbox, "close"):
            dbox.close()


class Wait(CutsceneAction):
    """Pause cutscene progression for a duration in seconds."""

    def __init__(self, duration: float) -> None:
        """Initialise wait duration."""
        super().__init__()
        self.duration = duration
        self.elapsed: float = 0.0

    def update(self, dt: float, context: dict[str, Any]) -> bool:
        """Advance wait timer."""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finish(context)
            return True
        return False


class TriggerEvent(CutsceneAction):
    """Emit an event on the event bus or invoke a callback instantly."""

    def __init__(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        """Initialise trigger event parameters."""
        super().__init__()
        self.event_name = event_name
        self.payload = payload or {}

    def start(self, context: dict[str, Any]) -> None:
        """Emit event immediately."""
        super().start(context)
        event_bus = context.get("event_bus")
        if event_bus is not None and hasattr(event_bus, "emit"):
            event_bus.emit(self.event_name, **self.payload)
        callback = context.get(f"on_{self.event_name}")
        if callable(callback):
            callback(self.payload)
        self.finish(context)

    def update(self, dt: float, context: dict[str, Any]) -> bool:
        """Instant action completes immediately."""
        return True


class CutsceneManager:
    """Manages sequential cutscene execution, actions queue, and skipping."""

    def __init__(self) -> None:
        """Initialise empty CutsceneManager."""
        self.timeline: list[CutsceneAction] = []
        self.current_index: int = 0
        self.is_active: bool = False
        self.context: dict[str, Any] = {}
        self.on_complete: Callable[[], None] | None = None

    def start_cutscene(
        self,
        actions: list[CutsceneAction],
        context: dict[str, Any],
        on_complete: Callable[[], None] | None = None
    ) -> None:
        """Begin executing a new cutscene action sequence."""
        self.timeline = list(actions)
        self.current_index = 0
        self.context = context
        self.is_active = len(self.timeline) > 0
        self.on_complete = on_complete
        if self.is_active and len(self.timeline) > 0:
            self.timeline[0].start(self.context)

    def update(self, dt: float) -> None:
        """Advance current cutscene action by delta time."""
        if not self.is_active or self.current_index >= len(self.timeline):
            return

        action = self.timeline[self.current_index]
        if not action.started:
            action.start(self.context)

        finished = action.update(dt, self.context)
        if finished:
            if not action.finished:
                action.finish(self.context)
            self.current_index += 1
            if self.current_index < len(self.timeline):
                self.timeline[self.current_index].start(self.context)
            else:
                self.stop()

    def skip(self) -> None:
        """Skip currently active action or the remainder of the cutscene."""
        if not self.is_active:
            return

        dbox = self.context.get("dialogue_box")
        if dbox is not None and getattr(dbox, "is_open", False):
            if getattr(dbox, "is_typing", False):
                dbox.fast_forward()
                return

        while self.current_index < len(self.timeline):
            act = self.timeline[self.current_index]
            if not act.started:
                act.start(self.context)
            act.finish(self.context)
            self.current_index += 1

        self.stop()

    def stop(self) -> None:
        """Conclude cutscene and invoke completion callback."""
        self.is_active = False
        self.timeline = []
        self.current_index = 0
        if self.on_complete is not None:
            cb = self.on_complete
            self.on_complete = None
            cb()
