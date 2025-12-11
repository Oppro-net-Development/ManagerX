Wikipedia commands
===========================
This section provides an overview of the Wikipedia commands available in ManagerX. These commands allow users to
search for and retrieve information from Wikipedia directly within the platform.

Supported Languages
-------------------
The Wikipedia bot supports the following languages:

- 🇩🇪 Deutsch (German)
- 🇺🇸 English
- 🇫🇷 Français (French)
- 🇪🇸 Español (Spanish)
- 🇮🇹 Italiano (Italian)
- 🇯🇵 日本語 (Japanese)
- 🇷🇺 Русский (Russian)

Available Commands
-------------------

Wikipedia Search Command
---------------------------

.. admonition:: Command

    **Command:** `/wiki_search`

    **Description:** Search Wikipedia for articles and information

    **Parameters:**
    
    - ``suchbegriff`` (required): The search term you want to look up on Wikipedia (max 100 characters)
    - ``sprache`` (optional): Choose the language for the search (default: Deutsch)

    **Example:**
    
    .. code-block:: 
    
        /wiki_search suchbegriff:Python sprache:en

    The bot displays the article with title, summary, categories, and interactive buttons.
    
    **Features:**
    
    - Autocomplete suggestions as you type
    - Displays article title, summary, and categories
    - Shows coordinates if available
    - Provides links to related/similar articles
    - Includes direct link to the full Wikipedia article
    - Caches results for fast repeated access

---
Wikipedia Random Command
---------------------------

.. admonition:: Command

    **Command:** `/wiki_random`

    **Description:** Display a random Wikipedia article

    **Parameters:**
    
    - ``sprache`` (optional): Choose the language for the random article (default: Deutsch)
    - ``anzahl`` (optional): Number of random articles to display (1-5, default: 1)

    **Example:**
    
    .. code-block:: 
    
        /wiki_random sprache:de anzahl:3

    The bot displays one or more random Wikipedia articles with summaries and related information.
    
    **Features:**
    
    - Single random article with full details
    - Or multiple random articles (up to 5) with summaries
    - Each article shows title, summary, and related information
    - Articles can be opened individually with buttons
    - Allows quick discovery of new topics

---
Wikipedia Multi-Search Command
---------------------------

.. admonition:: Command

    **Command:** `/wiki_multisearch`

    **Description:** Extended Wikipedia search with multiple results

    **Parameters:**
    
    - ``suchbegriff`` (required): The search term (max 100 characters)
    - ``anzahl`` (optional): Number of results to display (1-15, default: 8)
    - ``sprache`` (optional): Language for the search (default: Deutsch)

    **Example:**
    
    .. code-block:: 
    
        /wiki_multisearch suchbegriff:Klimawandel anzahl:10 sprache:de

    The bot displays multiple search results with summaries and quick access buttons.
    
    **Features:**
    
    - Displays multiple search results with summaries
    - Each result shows a preview of the first sentence
    - Quick access buttons to open individual articles
    - Organized list format for easy browsing
    - Shows the language flag and number of results

---
Wikipedia Category Command
---------------------------

.. admonition:: Command

    **Command:** `/wiki_category`

    **Description:** Browse Wikipedia categories

    **Parameters:**
    
    - ``kategorie`` (required): Name of the category to search (max 100 characters)
    - ``sprache`` (optional): Language for the category (default: Deutsch)

    **Example:**
    
    .. code-block:: 
    
        /wiki_category kategorie:Planeten sprache:de

    The bot displays articles within the specified category with summaries.
    
    **Features:**
    
    - Find articles within a specific category
    - Displays articles categorized under the search term
    - Shows summaries for each article
    - Quick buttons to open full articles
    - Returns up to 8 results from the category

---
Wikipedia Statistics Command
---------------------------

.. admonition:: Command

    **Command:** `/wiki_stats`

    **Description:** Display bot statistics and Wikipedia information

    **Parameters:** None

    **Example:**
    
    .. code-block:: 
    
        /wiki_stats

    The bot displays comprehensive statistics about usage and available features.
    
    **Features:**
    
    - Shows total search queries performed
    - Displays number of articles viewed
    - Bot uptime in days, hours, and minutes
    - Lists languages used since bot startup
    - Shows available languages with flags
    - Technical information (cache entries, rate limiting, features)

---
Wikipedia Cache Management
---------------------------

.. admonition:: Command

    **Command:** `/wiki_cache`

    **Description:** Cache management (Administrator only)

    **Parameters:**
    
    - ``aktion`` (required): Cache action to perform
      
      - ``status``: Show current cache statistics
      - ``clear``: Clear all cached entries
      - ``cleanup``: Remove expired cache entries

    **Example:**
    
    .. code-block:: 
    
        /wiki_cache aktion:status

    The bot displays cache statistics or performs the requested cache action.
    
    **Features:**
    
    - View cache performance metrics
    - Total entries count
    - Expired entries count
    - Active entries count
    - Cache duration setting
    - Requires administrator permissions

---

Interactive Features
---------------------

All article results include interactive buttons:

- **🔗 Read Full Article**: Direct link to the complete Wikipedia article
- **🌐 Language Selection**: Switch between supported languages
- **📚 Similar Articles**: Quick buttons to view related articles
- **🎲 Random Article**: Get another random article
- **📊 Article Info**: View detailed statistics about the article
- **🔄 Refresh**: Update the article with fresh data

Article Information
-------------------

When viewing an article, you get:

- **Title and Language**: Article name and which language version
- **Summary**: Concise overview (up to 1500 characters)
- **Categories**: Topics the article is filed under
- **Coordinates**: Geographic location (if applicable)
- **Related Links**: Similar or related articles
- **Images**: Image count (if available)

Caching System
---------------

The bot includes an intelligent caching system that:

- Stores frequently accessed articles
- Improves response time for repeat searches
- Automatically expires old cache entries after 5 minutes
- Can be manually managed by administrators
- Reduces API calls to Wikipedia servers

Search Features
---------------

- **Autocomplete**: Get suggestions as you type (minimum 2 characters)
- **Disambiguation Handling**: When a search term has multiple meanings, shows all options
- **Error Handling**: Friendly error messages with suggestions if an article isn't found
- **Multi-language Support**: Same search term returns results in different languages
- **Smart Sorting**: Search results ranked by relevance

Tips and Tricks
---------------

- Use specific search terms for better results (e.g., "Python (Programmiersprache)" for the programming language)
- Try different languages to find articles that may not exist in your preferred language
- Use ``/wiki_random`` to discover new interesting topics
- The ``/wiki_multisearch`` command is great for research with multiple related articles
- Administrator can clean up the cache to free up memory
