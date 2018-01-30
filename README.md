# performance
A command line tool to measure GPU, CPU, RAM and disk performance in one place.

## Getting started
This project measures CPU, RAM, GPU and Disk I/O stats and displays a simple line chart in the console.

### Installing
*Note: At the moment, performance only works on Linux systems.*

Clone the repository and run `./install.sh` to install all needed programs.

Alternatively, you can manually install the python packages in `requirements.txt`.
`nvidia-smi` and `sysstats` are also needed to display GPU RAM and disk read / write performance, respectively. RAM and CPU measurements will work without these though.

## Running the tool

Once installed, run `./performance.py` in the terminal to use the tool.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
