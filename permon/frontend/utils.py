def format_labels(axis_values):
    max_value = abs(max(axis_values))

    def format_value(x):
        if max_value <= 10:
            return '{:.3f}'.format(x)
        elif max_value <= 100:
            return '{:.2f}'.format(x)
        elif max_value <= 1000:
            return '{:.1f}'.format(x)
        elif max_value <= 10000:
            return str(int(x / 50) * 50)
        elif max_value > 10000:
            return str(int(x / 100) * 100)

    return [format_value(x) for x in axis_values]
