# permon

[![CircleCI](https://circleci.com/gh/bminixhofer/permon/tree/dev.svg?style=svg)](https://circleci.com/gh/bminixhofer/permon/tree/dev)
[![codecov](https://codecov.io/gh/bminixhofer/permon/branch/dev/graph/badge.svg)](https://codecov.io/gh/bminixhofer/permon)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/aeb0088ce100440f9077e1da6c6ca4f6)](https://www.codacy.com/app/bminixhofer/permon?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=bminixhofer/permon&amp;utm_campaign=Badge_Grade)

A tool to monitor everything you want. Clean, simple, extensible and in one place.


## Why permon?

- Permon is different to other performance monitors (like [glances](https://github.com/nicolargo/glances)). Permon shows you all stats you care about. Nothing more, nothing less. This leads to a cleaner GUI and makes it easy to see how stats change over time.

- Permon is extensible. Defining your own stats is simple. See the [custom stats section](#adding-your-own-stats) for details.
- Permon works everywhere, on Linux, Windows and MacOS. But thats not all. You can choose from 3 frontends.

### Terminal

TODO: Image of permon terminal

### Native

TODO: Image of permon native

### Browser

TODO: Image of permon browser

## Getting started

To install permon with pip run

`pip install permon`

and

`permon --help`

to see everything you can do.

## Adding your own stats

Run `permon show_config_dir` to check the location of permons config directory. You can then add your own python files to the `custom_stats/` subdirectory. For example, to display the sine, add this code to the file `custom_stats/math.py`:

```python
import math
from permon.backend import Stat

@Stat.windows
@Stat.linux
class SineStat(Stat):
    name = 'Sine'
    base_tag = 'sine'

    def __init__(self, fps):
        self.current = 0
        super(SineStat, self).__init__(fps=fps)

    def get_stat(self):
        self.current += 1 / self.fps
        return math.sin(self.current)

    @property
    def minimum(self):
        return -1

    @property
    def maximum(self):
        return 1
```

Let's break this down.

TODO: add more

## License

This project uses the MIT License - basically you can do whatever you want with the code - see the [LICENSE](LICENSE) file for details.
