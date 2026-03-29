from dataclasses import dataclass, field
from typing import Optional

VIEWPORT = 100
EYE_RADIUS = 12.5
K = 0.5523

LEFT_CENTER = (25.0, 50.0)
RIGHT_CENTER = (75.0, 50.0)

OPEN_PATH_TEMPLATE = (
    "M {cx} {top} L {cx} {top} "
    "C {crx} {top} {right} {cty} {right} {cy} "
    "L {right} {cy} "
    "C {right} {cby} {crx} {bottom} {cx} {bottom} "
    "L {cx} {bottom} "
    "C {clx} {bottom} {left} {cby} {left} {cy} "
    "L {left} {cy} "
    "C {left} {cty} {clx} {top} {cx} {top} Z"
)

CLOSED_HEIGHT = 10.0
CLOSED_RADIUS = 5.0


def _f(v: float) -> str:
    return f"{round(v, 4):g}"


def _circle_path(cx: float, cy: float, r: float) -> str:
    kr = K * r
    top, bottom = cy - r, cy + r
    left, right = cx - r, cx + r
    return OPEN_PATH_TEMPLATE.format(
        cx=_f(cx), cy=_f(cy),
        top=_f(top), bottom=_f(bottom), left=_f(left), right=_f(right),
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


@dataclass
class Keyframe:
    target: str          # element name in the vector
    prop: str            # android property name
    value_from: str
    value_to: str
    duration_ms: int
    value_type: str = "floatType"
    interpolator: str = "@android:interpolator/fast_out_slow_in"


@dataclass
class Eye:
    name: str            # "left" or "right"
    center: tuple

    _keyframes: list = field(default_factory=list, init=False)

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
        w = EYE_RADIUS * 2
        return _pill_path(cx, cy, w, CLOSED_HEIGHT, CLOSED_RADIUS)

    def move(self, dx: float, dy: float, duration: float):
        """Translate both eyes by dx, dy over duration seconds."""
        ms = int(duration * 1000)
        if dx != 0:
            self._keyframes.append(Keyframe(
                target=self.group_name, prop="translateX",
                value_from="0", value_to=str(dx), duration_ms=ms,
            ))
        if dy != 0:
            self._keyframes.append(Keyframe(
                target=self.group_name, prop="translateY",
                value_from="0", value_to=str(dy), duration_ms=ms,
            ))

    def blink(self, duration: float):
        """Close then reopen eye, each half taking duration seconds."""
        ms = int(duration * 1000)
        open_p = self.open_path
        closed_p = self.closed_path
        self._keyframes.append(Keyframe(
            target=self.path_name, prop="pathData",
            value_from=open_p, value_to=closed_p,
            duration_ms=ms, value_type="pathType",
        ))
        self._keyframes.append(Keyframe(
            target=self.path_name, prop="pathData",
            value_from=closed_p, value_to=open_p,
            duration_ms=ms, value_type="pathType",
        ))

    def dilate(self, scale: float, duration: float):
        """Scale eye from 1.0 to scale and back, each phase taking duration seconds."""
        ms = int(duration * 1000)
        for prop in ("scaleX", "scaleY"):
            self._keyframes.append(Keyframe(
                target=self.group_name, prop=prop,
                value_from="1.0", value_to=str(scale), duration_ms=ms,
            ))
        for prop in ("scaleX", "scaleY"):
            self._keyframes.append(Keyframe(
                target=self.group_name, prop=prop,
                value_from=str(scale), value_to="1.0", duration_ms=ms,
            ))

    def keyframes(self) -> list:
        return self._keyframes


def _indent(elem, level=0):
    """Add pretty-print indentation to an ElementTree in place."""
    indent = "\n" + "    " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def _build_animator_set(keyframes: list[Keyframe]) -> list:
    """Group keyframes by target, then build nested sets."""
    # Group by target name
    by_target: dict[str, list[Keyframe]] = {}
    for kf in keyframes:
        by_target.setdefault(kf.target, []).append(kf)

    # For each target, group consecutive keyframes that share the same prop
    # into sequential sets. If multiple props fire at the same time step,
    # wrap them in a "together" set.
    # Simple approach: all keyframes per target are sequential.
    targets = []
    for target_name, kfs in by_target.items():
        # Group into steps: keyframes with the same index position across props
        # are "together", sequential otherwise.
        # Since dilate emits scaleX/scaleY pairs, detect pairs by position.
        steps = _group_into_steps(kfs)
        targets.append((target_name, steps))
    return targets


def _group_into_steps(keyframes: list[Keyframe]) -> list[list[Keyframe]]:
    """
    Group keyframes into sequential steps. Consecutive keyframes with the
    same duration and different props are grouped as simultaneous.
    """
    if not keyframes:
        return []

    steps = []
    i = 0
    while i < len(keyframes):
        current = keyframes[i]
        group = [current]
        # Look ahead: same duration, different prop, same from/to pattern
        j = i + 1
        while j < len(keyframes):
            nxt = keyframes[j]
            if (nxt.duration_ms == current.duration_ms and
                    nxt.prop != current.prop and
                    nxt.target == current.target):
                group.append(nxt)
                j += 1
            else:
                break
        steps.append(group)
        i = j
    return steps


def _animator_xml(kf: Keyframe, indent: int) -> str:
    pad = "    " * indent
    return (
        f'{pad}<objectAnimator\n'
        f'{pad}    android:propertyName="{kf.prop}"\n'
        f'{pad}    android:duration="{kf.duration_ms}"\n'
        f'{pad}    android:valueFrom="{kf.value_from}"\n'
        f'{pad}    android:valueTo="{kf.value_to}"\n'
        f'{pad}    android:valueType="{kf.value_type}"\n'
        f'{pad}    android:interpolator="{kf.interpolator}"/>'
    )


def compile_xml(left: Eye, right: Eye, output_path: str):
    lines = []
    lines.append('<animated-vector')
    lines.append('    xmlns:android="http://schemas.android.com/apk/res/android"')
    lines.append('    xmlns:aapt="http://schemas.android.com/aapt">')
    lines.append('    <aapt:attr name="android:drawable">')
    lines.append('        <vector')
    lines.append('            android:name="vector"')
    lines.append('            android:width="100dp"')
    lines.append('            android:height="100dp"')
    lines.append('            android:viewportWidth="100"')
    lines.append('            android:viewportHeight="100">')

    for eye in (left, right):
        cx, cy = eye.center
        lines.append(f'            <group')
        lines.append(f'                android:name="{eye.group_name}"')
        lines.append(f'                android:pivotX="{_f(cx)}"')
        lines.append(f'                android:pivotY="{_f(cy)}">')
        lines.append(f'                <path')
        lines.append(f'                    android:name="{eye.path_name}"')
        lines.append(f'                    android:pathData="{eye.open_path}"')
        lines.append(f'                    android:fillColor="#FF000000"/>')
        lines.append(f'            </group>')

    lines.append('        </vector>')
    lines.append('    </aapt:attr>')

    for eye in (left, right):
        targets = _build_animator_set(eye.keyframes())
        for target_name, steps in targets:
            lines.append(f'    <target android:name="{target_name}">')
            lines.append(f'        <aapt:attr name="android:animation">')
            lines.append(f'            <set android:ordering="sequentially">')
            for step in steps:
                if len(step) == 1:
                    lines.append(_animator_xml(step[0], indent=4))
                else:
                    lines.append(f'                <set android:ordering="together">')
                    for kf in step:
                        lines.append(_animator_xml(kf, indent=5))
                    lines.append(f'                </set>')
            lines.append(f'            </set>')
            lines.append(f'        </aapt:attr>')
            lines.append(f'    </target>')

    lines.append('</animated-vector>')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Written: {output_path}")


# --- Example usage ---

if __name__ == "__main__":
    left = Eye("left", LEFT_CENTER)
    right = Eye("right", RIGHT_CENTER)

    # Look right and back
    left.move(10, 0, 0.5)
    right.move(10, 0, 0.5)

    compile_xml(left, right, "eyes_look_right_g.xml")

    left2 = Eye("left", LEFT_CENTER)
    right2 = Eye("right", RIGHT_CENTER)

    # Blink
    left2.blink(0.1)
    right2.blink(0.1)

    compile_xml(left2, right2, "eyes_blink_g.xml")

    left3 = Eye("left", LEFT_CENTER)
    right3 = Eye("right", RIGHT_CENTER)

    # Dilate
    left3.dilate(1.1, 1.0)
    right3.dilate(1.1, 1.0)

    compile_xml(left3, right3, "eyes_dilate_g.xml")
