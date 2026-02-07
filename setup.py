from setuptools import setup, find_packages

setup(
    name="android-phone-mcp",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "uiautomator2>=3.0.0",
        "httpx>=0.25.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "android-agent=android_phone.main:main",
        ],
    },
)
