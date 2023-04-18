# crypto-market-simulator

This is the implementation for our FYP titled "Optimal Order Placement in Cryptocurrency Markets" for the COMP4801 course.

## Group Members

1. Kritik Satija
2. Raghav Agarwal
3. Mohammad Muttasif

## Contributions

| Component                          | Tools Used | Contributor(s)    |
|------------------------------------|------------|-------------------|
| Exchange Simulator                 | Python     | Kritik, Raghav    |
| Deep Q-Network algorithm           | Python     | Kritik            |
| Microprice algorithm               | Python     | Raghav            |
| ~~Front-end~~                          | ~~PyQt5~~      | ~~Muttasif~~          |

*******

## Usage

### Environment

Create virtual environment using pipenv, conda, or any other virtual environment creator. The example below is using conda:
```
conda create -n crypto-market-simulator python=3.x
conda activate crypto-market-simulator
pip install -r requirements.txt
```

### Running the simulator

Run the file `market-simulator.py` in the market-simulator directory to start the simulator
```
python market-simulator.py
```

### Running the Reinforcement Learning model

In the reinforcement-learning directory, run the reinforcement-learning.ipynb file using Jupyter Notebook. Run all the cells

### Running the Microprice algorithm

In the microprice directory, run the microprice.ipynb file using Jupyter Notebook. Run all the cells
