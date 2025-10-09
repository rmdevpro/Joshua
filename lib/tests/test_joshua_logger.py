import asyncio
import os

import pytest
from pytest_mock import MockerFixture

from joshua_logger import logger as default_logger_instance
from joshua_logger.logger import Logger

pytestmark = pytest.mark.asyncio


class TestLogger:
    async def test_logger_connects_and_sends_log(self, mock_godot_server):
        """Tests basic connection and validates the JSON-RPC log format."""
        logger = Logger(url=mock_godot_server["url"], timeout=1)
        await logger.log("INFO", "Test message", "test_component", data={"id": 1})

        message = await asyncio.wait_for(mock_godot_server["messages"].get(), timeout=1)

        assert message["method"] == "tools/call"
        params = message["params"]
        assert params["name"] == "logger_log"
        args = params["arguments"]
        assert args["level"] == "INFO"
        assert args["message"] == "Test message"
        assert args["component"] == "test_component"
        assert args["data"] == {"id": 1}

        await logger.close()

    async def test_silent_failure_when_godot_unavailable(self):
        """Tests that log() does not raise an exception if the server is down."""
        logger = Logger(url="ws://localhost:12345", timeout=0.1) # Use a closed port
        try:
            await logger.log("ERROR", "This should not be sent", "fail_component")
        except Exception as e:
            pytest.fail(f"Logger raised an unexpected exception on connection failure: {e}")
        finally:
            await logger.close()

    async def test_reconnection_and_exponential_backoff(self, mocker: MockerFixture):
        """Verifies that the reconnect logic uses exponential backoff."""
        logger = Logger(url="ws://localhost:12345", timeout=0.1)

        # Spy on asyncio.sleep to check its call arguments
        sleep_spy = mocker.spy(asyncio, "sleep")

        # Trigger the reconnect loop by failing to connect
        asyncio.create_task(logger._ensure_connected())

        # Wait for a few backoff cycles to occur
        await asyncio.sleep(7.5) # 1s + 2s + 4s = 7s total sleep time

        await logger.close()

        call_delays = [call.args[0] for call in sleep_spy.call_args_list]

        # Check for the expected backoff sequence (1, 2, 4)
        assert any(0.9 < delay < 1.1 for delay in call_delays)
        assert any(1.9 < delay < 2.1 for delay in call_delays)
        assert any(3.9 < delay < 4.1 for delay in call_delays)

    async def test_concurrency_with_send_lock(self, mock_godot_server):
        """Tests that multiple async tasks can log simultaneously without error, thanks to the send lock."""
        logger = Logger(url=mock_godot_server["url"], timeout=1)

        num_tasks = 100
        tasks = [
            asyncio.create_task(logger.log("INFO", f"Message {i}", "concurrency_test"))
            for i in range(num_tasks)
        ]

        await asyncio.gather(*tasks)

        # Verify that all messages were received
        received_count = mock_godot_server["messages"].qsize()
        assert received_count == num_tasks
        await logger.close()

    def test_environment_variable_configuration(self, mocker: MockerFixture):
        """Tests that the logger can be configured with environment variables."""
        mocker.patch.dict(os.environ, {
            "JOSHUA_LOGGER_URL": "ws://test-host:1234",
            "JOSHUA_LOGGER_TIMEOUT": "5.5"
        })
        logger = Logger() # Instantiated without args to use env vars
        assert logger.url == "ws://test-host:1234"
        assert logger.timeout == 5.5

    async def test_default_instance_works(self, mock_godot_server, mocker: MockerFixture):
        """Tests the pre-configured default instance."""
        mocker.patch.dict(os.environ, {"JOSHUA_LOGGER_URL": mock_godot_server["url"]})

        # Patch the default instance's attributes directly for test isolation
        mocker.patch.object(default_logger_instance, 'url', mock_godot_server["url"])
        mocker.patch.object(default_logger_instance, 'timeout', 1.0)

        await default_logger_instance.log("DEBUG", "Default instance test", "default")

        message = await asyncio.wait_for(mock_godot_server["messages"].get(), timeout=1)
        assert message["params"]["arguments"]["message"] == "Default instance test"

        await default_logger_instance.close()
