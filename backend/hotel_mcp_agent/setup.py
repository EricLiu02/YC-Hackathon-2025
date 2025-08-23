from setuptools import setup, find_packages

setup(
    name="hotel-mcp-agent",
    version="1.0.0",
    description="Hotel search and pricing MCP server using SearchAPI Google Hotels",
    author="YC Hackathon Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "fastmcp",
        "pydantic>=2.0.0",
        "python-dotenv",
        "httpx",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "hotel-mcp-server=hotel_mcp_agent.fast_server:main",
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