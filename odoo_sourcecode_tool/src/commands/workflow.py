"""
Command module for executing predefined workflows
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from commands.detect import DetectCommand
from commands.rename import RenameCommand
from commands.reorder import UnifiedReorderCommand
from core.config import Config

logger = logging.getLogger(__name__)


class WorkflowCommand:
    """Command handler for executing complex workflows"""

    def __init__(self, config: Config):
        """Initialize workflow command with configuration"""
        self.config = config
        self.commands = {
            "reorder": UnifiedReorderCommand(config),
            "detect": DetectCommand(config),
            "rename": RenameCommand(config),
        }

    def execute(self, workflow_file: Path, pipeline_name: str | None = None) -> bool:
        """
        Execute a workflow from configuration file

        Args:
            workflow_file: Path to workflow YAML file
            pipeline_name: Specific pipeline to execute (optional)

        Returns:
            True if successful, False if errors occurred
        """
        try:
            # Load workflow configuration
            with open(workflow_file, "r") as f:
                workflow_config = yaml.safe_load(f)

            # Get pipelines
            pipelines = workflow_config.get("pipelines", {})

            if not pipelines:
                logger.error("No pipelines defined in workflow file")
                return False

            # Select pipeline
            if pipeline_name:
                if pipeline_name not in pipelines:
                    logger.error(f"Pipeline '{pipeline_name}' not found")
                    return False
                selected_pipelines = {pipeline_name: pipelines[pipeline_name]}
            else:
                # Execute all pipelines
                selected_pipelines = pipelines

            # Execute selected pipelines
            for name, pipeline in selected_pipelines.items():
                logger.info(f"Executing pipeline: {name}")
                if not self._execute_pipeline(name, pipeline):
                    logger.error(f"Pipeline '{name}' failed")
                    return False

            logger.info("All pipelines executed successfully")
            return True

        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return False

    def _execute_pipeline(self, name: str, pipeline: list[dict[str, Any]]) -> bool:
        """Execute a single pipeline"""
        logger.info(f"Starting pipeline: {name}")

        for step_num, step in enumerate(pipeline, 1):
            step_type = step.get("type")
            if not step_type:
                logger.error(f"Step {step_num}: missing 'type'")
                return False

            logger.info(f"Step {step_num}/{len(pipeline)}: {step_type}")

            if step_type == "order":
                if not self._execute_order_step(step):
                    return False

            elif step_type == "detect":
                if not self._execute_detect_step(step):
                    return False

            elif step_type == "rename":
                if not self._execute_rename_step(step):
                    return False

            elif step_type == "shell":
                if not self._execute_shell_step(step):
                    return False

            else:
                logger.error(f"Unknown step type: {step_type}")
                return False

        return True

    def _execute_order_step(self, step: dict[str, Any]) -> bool:
        """Execute order command step"""
        try:
            path = Path(step.get("path", "."))
            recursive = step.get("recursive", False)

            # Override config if step specifies
            if "strategy" in step:
                self.config.ordering.strategy = step["strategy"]

            return self.commands["order"].execute(path, recursive)

        except Exception as e:
            logger.error(f"Order step failed: {e}")
            return False

    def _execute_detect_step(self, step: dict[str, Any]) -> bool:
        """Execute detect command step"""
        try:
            from_commit = step.get("from")
            to_commit = step.get("to")
            output = step.get("output", "changes.csv")

            # Override config if step specifies
            if "threshold" in step:
                self.config.detection.confidence_threshold = step["threshold"]

            return self.commands["detect"].execute(from_commit, to_commit, output)

        except Exception as e:
            logger.error(f"Detect step failed: {e}")
            return False

    def _execute_rename_step(self, step: dict[str, Any]) -> bool:
        """Execute rename command step"""
        try:
            csv_file = Path(step.get("csv", "changes.csv"))

            if not csv_file.exists():
                logger.error(f"CSV file not found: {csv_file}")
                return False

            return self.commands["rename"].execute(csv_file)

        except Exception as e:
            logger.error(f"Rename step failed: {e}")
            return False

    def _execute_shell_step(self, step: dict[str, Any]) -> bool:
        """Execute shell command step"""
        import subprocess

        try:
            command = step.get("command")
            if not command:
                logger.error("Shell step missing 'command'")
                return False

            logger.info(f"Executing shell: {command}")

            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Shell command failed: {result.stderr}")
                return False

            return True

        except Exception as e:
            logger.error(f"Shell step failed: {e}")
            return False
