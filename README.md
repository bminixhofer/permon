# permon
A tool to view GPU, CPU, RAM and disk performance in a clear, uncluttered way.

## Getting started
This project measures CPU, RAM, GPU and Disk I/O stats and displays a simple line chart.
The chart can be displayed either in the console or in a simple GUI.

![performance with a GUI](https://user-images.githubusercontent.com/13353204/35768304-e6dcb9a0-08f9-11e8-8588-664a25fef891.png)
![performance in the CLI](https://user-images.githubusercontent.com/13353204/35768298-cf8f1e5a-08f9-11e8-9879-07b923f2c429.png)

### Installing
*Note: At the moment, performance only works on Linux systems.*

Install the project with

`pip install permon`

If you want the latest, possibly unstable version you can also clone the repository and run

`python setup.py install`

`nvidia-smi` and `sysstats` are also needed to display GPU RAM and disk read / write performance, respectively. RAM and CPU measurements will work without these though.

## Running the tool

Once installed, run `permon` in the terminal to use the GUI version of the tool.
To use the terminal frontend, run `permon -t` or `permon --terminal`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
