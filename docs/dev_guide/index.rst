Developer Guide
=========================
Welcome to the ManagerX Developer Guide! This section provides in-depth information for developers looking to contribute to or extend ManagerX, including architecture overviews, API references, and development best practices.

To download and set up the development environment, follow these steps:
1. Clone the ManagerX repository from GitHub:

.. code-block:: bash

   git clone https://github.com/Oppro-net-Development/ManagerX.git

2. Navigate to the project directory:

.. code-block:: bash

   cd ManagerX

3. Install the required dependencies:

.. code-block:: bash

   pip install -r req.txt

.. admonition:: note

   Ensure you have Python 3.10 or higher installed to run ManagerX successfully.

Dependencies
=========================

The following dependencies are required for developing and running ManagerX:

- Python 3.10+
- aiocache
- aiohappyeyeballs
- aiohttp
- aiosqlite
- annotated-types
- anyio
- attrs
- beautifulsoup4
- certifi
- charset-normalizer
- click
- colorama
- ezcord
- frozenlist
- h11
- idna
- Jinja2
- MarkupSafe
- multidict
- propcache
- py-cord==2.7.0rc2
- pydantic
- pydantic_core
- python-dotenv
- PyYAML
- requests
- six
- sniffio
- soupsieve
- starlette
- typing_extensions
- typing-inspection
- urllib3
- wikipedia
- yarl
- timedelta
- sphinx
- pydata-sphinx-theme
- sphinx-autodoc-typehints
- myst-parser
- SimpleColoredLogs – Another Project of OPPRO.NET Development
- sphinx-copybutton


.. toctree::
   :maxdepth: 2
   :caption: Developer Guide:

   index
   Database Handler <database_handler/index>
   Architecture <architecture/index>
   API Reference <api_reference/index>
   Contributing <contributing/index>
   Testing <testing/index>

