# For general information on the Pynini grammar compilation library, see
# pynini.opengrm.org.


from setuptools import setup


setup(
    name="pynini_rewrite",
    version="0.1",
    description="Rewriter library for Pynini",
    author="Kyle Gorman",
    author_email="kbg@google.com",
    url="http://pynini.opengrm.org",
    keywords=[
        "natural language processing", "speech recognition", "machine learning"
    ],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment", "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics"
    ],
    packages=["pynini_rewrite"],
    test_suite="rule_cascade_test")
