# performance
A tool to measure GPU, CPU, RAM and disk performance in one place.

## Getting started
This project measures CPU, RAM, GPU and Disk I/O stats and displays a simple line chart.
The chart can be displayed either in the console or in a simple GUI.

![performance with a GUI](https://user-images.githubusercontent.com/13353204/35768304-e6dcb9a0-08f9-11e8-8588-664a25fef891.png)
![performance in the CLI](https://user-images.githubusercontent.com/13353204/35768298-cf8f1e5a-08f9-11e8-9879-07b923f2c429.png)

### Installing
*Note: At the moment, performance only works on Linux systems.*

Clone the repository and run `./install.sh` to install all needed programs.

Alternatively, you can manually install the python packages in `requirements.txt`.
`nvidia-smi` and `sysstats` are also needed to display GPU RAM and disk read / write performance, respectively. RAM and CPU measurements will work without these though.

## Running the tool

Once installed, run `./performance.py` in the terminal to use the GUI version of the tool.
To use the terminal frontend, run `./performance.py -t` or `./performance.py --terminal`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
