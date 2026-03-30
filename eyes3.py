from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union

VIEWPORT = 100
EYE_RADIUS = 12
K = 0.5523

LEFT_CENTER = (25.0, 50.0)
RIGHT_CENTER = (75.0, 50.0)

CLOSED_HEIGHT = 6.0
CLOSED_RADIUS = CLOSED_HEIGHT / 2

_CIRCLE_TEMPLATE = (
    "M {cx} {top} L {cx} {top} "
    "C {crx} {top} {right} {cty} {right} {cy} "
    "L {right} {cy} "
    "C {right} {cby} {crx} {bottom} {cx} {bottom} "
    "L {cx} {bottom} "
    "C {clx} {bottom} {left} {cby} {left} {cy} "
    "L {left} {cy} "
    "C {left} {cty} {clx} {top} {cx} {top} Z"
)


def _f(v: float) -> str:
    return f"{round(v, 4):g}"


def _circle_path(cx: float, cy: float, r: float) -> str:
    kr = K * r
    top, bottom = cy - r, cy + r
    left, right = cx - r, cx + r
    return _CIRCLE_TEMPLATE.format(
        cx=_f(cx), cy=_f(cy),
        top=_f(top), bottom=_f(bottom),
        left=_f(left), right=_f(right),
        crx=_f(cx + kr), clx=_f(cx - kr),
        cty=_f(cy - kr), cby=_f(cy + kr),
    )


def _pill_path(cx: float, cy: float, w: float, h: float, r: float) -> str:
    kr = K * r
    x, y = cx - w / 2, cy - h / 2
    n = _f
    return (
        f"M {n(x+r)} {n(y)} L {n(x+w-r)} {n(y)} "
        f"C {n(x+w-r+kr)} {n(y)} {n(x+w)} {n(y+r-kr)} {n(x+w)} {n(y+r)} "
        f"L {n(x+w)} {n(y+h-r)} "
        f"C {n(x+w)} {n(y+h-r+kr)} {n(x+w-r+kr)} {n(y+h)} {n(x+w-r)} {n(y+h)} "
        f"L {n(x+r)} {n(y+h)} "
        f"C {n(x+r-kr)} {n(y+h)} {n(x)} {n(y+h-r+kr)} {n(x)} {n(y+h-r)} "
        f"L {n(x)} {n(y+r)} "
        f"C {n(x)} {n(y+r-kr)} {n(x+r-kr)} {n(y)} {n(x+r)} {n(y)} Z"
    )


# ---------------------------------------------------------------------------
# Animation step types
# ---------------------------------------------------------------------------

@dataclass
class FloatAnimator:
    target: str
    prop: str
    value_from: float
    value_to: float
    duration_ms: int
    interpolator: str = "@android:interpolator/fast_out_slow_in"


@dataclass
class PathAnimator:
    target: str
    value_from: str
    value_to: str
    duration_ms: int
    interpolator: str = "@android:interpolator/fast_out_slow_in"

    @property
    def prop(self) -> str:
        return "pathData"


Animator = Union[FloatAnimator, PathAnimator]


@dataclass
class TogetherStep:
    """Two or more animators that fire simultaneously."""
    animators: list[Animator]


@dataclass
class SequentialStep:
    """A single animator in the sequential timeline."""
    animator: Animator


Step = Union[SequentialStep, TogetherStep]


# ---------------------------------------------------------------------------
# Eye
# ---------------------------------------------------------------------------

@dataclass
class Eye:
    name: str
    center: tuple[float, float]
    _steps: list[Step] = field(default_factory=list, init=False)
    _tx: float = field(default=0.0, init=False)
    _ty: float = field(default=0.0, init=False)
    _scale: float = field(default=1.0, init=False)

    @property
    def group_name(self) -> str:
        return f"{self.name}_eye_group"

    @property
    def path_name(self) -> str:
        return f"{self.name}_eye"

    @property
    def open_path(self) -> str:
        return _circle_path(*self.center, EYE_RADIUS)

    @property
    def closed_path(self) -> str:
        cx, cy = self.center
        return _pill_path(cx, cy, EYE_RADIUS * 2, CLOSED_HEIGHT, CLOSED_RADIUS)

    def _ms(self, duration: float) -> int:
        return int(duration * 1000)

    def move(self, tx: float, ty: float, duration: float) -> Eye:
        """Translate to (tx, ty)."""
        ms = self._ms(duration)
        animators = []
        if tx != self._tx:
            animators.append(FloatAnimator(self.group_name, "translateX", self._tx, tx, ms))
        if ty != self._ty:
            animators.append(FloatAnimator(self.group_name, "translateY", self._ty, ty, ms))
        if len(animators) == 1:
            self._steps.append(SequentialStep(animators[0]))
        elif len(animators) == 2:
            self._steps.append(TogetherStep(animators))
        self._tx, self._ty = tx, ty
        return self

    def wait_position(self, duration: float) -> Eye:
        """Hold current translation."""
        ms = self._ms(duration)
        self._steps.append(TogetherStep([
            FloatAnimator(self.group_name, "translateX", self._tx, self._tx, ms),
            FloatAnimator(self.group_name, "translateY", self._ty, self._ty, ms),
        ]))
        return self

    def wait_shape(self, duration: float) -> Eye:
        """Hold open path shape."""
        ms = self._ms(duration)
        self._steps.append(SequentialStep(
            PathAnimator(self.path_name, self.open_path, self.open_path, ms)
        ))
        return self

    def close(self, duration: float) -> Eye:
        """Morph open -> closed."""
        ms = self._ms(duration)
        self._steps.append(SequentialStep(
            PathAnimator(self.path_name, self.open_path, self.closed_path, ms)
        ))
        return self

    def open(self, duration: float) -> Eye:
        """Morph closed -> open."""
        ms = self._ms(duration)
        self._steps.append(SequentialStep(
            PathAnimator(self.path_name, self.closed_path, self.open_path, ms)
        ))
        return self
    
    def dilate(self, scale: float, duration: float) -> Eye:
        """Scale from current scale to `scale`."""
        ms = self._ms(duration)
        self._steps.append(TogetherStep([
            FloatAnimator(self.group_name, "scaleX", self._scale, scale, ms),
            FloatAnimator(self.group_name, "scaleY", self._scale, scale, ms),
        ]))
        self._scale = scale
        return self

    def steps(self) -> list[Step]:
        return self._steps


