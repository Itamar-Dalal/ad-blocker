# DNS Ad Blocker

A Python-based DNS ad blocker application designed to filter unwanted advertisements by intercepting and processing DNS queries. The application combines a custom network protocol, a graphical user interface, a database for domain records, and an integrated DNS server to provide a comprehensive ad blocking solution.

## Features

- **Ad Blocking & Domain Management:**  
  Block and unblock domains using customizable rules.  
  Retrieve and manage the list of currently blocked domains on the server.

- **Network Communication:**  
  Utilizes both TCP and UDP for communication between client and server.  
  Implements custom encryption routines for secure transmission of commands and data.

- **DNS Filtering:**  
  Implements a DNS server using [dnslib](https://pypi.org/project/dnslib/) that intercepts DNS queries and checks against the blocked domains list.  
  Responds with a blocked or forwarded DNS response based on the domain status.

- **Graphical User Interface:**  
  Uses PyQt6 to provide an intuitive GUI for domain management, status updates, and configuration defaults.

- **Database Integration:**  
  Stores user and domain data in a SQLite database.  
  Provides methods for both user-specific and system-wide domain record retrieval and management.

- **Registry Management (Windows):**  
  Manages application settings (e.g., theme) via the Windows Registry.
