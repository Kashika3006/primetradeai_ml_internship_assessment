import argparse
import json
import logging
import time
import os
import sys
import yaml
import numpy as np
import pandas as pd

def setup_logging(log_path: str):
    """Configure structure Python logging to standard output and a log file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def write_metrics(output_path: str, metrics: dict):
    """Write metrics dictionary to the targeted output path as a JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
    except Exception as e:
        print(f"Critical error writing metrics.json : {e}", file=sys.stderr)


def main():
    # Start high-precision execution timer
    start_time = time.perf_counter()

    # Setup CLI parsing parameters
    parser = argparse.ArgumentParser(description="Deterministic MLOps Signal Generation Pipeline")
    parser.add_argument("--input", required=True, help="Path to the input data.csv")
    parser.add_argument("--config", required=True, help="Path to the config.yaml")
    parser.add_argument("--output", required=True, help="Path to the output metrics.json") 
    parser.add_argument("--log", required=True, help="Path to output run.log")
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log)
    logging.info("Job execution started.")

    # Default fallback values for structured failure output
    config_version = "unknown"
    config_seef = None

    try:
        logging.info(f"Loading config profile from {args.config}")
        if not os.path.exists(args.config):
            raise FileNotFoundError(f"Config file not found: {args.config}")
        
        with open(args.config, 'r') as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML config file: {e}") 

        if not config or not isinstance(config, dict):
            raise ValueError("Config file is empty or not a valid dictionary.")

        for required_key in ["seed", "window", "version"]:
            if required_key not in config:
                raise KeyError(f"Missing required key '{required_key}' in config file.")
            
        config_version = str(config["version"])
        config_seed = config["seed"]
        window = config["window"]

        if not isinstance(window, int) or window <= 0:
            raise ValueError("Window size must be a positive integer.")
        
        np.random.seed(config_seed)
        logging.info(f"Config loaded successfully: version={config_version}, seed={config_seed}, window={window}")

        logging.info(f"Loading input data from {args.input}")
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Input data file not found: {args.input}")
        if os.path.getsize(args.input) == 0:
            raise ValueError(f"Input data file is empty: {args.input}")
        
        try:
            raw_df = pd.read_csv(args.input)
            raw_col_name = raw_df.columns[0]
            
            clean_headers = raw_col_name.split(',')

            fixed_series = raw_df[raw_col_name].str.split(r'(?=2024)', n=1).str[1]
            df = fixed_series.str.split(',', expand=True)
            df.columns = clean_headers

            numeric_cols = ['open', 'high', 'low', 'close', 'volume_btc', 'volume_usd']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')

        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
        
        if df.empty:
            raise ValueError("Input data is empty after reading CSV.")
        if "close" not in df.columns:
            raise KeyError("Input data must contain a 'close' column.")
        
        rows_processed = len(df)
        logging.info(f"Data validation succeeded. Row processed: {rows_processed} rows.")

        logging.info("Computing mathematical window execution blocks...")

        df['rolling_mean'] = df['close'].rolling(window=window).mean()

        valid_mask = df['rolling_mean'].notna()

        df['signal'] = 0

        df.loc[valid_mask, 'signal'] = (df.loc[valid_mask, 'close'] > df.loc[valid_mask, 'rolling_mean']).astype(int)

        if valid_mask.sum() == 0:
            signal_rate = 0.0
            logging.warning("No rows fell outside window bounds. signal_rate evaluated as 0.0 ")
        else:
            signal_rate = df.loc[valid_mask, 'signal'].mean()

        logging.info("Processing matrix computation completed successfully.")

        latency_ms = int(round((time.perf_counter() - start_time) * 1000))

        success_output ={
            "version": config_version,
            "rows_processed": rows_processed,
            "metrics": "signal_rate",
            "value": float(f"{signal_rate:.4f}"),
            "latency_ms": latency_ms,
            "seed": config_seed,
            "status": "success"
        }

        write_metrics(args.output, success_output)
        logging.info(f"Metrics written successfully: {success_output}")
        logging.info("Job finalized with code status: success (0)")

        print(json.dumps(success_output, indent=2))
        sys.exit(0)

    except Exception as e:

        logging.error(f"Critical error during execution: {e}", exc_info=True)

        error_output = {
            "version": config_version,
            "status": "error",
            "error_message": str(e)
        }
        write_metrics(args.output, error_output)
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()