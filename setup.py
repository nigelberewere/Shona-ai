from pathlib import Path

from setuptools import find_packages, setup


def read_requirements() -> list[str]:
    req_path = Path(__file__).parent / "requirements.txt"
    if not req_path.exists():
        return []
    return [line.strip() for line in req_path.read_text(encoding="utf-8").splitlines() if line.strip()]


setup(
    name="shona-ai",
    version="0.1.0",
    description="Shona AI - a Shona (ChiShona) large language model",
    long_description=(Path(__file__).parent / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Shona AI Contributors",
    packages=find_packages(exclude=("tests",)),
    python_requires=">=3.10",
    install_requires=read_requirements(),
)
