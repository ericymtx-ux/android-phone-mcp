import argparse
import sys
import os
import logging
from dotenv import load_dotenv

from android_phone.core.controller import AndroidController
from android_phone.integrations.volcengine import VolcengineGUIClient
from android_phone.core.agent import AutonomousAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AndroidPhoneCLI")

def run_task(goal: str, max_steps: int, eco_mode: bool = False):
    """Run autonomous task"""
    # Load env
    load_dotenv()
    
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        logger.error("Please set ARK_API_KEY environment variable or in .env file")
        return

    if eco_mode:
        logger.info("Running in Eco Mode")

    logger.info("Initializing Controller...")
    controller = AndroidController()
    try:
        controller.connect()
        info = controller.get_info()
        logger.info(f"Connected to device: {info.get('productName')} ({controller.serial})")
    except Exception as e:
        logger.error(f"Failed to connect to device: {e}")
        return

    logger.info("Initializing Agent...")
    client = VolcengineGUIClient()
    agent = AutonomousAgent(controller, client, eco_mode=eco_mode)

    logger.info(f"Starting task: {goal}")
    try:
        result = agent.run(goal, max_steps=max_steps)
        logger.info(f"Task Result: {result}")
    except Exception as e:
        logger.error(f"Task execution failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Android Phone Autonomous Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Command: run (Run autonomous task)
    run_parser = subparsers.add_parser("run", help="Run an autonomous task")
    run_parser.add_argument("goal", help="Task goal description (e.g. 'Open WeChat')")
    run_parser.add_argument("--steps", type=int, default=50, help="Max steps")
    run_parser.add_argument("--eco", action="store_true", help="Enable Eco Mode")

    # Command: server (Start MCP Server)
    server_parser = subparsers.add_parser("server", help="Start MCP Server")

    args = parser.parse_args()

    if args.command == "run":
        run_task(args.goal, args.steps, eco_mode=args.eco)
    elif args.command == "server":
        from android_phone.server import app
        app.run()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
