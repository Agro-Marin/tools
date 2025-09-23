"""
Unit tests for workflow command
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest
import yaml
from src.commands.workflow import Pipeline, WorkflowCommand, WorkflowStep
from src.core.config import Config


class TestWorkflowCommand:
    """Test workflow command functionality"""

    def test_initialization(self):
        """Test workflow command initialization"""
        config = Config()
        command = WorkflowCommand(config)

        assert command.config == config
        assert command.available_commands == ["order", "detect", "rename"]

    def test_load_workflow_file(self, tmp_path):
        """Test loading workflow from YAML file"""
        config = Config()
        command = WorkflowCommand(config)

        # Create workflow file
        workflow_file = tmp_path / "workflow.yaml"
        workflow_data = {
            "pipelines": {
                "test_pipeline": {
                    "description": "Test pipeline",
                    "steps": [
                        {"command": "order", "args": {"path": "./models"}},
                        {"command": "detect", "args": {"from_commit": "HEAD~1"}},
                    ],
                }
            }
        }

        with open(workflow_file, "w") as f:
            yaml.dump(workflow_data, f)

        # Load workflow
        pipelines = command._load_workflow(workflow_file)

        assert len(pipelines) == 1
        assert "test_pipeline" in pipelines
        pipeline = pipelines["test_pipeline"]
        assert pipeline.name == "test_pipeline"
        assert pipeline.description == "Test pipeline"
        assert len(pipeline.steps) == 2

    def test_parse_workflow_step(self):
        """Test parsing individual workflow steps"""
        config = Config()
        command = WorkflowCommand(config)

        # Test command step
        step_data = {
            "command": "order",
            "args": {"path": "./models", "strategy": "semantic"},
        }

        step = command._parse_step(step_data)

        assert step.command == "order"
        assert step.args == {"path": "./models", "strategy": "semantic"}
        assert step.shell_command is None

        # Test shell step
        shell_data = {"shell": "echo 'Hello World'"}

        shell_step = command._parse_step(shell_data)

        assert shell_step.command is None
        assert shell_step.shell_command == "echo 'Hello World'"

    @patch("src.commands.workflow.UnifiedReorderCommand")
    def test_execute_order_step(self, mock_order_class, tmp_path):
        """Test executing order command step"""
        config = Config()
        config.repo_path = str(tmp_path)
        command = WorkflowCommand(config)

        # Mock UnifiedReorderCommand
        mock_order = Mock()
        mock_order.execute.return_value = True
        mock_order_class.return_value = mock_order

        # Create step
        step = WorkflowStep(
            command="order",
            args={"path": "./models", "strategy": "semantic"},
            shell_command=None,
        )

        # Execute step
        success = command._execute_step(step)

        assert success is True
        mock_order_class.assert_called_once()
        mock_order.execute.assert_called_once()

    @patch("src.commands.workflow.DetectCommand")
    def test_execute_detect_step(self, mock_detect_class):
        """Test executing detect command step"""
        config = Config()
        command = WorkflowCommand(config)

        # Mock DetectCommand
        mock_detect = Mock()
        mock_detect.execute.return_value = [{"old": "field1", "new": "field1_new"}]
        mock_detect_class.return_value = mock_detect

        # Create step
        step = WorkflowStep(
            command="detect",
            args={
                "from_commit": "HEAD~1",
                "to_commit": "HEAD",
                "output": "changes.csv",
            },
            shell_command=None,
        )

        # Execute step
        success = command._execute_step(step)

        assert success is True
        mock_detect.execute.assert_called_once_with(
            "HEAD~1", "HEAD", output_file="changes.csv"
        )

    @patch("src.commands.workflow.RenameCommand")
    def test_execute_rename_step(self, mock_rename_class, tmp_path):
        """Test executing rename command step"""
        config = Config()
        command = WorkflowCommand(config)

        # Create CSV file
        csv_file = tmp_path / "changes.csv"
        csv_file.write_text(
            "old_name,new_name,type,module,model\nfield1,field1_new,field,test,test.model"
        )

        # Mock RenameCommand
        mock_rename = Mock()
        mock_rename.execute.return_value = True
        mock_rename_class.return_value = mock_rename

        # Create step
        step = WorkflowStep(
            command="rename", args={"csv_file": str(csv_file)}, shell_command=None
        )

        # Execute step
        success = command._execute_step(step)

        assert success is True
        mock_rename.execute.assert_called_once_with(Path(str(csv_file)))

    @patch("subprocess.run")
    def test_execute_shell_step(self, mock_subprocess):
        """Test executing shell command step"""
        config = Config()
        command = WorkflowCommand(config)

        # Mock successful shell command
        mock_subprocess.return_value = Mock(returncode=0, stdout="Success")

        # Create shell step
        step = WorkflowStep(command=None, args={}, shell_command="echo 'Test'")

        # Execute step
        success = command._execute_step(step)

        assert success is True
        mock_subprocess.assert_called_once_with(
            "echo 'Test'", shell=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_execute_shell_step_failure(self, mock_subprocess):
        """Test shell command failure handling"""
        config = Config()
        command = WorkflowCommand(config)

        # Mock failed shell command
        mock_subprocess.return_value = Mock(returncode=1, stderr="Error")

        # Create shell step
        step = WorkflowStep(command=None, args={}, shell_command="false")

        # Execute step - should return False
        success = command._execute_step(step)

        assert success is False

    def test_execute_pipeline(self, tmp_path):
        """Test executing complete pipeline"""
        config = Config()
        command = WorkflowCommand(config)

        # Create pipeline
        pipeline = Pipeline(
            name="test_pipeline",
            description="Test",
            steps=[
                WorkflowStep(
                    command="order", args={"path": "./models"}, shell_command=None
                ),
                WorkflowStep(command=None, args={}, shell_command="echo 'Done'"),
            ],
        )

        # Mock step execution
        with patch.object(
            command, "_execute_step", side_effect=[True, True]
        ) as mock_exec:
            success = command._execute_pipeline(pipeline)

            assert success is True
            assert mock_exec.call_count == 2

    def test_execute_pipeline_with_failure(self):
        """Test pipeline stops on failure"""
        config = Config()
        command = WorkflowCommand(config)

        # Create pipeline with multiple steps
        pipeline = Pipeline(
            name="test_pipeline",
            description="Test",
            steps=[
                WorkflowStep(command="order", args={}, shell_command=None),
                WorkflowStep(command="detect", args={}, shell_command=None),
                WorkflowStep(command="rename", args={}, shell_command=None),
            ],
        )

        # Mock step execution - second step fails
        with patch.object(
            command, "_execute_step", side_effect=[True, False, True]
        ) as mock_exec:
            success = command._execute_pipeline(pipeline)

            # Pipeline should fail
            assert success is False
            # Should stop after failure (only 2 calls, not 3)
            assert mock_exec.call_count == 2

    def test_execute_specific_pipeline(self, tmp_path):
        """Test executing specific pipeline by name"""
        config = Config()
        command = WorkflowCommand(config)

        # Create workflow file with multiple pipelines
        workflow_file = tmp_path / "workflow.yaml"
        workflow_data = {
            "pipelines": {
                "pipeline1": {
                    "description": "First pipeline",
                    "steps": [{"shell": "echo 'Pipeline 1'"}],
                },
                "pipeline2": {
                    "description": "Second pipeline",
                    "steps": [{"shell": "echo 'Pipeline 2'"}],
                },
            }
        }

        with open(workflow_file, "w") as f:
            yaml.dump(workflow_data, f)

        # Mock pipeline execution
        with patch.object(command, "_execute_pipeline") as mock_exec:
            mock_exec.return_value = True

            # Execute specific pipeline
            success = command.execute(workflow_file, pipeline_name="pipeline2")

            assert success is True
            # Should only execute pipeline2
            assert mock_exec.call_count == 1
            executed_pipeline = mock_exec.call_args[0][0]
            assert executed_pipeline.name == "pipeline2"

    def test_execute_all_pipelines(self, tmp_path):
        """Test executing all pipelines when no name specified"""
        config = Config()
        command = WorkflowCommand(config)

        # Create workflow file
        workflow_file = tmp_path / "workflow.yaml"
        workflow_data = {
            "pipelines": {
                "pipeline1": {"steps": [{"shell": "echo '1'"}]},
                "pipeline2": {"steps": [{"shell": "echo '2'"}]},
            }
        }

        with open(workflow_file, "w") as f:
            yaml.dump(workflow_data, f)

        # Mock pipeline execution
        with patch.object(command, "_execute_pipeline") as mock_exec:
            mock_exec.return_value = True

            # Execute without specifying pipeline
            success = command.execute(workflow_file)

            assert success is True
            # Should execute both pipelines
            assert mock_exec.call_count == 2

    def test_invalid_command_in_step(self):
        """Test handling invalid command in step"""
        config = Config()
        command = WorkflowCommand(config)

        # Create step with invalid command
        step = WorkflowStep(command="invalid_command", args={}, shell_command=None)

        # Should return False for invalid command
        success = command._execute_step(step)
        assert success is False

    def test_workflow_with_config_override(self, tmp_path):
        """Test workflow with config overrides"""
        config = Config()
        config.dry_run = False
        command = WorkflowCommand(config)

        # Create workflow with config override
        workflow_file = tmp_path / "workflow.yaml"
        workflow_data = {
            "config": {"dry_run": True, "verbose": True},
            "pipelines": {
                "test": {"steps": [{"command": "order", "args": {"path": "."}}]}
            },
        }

        with open(workflow_file, "w") as f:
            yaml.dump(workflow_data, f)

        # Load workflow
        pipelines = command._load_workflow(workflow_file)

        # Config should be updated from workflow
        assert command.config.dry_run is True
        assert command.config.verbose is True

    def test_empty_workflow_file(self, tmp_path):
        """Test handling empty workflow file"""
        config = Config()
        command = WorkflowCommand(config)

        # Create empty workflow file
        workflow_file = tmp_path / "empty.yaml"
        workflow_file.write_text("")

        # Should handle gracefully
        pipelines = command._load_workflow(workflow_file)
        assert pipelines == {}

    def test_malformed_workflow_file(self, tmp_path):
        """Test handling malformed workflow file"""
        config = Config()
        command = WorkflowCommand(config)

        # Create malformed workflow file
        workflow_file = tmp_path / "malformed.yaml"
        workflow_file.write_text("not: valid: yaml: structure::")

        # Should handle error gracefully
        with patch("logging.Logger.error"):
            success = command.execute(workflow_file)
            assert success is False
