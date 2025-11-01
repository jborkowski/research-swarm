from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="research-swarm",
    version="1.0.0",
    author="Research Automation Team",
    author_email="research@example.com",
    description="AI-powered research automation and prototype generation system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/research-swarm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langgraph>=0.0.20",
        "openai>=1.0.0",
        "redis>=5.0.0",
        "gitpython>=3.1.40",
        "aiohttp>=3.9.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "black>=23.0.0",
        "autopep8>=2.0.0",
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "prometheus-client>=0.19.0",
        "python-json-logger>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "research-swarm-api=api.main:main",
            "research-swarm-worker=orchestrator.worker:main",
        ],
    },
)
