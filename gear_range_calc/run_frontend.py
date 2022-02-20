"""Make the Streamlit app to be accessable from an entrypoint."""
from pathlib import Path
import subprocess

def run_app():
    import argparse
    parser = argparse.ArgumentParser(description='Run the gear range calculator streamlit app.')
    parser.add_argument('-p', '--port', help='The port to expose the app on localhost', default=8501)
    args = parser.parse_args()
    app_pth = Path(__file__).parent / 'gearrange_viewer.py'
    subprocess.call(['streamlit', 'run', str(app_pth), '--server.port', str(args.port)])
    
if __name__ == '__main__':
    run_app()