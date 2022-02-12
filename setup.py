from setuptools import find_packages, setup

setup(
    name="example",
    version="0.1.0",
    description="GraphQL interface to the ISPyB database",
    author="Richard Gildea",
    author_email="richard.gildea@diamond.ac.uk",
    url="https://github.com/rjgildea/strawberry-ispyb",
    packages=find_packages(include=["src/ispyb_graphql"]),
    install_requires=[
        "asyncmy",
        "cython",
        "fastapi",
        "ispyb",
        "itsdangerous",
        "python-cas",
        "sqlalchemy[asyncio]",
        "strawberry-graphql[fastapi]",
        "uvicorn[standard]",
    ],
    # extras_require={'plotting': ['matplotlib>=2.2.0', 'jupyter']},
    setup_requires=["isort", "black", "flake8", "pre-commit"],
    test_requires=["pytest"],
    entry_points={},
    # package_data={}
)
