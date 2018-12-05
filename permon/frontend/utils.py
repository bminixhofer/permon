def format_labels(axis_values):
    """
    Format the labels of an axis. Rounds the labels to some value based on the
    maximum value of the axis.
    """
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


def format_contributor_label(label, max_len=15):
    fill = '...'

    if len(label) > max_len:
        label = label[:max_len - len(fill)] + fill
    return label
