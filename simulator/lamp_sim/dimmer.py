def step_brightness(current: float, target: float, elapsed_s: float, rate_per_s: float) -> float:
    if elapsed_s < 0:
        raise ValueError("elapsed time cannot be negative")
    if rate_per_s <= 0:
        raise ValueError("fade rate must be positive")
    current = min(100.0, max(0.0, float(current)))
    target = min(100.0, max(0.0, float(target)))
    step = elapsed_s * rate_per_s
    if current < target:
        return min(target, current + step)
    return max(target, current - step)
