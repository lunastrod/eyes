from dataclasses import dataclass, field
from typing import List

VIEWPORT = 100
K = 0.5523

LEFT_CENTER = (25.0, 50.0)
RIGHT_CENTER = (75.0, 50.0)


def _f(v: float) -> str:
    return f"{round(v, 4):g}"


def _circle_path(cx: float, cy: float, r: float) -> str:
    kr = K * r
    top, bottom = cy - r, cy + r
    left, right = cx - r, cx + r
    return (
        f"M {_f(cx)} {_f(top)} L {_f(cx)} {_f(top)} "
        f"C {_f(cx+kr)} {_f(top)} {_f(right)} {_f(cy-kr)} {_f(right)} {_f(cy)} "
        f"L {_f(right)} {_f(cy)} "
        f"C {_f(right)} {_f(cy+kr)} {_f(cx+kr)} {_f(bottom)} {_f(cx)} {_f(bottom)} "
        f"L {_f(cx)} {_f(bottom)} "
        f"C {_f(cx-kr)} {_f(bottom)} {_f(left)} {_f(cy+kr)} {_f(left)} {_f(cy)} "
        f"L {_f(left)} {_f(cy)} "
        f"C {_f(left)} {_f(cy-kr)} {_f(cx-kr)} {_f(top)} {_f(cx)} {_f(top)} Z"
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
    target: str
    prop: str
    value_from: str
    value_to: str
    duration_ms: int
    value_type: str = "floatType"
    interpolator: str = "@android:interpolator/fast_out_slow_in"


class Eye:
    RADIUS = 12.0
    CLOSED_HEIGHT = 6.0

    def __init__(self, name: str, center: tuple, color: str = "#FFFFFFFF"):
        self.name = name
        self.center = center
        self.color = color
        self._keyframes: List[Keyframe] = []
        self.curr_tx = 0.0
        self.curr_ty = 0.0
        self.curr_scale = 1.0

    @property
    def group_name(self) -> str:
        return f"{self.name}_eye_group"

    @property
    def path_name(self) -> str:
        return f"{self.name}_eye"

    @property
    def open_path(self) -> str:
        return _circle_path(*self.center, self.RADIUS)

    @property
    def closed_path(self) -> str:
        cx, cy = self.center
        w = self.RADIUS * 2
        r = self.CLOSED_HEIGHT / 2
        return _pill_path(cx, cy, w, self.CLOSED_HEIGHT, r)

    def move(self, tx: float, ty: float, duration: float):
        """Translate eye from current position to tx, ty."""
        ms = int(duration * 1000)
        if tx != self.curr_tx:
            self._keyframes.append(Keyframe(
                self.group_name, "translateX",
                str(self.curr_tx), str(tx), ms,
            ))
        if ty != self.curr_ty:
            self._keyframes.append(Keyframe(
                self.group_name, "translateY",
                str(self.curr_ty), str(ty), ms,
            ))
        self.curr_tx, self.curr_ty = tx, ty

    def blink(self, duration: float):
        """Morph path from open to closed and back."""
        ms = int(duration * 1000)
        open_p, closed_p = self.open_path, self.closed_path
        self._keyframes.append(Keyframe(
            self.path_name, "pathData",
            open_p, closed_p, ms, "pathType",
        ))
        self._keyframes.append(Keyframe(
            self.path_name, "pathData",
            closed_p, open_p, ms, "pathType",
        ))

    def dilate(self, scale: float, duration: float):
        """Scale eye from current scale to new scale and back."""
        ms = int(duration * 1000)
        for prop in ("scaleX", "scaleY"):
            self._keyframes.append(Keyframe(
                self.group_name, prop,
                str(self.curr_scale), str(scale), ms,
            ))
        for prop in ("scaleX", "scaleY"):
            self._keyframes.append(Keyframe(
                self.group_name, prop,
                str(scale), str(self.curr_scale), ms,
            ))

    def wait_position(self, duration: float):
        """Hold current translation for duration seconds."""
        ms = int(duration * 1000)
        self._keyframes.append(Keyframe(
            self.group_name, "translateX",
            str(self.curr_tx), str(self.curr_tx), ms,
        ))

    def wait_shape(self, duration: float):
        """Hold open path shape for duration seconds."""
        ms = int(duration * 1000)
        self._keyframes.append(Keyframe(
            self.path_name, "pathData",
            self.open_path, self.open_path, ms, "pathType",
        ))

    def keyframes(self) -> List[Keyframe]:
        return self._keyframes


def _group_into_steps(keyframes: List[Keyframe]) -> List[List[Keyframe]]:
    """Group consecutive keyframes with same duration and different props as simultaneous."""
    if not keyframes:
        return []
    steps = []
    i = 0
    while i < len(keyframes):
        current = keyframes[i]
        group = [current]
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


def _build_animator_set(keyframes: List[Keyframe]) -> List[tuple]:
    """Group keyframes by target name, then into steps."""
    by_target: dict = {}
    for kf in keyframes:
        by_target.setdefault(kf.target, []).append(kf)
    return [(name, _group_into_steps(kfs)) for name, kfs in by_target.items()]


def _animator_xml(kf: Keyframe, indent: int, repeat_count: int = 0) -> str:
    pad = "    " * indent
    rc_line = f'\n{pad}    android:repeatCount="{repeat_count}"' if repeat_count != 0 else ""
    return (
        f'{pad}<objectAnimator\n'
        f'{pad}    android:propertyName="{kf.prop}"\n'
        f'{pad}    android:duration="{kf.duration_ms}"\n'
        f'{pad}    android:valueFrom="{kf.value_from}"\n'
        f'{pad}    android:valueTo="{kf.value_to}"\n'
        f'{pad}    android:valueType="{kf.value_type}"\n'
        f'{pad}    android:interpolator="{kf.interpolator}"{rc_line}/>'
    )


def compile_xml(left: Eye, right: Eye, output_path: str, color: str = "#FFFFFFFF"):
    lines = [
        '<animated-vector',
        '    xmlns:android="http://schemas.android.com/apk/res/android"',
        '    xmlns:aapt="http://schemas.android.com/aapt">',
        '    <aapt:attr name="android:drawable">',
        '        <vector',
        '            android:name="vector"',
        '            android:width="100dp"',
        '            android:height="100dp"',
        '            android:viewportWidth="100"',
        '            android:viewportHeight="100">',
    ]

    for eye in (left, right):
        cx, cy = eye.center
        lines += [
            f'            <group',
            f'                android:name="{eye.group_name}"',
            f'                android:pivotX="{_f(cx)}"',
            f'                android:pivotY="{_f(cy)}">',
            f'                <path',
            f'                    android:name="{eye.path_name}"',
            f'                    android:pathData="{eye.open_path}"',
            f'                    android:fillColor="{color}"/>',
            f'            </group>',
        ]

    lines += ['        </vector>', '    </aapt:attr>']

    for eye in (left, right):
        for target_name, steps in _build_animator_set(eye.keyframes()):
            lines += [
                f'    <target android:name="{target_name}">',
                f'        <aapt:attr name="android:animation">',
                f'            <set android:ordering="sequentially">',
            ]
            for step in steps:
                if len(step) == 1:
                    lines.append(_animator_xml(step[0], indent=4))
                else:
                    lines.append(f'                <set android:ordering="together">')
                    for kf in step:
                        lines.append(_animator_xml(kf, indent=5))
                    lines.append(f'                </set>')
            lines += [
                f'            </set>',
                f'        </aapt:attr>',
                f'    </target>',
            ]

    lines.append('</animated-vector>')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Written: {output_path}")


if __name__ == "__main__":
    left = Eye("left", LEFT_CENTER)
    right = Eye("right", RIGHT_CENTER)
    left.move(10, 0, 0.5)
    right.move(10, 0, 0.5)
    compile_xml(left, right, "eyes_look_right.xml")

    left2 = Eye("left", LEFT_CENTER)
    right2 = Eye("right", RIGHT_CENTER)
    left2.blink(0.1)
    right2.blink(0.1)
    left2.wait_shape(0.2)
    right2.wait_shape(0.2)
    left2.blink(0.1)
    right2.blink(0.1)
    left2.wait_shape(0.7)
    right2.wait_shape(0.7)
    compile_xml(left2, right2, "eyes_blink.xml")

    left3 = Eye("left", LEFT_CENTER)
    right3 = Eye("right", RIGHT_CENTER)
    left3.dilate(1.1, 1.0)
    right3.dilate(1.1, 1.0)
    compile_xml(left3, right3, "eyes_dilate.xml")

    left4 = Eye("left", LEFT_CENTER)
    right4 = Eye("right", RIGHT_CENTER)
    left4.blink(0.1)
    right4.blink(0.1)
    compile_xml(left4, right4, "eyes_blink_loop.xml")