# ---------------------------------------------------------------------------
# XML compiler
# ---------------------------------------------------------------------------

class XmlCompiler:
    INDENT = "    "

    def __init__(self, color: str = "#FFFFFFFF"):
        self.color = color

    def compile(self, left: Eye, right: Eye, output_path: str) -> None:
        lines = self._header(left, right) + self._targets(left, right) + ["</animated-vector>"]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Written: {output_path}")

    # --- drawable section ---

    def _header(self, left: Eye, right: Eye) -> list[str]:
        i = self.INDENT
        lines = [
            '<animated-vector',
            f'{i}xmlns:android="http://schemas.android.com/apk/res/android"',
            f'{i}xmlns:aapt="http://schemas.android.com/aapt">',
            f'{i}<aapt:attr name="android:drawable">',
            f'{i*2}<vector',
            f'{i*3}android:name="vector"',
            f'{i*3}android:width="100dp"',
            f'{i*3}android:height="100dp"',
            f'{i*3}android:viewportWidth="100"',
            f'{i*3}android:viewportHeight="100">',
        ]
        for eye in (left, right):
            lines += self._eye_drawable(eye)
        lines += [
            f'{i*2}</vector>',
            f'{i}</aapt:attr>',
        ]
        return lines

    def _eye_drawable(self, eye: Eye) -> list[str]:
        i = self.INDENT
        cx, cy = eye.center
        return [
            f'{i*3}<group',
            f'{i*4}android:name="{eye.group_name}"',
            f'{i*4}android:pivotX="{_f(cx)}"',
            f'{i*4}android:pivotY="{_f(cy)}">',
            f'{i*4}<path',
            f'{i*5}android:name="{eye.path_name}"',
            f'{i*5}android:pathData="{eye.open_path}"',
            f'{i*5}android:fillColor="{self.color}"/>',
            f'{i*3}</group>',
        ]

    # --- animation targets ---

    def _targets(self, left: Eye, right: Eye) -> list[str]:
        lines = []
        for eye in (left, right):
            lines += self._eye_targets(eye)
        return lines

    def _eye_targets(self, eye: Eye) -> list[str]:
        by_target: dict[str, list[Step]] = {}
        for step in eye.steps():
            animators = step.animators if isinstance(step, TogetherStep) else [step.animator]
            for a in animators:
                by_target.setdefault(a.target, [])
            if isinstance(step, TogetherStep):
                targets_in_step = {a.target for a in step.animators}
                if len(targets_in_step) == 1:
                    t = next(iter(targets_in_step))
                    by_target[t].append(step)
                else:
                    for a in step.animators:
                        by_target[a.target].append(SequentialStep(a))
            else:
                by_target[step.animator.target].append(step)

        lines = []
        for target, steps in by_target.items():
            lines += self._target_block(target, steps)
        return lines

    def _target_block(self, target: str, steps: list[Step]) -> list[str]:
        i = self.INDENT
        lines = [
            f'{i}<target android:name="{target}">',
            f'{i*2}<aapt:attr name="android:animation">',
            f'{i*3}<set android:ordering="sequentially">',
        ]
        for step in steps:
            if isinstance(step, SequentialStep):
                lines.append(self._animator_xml(step.animator, depth=4))
            else:
                lines.append(f'{i*4}<set android:ordering="together">')
                for a in step.animators:
                    lines.append(self._animator_xml(a, depth=5))
                lines.append(f'{i*4}</set>')
        lines += [
            f'{i*3}</set>',
            f'{i*2}</aapt:attr>',
            f'{i}</target>',
        ]
        return lines

    def _animator_xml(self, a: Animator, depth: int) -> str:
        i = self.INDENT * depth
        if isinstance(a, PathAnimator):
            value_type = "pathType"
            v_from, v_to = a.value_from, a.value_to
        else:
            value_type = "floatType"
            v_from, v_to = _f(a.value_from), _f(a.value_to)
        return (
            f'{i}<objectAnimator\n'
            f'{i}    android:propertyName="{a.prop}"\n'
            f'{i}    android:duration="{a.duration_ms}"\n'
            f'{i}    android:valueFrom="{v_from}"\n'
            f'{i}    android:valueTo="{v_to}"\n'
            f'{i}    android:valueType="{value_type}"\n'
            f'{i}    android:interpolator="{a.interpolator}"/>'
        )


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    compiler = XmlCompiler()

    left = Eye("left", LEFT_CENTER)
    right = Eye("right", RIGHT_CENTER)
    left.blink(0.1)
    right.blink(0.1)
    compiler.compile(left, right, "eyes_blink.xml")

    left = Eye("left", LEFT_CENTER)
    right = Eye("right", RIGHT_CENTER)
    left.move(10, 0, 0.5)
    right.move(10, 0, 0.5)
    compiler.compile(left, right, "eyes_look_right.xml")

    left = Eye("left", LEFT_CENTER)
    right = Eye("right", RIGHT_CENTER)
    left.dilate(1.1, 1.0)
    right.dilate(1.1, 1.0)
    compiler.compile(left, right, "eyes_dilate.xml")