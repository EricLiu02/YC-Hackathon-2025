from setuptools import setup, find_packages

setup(
    name="flight-mcp-agent",
    version="1.0.0",
    description="Flight search and pricing MCP server using Amadeus API",
    author="YC Hackathon Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "modelcontextprotocol==1.0.0",
        "amadeus==8.0.0",
        "pydantic==2.9.2",
        "python-dotenv==1.0.1",
        "httpx==0.27.2",
        "fastmcp==0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "flight-mcp-server=flight_mcp_agent.fast_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)