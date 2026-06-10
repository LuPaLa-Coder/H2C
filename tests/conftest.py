"""Shared fixtures for H2C tests."""

import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_text():
    return (
        "[CTX:NEGOTIATE]\n"
        "version:h2c_v1.4|capabilities:[PRUNE,COMPACT]\n"
        "\n"
        "[STATE:ACK]\n"
        "protocol:h2c_v1.4\n"
    )


@pytest.fixture
def hello_world_text():
    return (FIXTURES / "test1-hello-world.h2c").read_text()


@pytest.fixture
def calculator_text():
    return (FIXTURES / "test2-calculator.h2c").read_text()


@pytest.fixture
def stress_text():
    return (FIXTURES / "test5-stress-130msg.h2c").read_text()


@pytest.fixture
def all_fixture_files():
    return sorted(FIXTURES.glob("test*.h2c"))
