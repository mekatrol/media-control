import math


def euclidean_distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def vector(a, b):
    return (b.x - a.x, b.y - a.y, b.z - a.z)


def dot(v1, v2):
    return sum(a * b for a, b in zip(v1, v2))


def magnitude(v):
    return math.sqrt(sum(a * a for a in v))


def angle_between(v1, v2):
    mag1 = magnitude(v1)
    mag2 = magnitude(v2)
    if mag1 == 0 or mag2 == 0:
        return 0.0
    cos_angle = dot(v1, v2) / (mag1 * mag2)
    # Clamp to avoid math domain errors
    cos_angle = max(min(cos_angle, 1.0), -1.0)
    return math.degrees(math.acos(cos_angle))
